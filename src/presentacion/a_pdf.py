"""Convierte la presentación .pptx a PDF, y a un PDF con las notas del orador debajo.

No hace falta PowerPoint ni LibreOffice: el PDF se dibuja con las posiciones, tamaños,
colores y tipografías guardadas en el propio .pptx, sin recomponer nada. Todo el texto es
Arial y aquí se mide con la misma Arial, así que los cortes de línea caen donde caerían en
PowerPoint. Si un texto no cabe en su caja, lo avisa en la consola con el número de
diapositiva: es la revisión de que nada se desborda.

    python src/presentacion/a_pdf.py docs/presentacion/presentacion.pptx \
           docs/presentacion/presentacion.pdf --notas docs/presentacion/presentacion-notas.pdf

Requiere python-pptx y reportlab (no están en requirements.txt: solo sirven para esto).
"""
import io
import sys
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from reportlab.lib.colors import Color, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# Arial del sistema (macOS); en Linux, Liberation Sans tiene las mismas métricas.
CANDIDATAS = [
    (Path("/System/Library/Fonts/Supplemental/Arial.ttf"), Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf")),
    (Path("/usr/share/fonts/truetype/msttcorefonts/Arial.ttf"), Path("/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf")),
    (Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"), Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf")),
]
for normal, negrita in CANDIDATAS:
    if normal.exists() and negrita.exists():
        pdfmetrics.registerFont(TTFont("Arial", normal))
        pdfmetrics.registerFont(TTFont("Arial-Bold", negrita))
        break
else:
    sys.exit("No encontré Arial ni Liberation Sans.")

ASCENT = pdfmetrics.getFont("Arial").face.ascent / 1000.0
INTERLINEA = 1.15          # alto de una línea sencilla de Arial, en múltiplos del tamaño
EMU = 914400.0
PT = 72.0
avisos = []
bajos = []


def color(rgb, defecto=(0, 0, 0)):
    r, g, b = defecto if rgb is None else (rgb[0], rgb[1], rgb[2])
    return Color(r / 255, g / 255, b / 255)


def color_de_forma(forma):
    try:
        if forma.fill.type == 1:
            return color(forma.fill.fore_color.rgb)
    except Exception:
        pass
    return None


def palabras(parrafo, tam_defecto):
    """[(texto, fuente, tamaño, color, espacio_después)] por palabra, con el estilo de su run."""
    fuera = []
    for r in parrafo.runs:
        tam = r.font.size.pt if r.font.size else tam_defecto
        fuente = "Arial-Bold" if r.font.bold else "Arial"
        try:
            col = color(r.font.color.rgb)
        except Exception:
            col = color(None)
        # Un run que empieza con espacio separa la palabra anterior, aunque sea de otro run.
        if r.text.startswith(" ") and fuera:
            fuera[-1][4] = True
        trozos = r.text.split(" ")
        for i, t in enumerate(trozos):
            if t == "" and i < len(trozos) - 1:
                continue
            fuera.append([t, fuente, tam, col, i < len(trozos) - 1])
    return fuera


def arma_lineas(tokens, ancho):
    """Corte voraz, como el de PowerPoint: sin guionado."""
    lineas, actual, w = [], [], 0.0
    for tok in tokens:
        t, f, tam, col, espacio = tok
        wt = pdfmetrics.stringWidth(t, f, tam)
        we = pdfmetrics.stringWidth(" ", f, tam) if espacio else 0.0
        if actual and w + wt > ancho + 0.01:
            lineas.append(actual)
            actual, w = [tok], wt + we
        else:
            actual.append(tok)
            w += wt + we
    if actual:
        lineas.append(actual)
    return lineas


def alto_de_lineas(lineas):
    return sum(max(t[2] for t in ln) * INTERLINEA for ln in lineas)


def dibuja_texto(c, marco, x, y, ancho, alto, tam_defecto=18.0, donde=""):
    """x, y en puntos desde la esquina superior izquierda de la página."""
    bloques = []
    for p in marco.paragraphs:
        toks = palabras(p, tam_defecto)
        despues = p.space_after.pt if p.space_after else 0
        if not any(t[0].strip() for t in toks):
            bloques.append((None, despues, tam_defecto * INTERLINEA, None))
            continue
        lineas = arma_lineas(toks, ancho)
        bloques.append((lineas, despues, alto_de_lineas(lineas), p.alignment))
    total = sum(b[2] for b in bloques) + sum(b[1] for b in bloques[:-1])
    if donde and total > alto + 2:
        avisos.append(f"{donde}: el texto mide {total:.0f} pt y la caja {alto:.0f} pt · «{marco.text[:60]}»")
    cursor = y
    if marco.vertical_anchor == MSO_ANCHOR.MIDDLE:
        cursor = y + (alto - total) / 2
    elif marco.vertical_anchor == MSO_ANCHOR.BOTTOM:
        cursor = y + alto - total
    for lineas, despues, alto_b, alineacion in bloques:
        if lineas is None:
            cursor += alto_b + despues
            continue
        for ln in lineas:
            tam = max(t[2] for t in ln)
            base = cursor + ASCENT * tam
            ancho_linea = sum(pdfmetrics.stringWidth(t[0], t[1], t[2])
                              + (pdfmetrics.stringWidth(" ", t[1], t[2]) if t[4] else 0) for t in ln)
            if alineacion == PP_ALIGN.CENTER:
                cx = x + (ancho - ancho_linea) / 2
            elif alineacion == PP_ALIGN.RIGHT:
                cx = x + ancho - ancho_linea
            else:
                cx = x
            for t, f, tam_t, col, espacio in ln:
                c.setFillColor(col)
                c.setFont(f, tam_t)
                c.drawString(cx, PAGINA_ALTO - base, t)
                cx += pdfmetrics.stringWidth(t, f, tam_t) + (pdfmetrics.stringWidth(" ", f, tam_t) if espacio else 0)
            cursor += tam * INTERLINEA
        cursor += despues


def dibuja_tabla(c, forma, donde):
    t = forma.table
    x0, y0 = forma.left / EMU * PT, forma.top / EMU * PT
    anchos = [col.width / EMU * PT for col in t.columns]
    altos = []
    for fila in t.rows:
        necesario = 0.0
        for j, celda in enumerate(fila.cells):
            interior = anchos[j] - celda.margin_left.pt - celda.margin_right.pt
            alto = 0.0
            for p in celda.text_frame.paragraphs:
                toks = palabras(p, 12)
                if any(k[0].strip() for k in toks):
                    alto += alto_de_lineas(arma_lineas(toks, interior))
            necesario = max(necesario, alto + celda.margin_top.pt + celda.margin_bottom.pt)
        altos.append(max(fila.height / EMU * PT, necesario))
    y = y0
    for i, fila in enumerate(t.rows):
        x = x0
        for j, celda in enumerate(fila.cells):
            try:
                relleno = color(celda.fill.fore_color.rgb) if celda.fill.type == 1 else None
            except Exception:
                relleno = None
            if relleno is not None:
                c.setFillColor(relleno)
                c.rect(x, PAGINA_ALTO - y - altos[i], anchos[j], altos[i], stroke=0, fill=1)
            dibuja_texto(c, celda.text_frame,
                         x + celda.margin_left.pt, y + celda.margin_top.pt,
                         anchos[j] - celda.margin_left.pt - celda.margin_right.pt,
                         altos[i] - celda.margin_top.pt - celda.margin_bottom.pt, 12)
            x += anchos[j]
        # Solo líneas horizontales: la tabla se lee por renglones.
        c.setStrokeColor(Color(0xD9 / 255, 0xD9 / 255, 0xD9 / 255))
        c.setLineWidth(0.75)
        c.line(x0, PAGINA_ALTO - y - altos[i], x0 + sum(anchos), PAGINA_ALTO - y - altos[i])
        y += altos[i]
    # PowerPoint estira la tabla hacia abajo lo que haga falta: se avisa si llega al pie.
    if donde and y > PAGINA_ALTO - 0.35 * PT:
        avisos.append(f"{donde}: la tabla termina a {y / PT:.2f} in, encima del pie")
    if donde:
        bajos.append(f"{donde}: tabla de {y0 / PT:.2f} a {y / PT:.2f} in")


def dibuja_diapositiva(c, d, ancho_pt, alto_pt, num=None):
    c.setFillColor(white)
    c.rect(0, PAGINA_ALTO - alto_pt, ancho_pt, alto_pt, stroke=0, fill=1)
    donde = f"diapositiva {num}" if num else ""
    for sh in d.shapes:
        if sh.has_table:
            dibuja_tabla(c, sh, donde)
            continue
        x, y = sh.left / EMU * PT, sh.top / EMU * PT
        w, h = sh.width / EMU * PT, sh.height / EMU * PT
        if donde and (x + w > ancho_pt + 1 or y + h > alto_pt + 1):
            avisos.append(f"{donde}: una forma se sale de la diapositiva · «{sh.text_frame.text[:40] if sh.has_text_frame else sh.name}»")
        if sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
            c.drawImage(ImageReader(io.BytesIO(sh.image.blob)), x, PAGINA_ALTO - y - h, w, h, mask="auto")
            continue
        relleno = color_de_forma(sh)
        if relleno is not None:
            c.setFillColor(relleno)
            c.rect(x, PAGINA_ALTO - y - h, w, h, stroke=0, fill=1)
        if sh.has_text_frame and sh.text_frame.text.strip():
            m = sh.text_frame
            dibuja_texto(c, m, x + m.margin_left.pt, y + m.margin_top.pt,
                         w - m.margin_left.pt - m.margin_right.pt,
                         h - m.margin_top.pt - m.margin_bottom.pt, donde=donde)


entrada, salida = sys.argv[1], sys.argv[2]
notas = sys.argv[4] if len(sys.argv) > 4 and sys.argv[3] == "--notas" else None
prs = Presentation(entrada)
W = prs.slide_width / EMU * PT
H = prs.slide_height / EMU * PT
TITULO = prs.core_properties.title or "Presentación"
AUTOR = prs.core_properties.author or ""

PAGINA_ALTO = H
c = canvas.Canvas(salida, pagesize=(W, H))
c.setTitle(TITULO)
c.setAuthor(AUTOR)
for i, d in enumerate(prs.slides, 1):
    dibuja_diapositiva(c, d, W, H, i)
    c.showPage()
c.save()
print(f"{salida}: {len(prs.slides)} páginas")

if notas:
    NW, NH = 8.5 * PT, 11 * PT
    margen = 0.6 * PT
    escala = (NW - 2 * margen) / W
    tinta = Color(0x1A / 255, 0x1A / 255, 0x1A / 255)
    gris = Color(0x6E / 255, 0x6E / 255, 0x6E / 255)
    c = canvas.Canvas(notas, pagesize=(NW, NH))
    c.setTitle(TITULO + " (con notas del orador)")
    c.setAuthor(AUTOR)
    paginas = 0
    for i, d in enumerate(prs.slides, 1):
        c.saveState()
        c.translate(margen, NH - margen - H * escala)
        c.scale(escala, escala)
        PAGINA_ALTO = H
        dibuja_diapositiva(c, d, W, H)
        c.restoreState()
        PAGINA_ALTO = NH
        c.setStrokeColor(Color(0xD9 / 255, 0xD9 / 255, 0xD9 / 255))
        c.setLineWidth(0.75)
        c.rect(margen, NH - margen - H * escala, W * escala, H * escala, stroke=1, fill=0)
        texto = d.notes_slide.notes_text_frame.text if d.has_notes_slide else ""
        y = NH - margen - H * escala - 26
        c.setFillColor(gris)
        c.setFont("Arial-Bold", 10)
        c.drawString(margen, y, f"DIAPOSITIVA {i} DE {len(prs.slides)}")
        c.drawRightString(NW - margen, y, "Notas del orador")
        y -= 18
        for k, parrafo in enumerate(texto.split("\n")):
            if not parrafo.strip():
                y -= 6
                continue
            # La primera línea de cada nota es el tiempo o la marca de anexo: va en negritas.
            fuente = "Arial-Bold" if k == 0 else "Arial"
            tokens = [[p, fuente, 12, tinta, True] for p in parrafo.split(" ")]
            for ln in arma_lineas(tokens, NW - 2 * margen):
                if y < margen:
                    c.showPage()
                    paginas += 1
                    y = NH - margen
                c.setFillColor(tinta)
                c.setFont(fuente, 12)
                x = margen
                for t, f, tam, col, esp in ln:
                    c.drawString(x, y, t)
                    x += pdfmetrics.stringWidth(t, f, tam) + pdfmetrics.stringWidth(" ", f, tam)
                y -= 12 * 1.4
            y -= 5
        c.showPage()
        paginas += 1
    c.save()
    print(f"{notas}: {paginas} páginas")

for a in avisos:
    print("  AVISO", a)
if "--tablas" in sys.argv:
    for b in bajos:
        print("  ", b)
