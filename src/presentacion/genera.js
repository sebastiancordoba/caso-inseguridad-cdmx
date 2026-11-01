/* Presentación final del caso: diez minutos y un anexo para preguntas.

   La historia va en el orden que pide la rúbrica para la presentación oral, orientada al
   problema y a la decisión y no al proceso técnico: el problema, los datos, lo que encontré,
   qué recomiendo y los límites. Cada diapositiva tiene una sola idea, el título es la
   afirmación y ninguna idea se repite en la siguiente (los comentarios de la presentación del
   15 de octubre fueron falta de flujo, ideas repetidas y conclusiones poco claras). Cada
   sigla, término y cifra se define en pantalla la primera vez que aparece, para que se
   entienda sin haber leído el escrito.

   El guion de cada diapositiva va en sus notas, con el tiempo estimado al hablarlo. El tiempo
   sale del número de palabras del guion a PALABRAS_POR_MINUTO, más los segundos de la
   demostración; la parte principal no puede pasar de diez minutos (assert al final). Lo que
   no cabe en diez minutos va al anexo, que no se presenta y sirve para responder preguntas.

   Todas las cifras salen del escrito y de las tablas del pipeline
   (datos/procesados/metro_tablas/), recalculadas el 29 de octubre de 2026.

   Se rehace así, desde la raíz del repositorio:
     npm install pptxgenjs                     (una vez)
     node src/presentacion/genera.js
     python src/presentacion/a_pdf.py docs/presentacion/presentacion.pptx \
            docs/presentacion/presentacion.pdf --notas docs/presentacion/presentacion-notas.pdf
*/
const fs = require("fs");
const path = require("path");
const Pptx = require("pptxgenjs");

const RAIZ = path.join(__dirname, "..", "..");
const SALIDA = path.join(RAIZ, "docs", "presentacion", "presentacion.pptx");
const LEEME = path.join(RAIZ, "docs", "presentacion", "README.md");
const FIG = (f) => path.join(RAIZ, "docs", "figuras", "metro", f);

const PALABRAS_POR_MINUTO = 140;   // ritmo pausado de exposición en español
const TOPE_SEGUNDOS = 600;         // diez minutos para la parte principal

const TINTA = "1A1A1A", GRIS = "5C5C5C", GRIS_CLARO = "9B9B9B", REGLA = "D9D9D9";
const NARANJA = "F7931E";          // el naranja del Metro: cifras grandes y reglas
const NARANJA_TEXTO = "B35900";    // el mismo tono, más oscuro, para texto chico legible
const F = "Arial";
const APP = "sebastiancordoba.github.io/metro-denuncias-cdmx";
const REPO = "github.com/sebastiancordoba/caso-inseguridad-cdmx";

const pres = new Pptx();
pres.layout = "LAYOUT_16x9";       // 10 × 5.625 pulgadas
pres.theme = { headFontFace: F, bodyFontFace: F };
pres.author = "Sebastián Córdoba";
pres.title = "Robo denunciado por pasajero en el metro de la CDMX: qué estaciones cambian de lugar al medir por millón de entradas";
pres.subject = "Caso 2 de la titulación por caso, Licenciatura en Ciencia de Datos, ITAM";

const SECCIONES = ["El problema", "Los datos", "Lo que encontré", "Qué recomiendo", "Límites"];
const diapositivas = [];           // {titulo, seccion, anexo, dice, escena, extra, respuesta}

/* ------------------------------------------------------------------ piezas */
const txt = (s, texto, o) => s.addText(texto, Object.assign(
  { fontFace: F, fontSize: 13, color: TINTA, margin: 0, isTextBox: true, valign: "top" }, o));

// Arriba a la izquierda, en qué parte de la historia va la diapositiva.
const ruta = (s, seccion) => {
  if (seccion === "anexo") {
    txt(s, [{ text: "ANEXO", options: { bold: true, color: NARANJA_TEXTO } },
             { text: " · para preguntas", options: { color: GRIS_CLARO } }],
        { x: 0.6, y: 0.22, w: 8.8, h: 0.2, fontSize: 9 });
    return;
  }
  const runs = [];
  SECCIONES.forEach((n, i) => {
    const actual = n === seccion;
    runs.push({ text: n.toUpperCase(), options: { bold: actual, color: actual ? NARANJA_TEXTO : GRIS_CLARO } });
    if (i < SECCIONES.length - 1) runs.push({ text: "   ·   ", options: { color: GRIS_CLARO } });
  });
  txt(s, runs, { x: 0.6, y: 0.22, w: 8.8, h: 0.2, fontSize: 9 });
};
// El título es la afirmación; se apoya abajo para que la bajada quede siempre en su sitio.
const titulo = (s, t, tam) => txt(s, t, { x: 0.6, y: 0.42, w: 8.8, h: 0.82, fontSize: tam || 22,
                                          bold: true, valign: "bottom" });
const bajada = (s, t) => txt(s, t, { x: 0.6, y: 1.3, w: 8.8, h: 0.45, fontSize: 13, color: GRIS });
const regla = (s, x, y, w, color) =>
  s.addShape(pres.ShapeType.rect, { x, y, w, h: 0.025, fill: { color: color || REGLA }, line: { type: "none" } });
const antetitulo = (s, x, y, w, t) =>
  txt(s, t.toUpperCase(), { x, y, w, h: 0.22, fontSize: 9.5, bold: true, color: NARANJA_TEXTO });
// Bloque: regla naranja, antetítulo y texto. Devuelve dónde termina.
const bloque = (s, x, y, w, ante, cuerpo, alto, tam) => {
  regla(s, x, y, w, NARANJA);
  antetitulo(s, x, y + 0.09, w, ante);
  txt(s, cuerpo, { x, y: y + 0.36, w, h: alto, fontSize: tam || 13 });
  return y + 0.36 + alto;
};
const cifra = (s, x, y, w, valor, etiqueta, tam, altoEtiqueta, color) => {
  const alto = (tam || 44) / 72 * 1.2;
  txt(s, valor, { x, y, w, h: alto, fontSize: tam || 44, bold: true, color: color || NARANJA });
  txt(s, etiqueta, { x, y: y + alto + 0.02, w, h: altoEtiqueta || 0.6, fontSize: 12, color: GRIS });
  return y + alto + 0.02 + (altoEtiqueta || 0.6);
};
const pie = (s, t, y, alto) => txt(s, t, { x: 0.6, y: y || 4.78, w: 8.8, h: alto || 0.42, fontSize: 10, color: GRIS });
const imagen = (s, archivo, x, y, w, alt) => {
  const [pw, ph] = tamano(FIG(archivo));
  const h = w * ph / pw;
  s.addImage({ path: FIG(archivo), x, y, w, h, altText: alt });
  return y + h;
};
// Ancho y alto de un PNG, leídos de su cabecera: así la imagen nunca se deforma.
function tamano(archivo) {
  const b = fs.readFileSync(archivo);
  return [b.readUInt32BE(16), b.readUInt32BE(20)];
}
const tabla = (s, filas, o) => {
  const borde = [{ type: "none" }, { type: "none" }, { type: "solid", pt: 0.75, color: REGLA }, { type: "none" }];
  const cuerpo = filas.map((fila, i) => fila.map((c) => {
    const celda = typeof c === "object" ? c : { text: String(c) };
    celda.options = Object.assign({ border: borde }, i === 0 ? { bold: true, color: GRIS, fontSize: o.tamCabeza || 10 } : {}, celda.options || {});
    return celda;
  }));
  s.addTable(cuerpo, Object.assign({ fontFace: F, fontSize: 12, color: TINTA, valign: "middle",
                                      margin: [3, 5, 3, 5] }, o));
};
const fuerte = (t, color) => ({ text: t, options: { bold: true, color: color || TINTA } });

function nueva(d) {
  const s = pres.addSlide();
  s.background = { color: "FFFFFF" };
  diapositivas.push(Object.assign({ extra: 0, slide: s }, d));
  if (d.seccion) ruta(s, d.anexo ? "anexo" : d.seccion);
  const n = diapositivas.length;
  txt(s, String(n), { x: 8.9, y: 5.3, w: 0.5, h: 0.2, fontSize: 9, color: GRIS_CLARO, align: "right" });
  return s;
}

/* ================================================================ PRINCIPAL */

/* 1 · portada */
let s = nueva({
  titulo: "Portada: la pregunta",
  dice: "Buenas tardes. Soy Sebastián Córdoba. Este trabajo usa datos públicos para estudiar la inseguridad en el metro de la Ciudad de México. Mi pregunta es qué estaciones concentran más denuncias de robo por cada millón de personas que entran, y cuánto cambia el orden si solo se cuentan las denuncias. Voy en cinco partes: el problema, los datos, lo que encontré, qué recomiendo y los límites.",
});
regla(s, 0.6, 0.85, 1.2, NARANJA);
antetitulo(s, 0.6, 0.98, 8.8, "Titulación por caso · Caso 2: inseguridad urbana en la Ciudad de México");
txt(s, "Robo denunciado por pasajero en el metro de la CDMX: qué estaciones cambian de lugar al medir por millón de entradas",
    { x: 0.6, y: 1.3, w: 8.8, h: 1.45, fontSize: 28, bold: true });
txt(s, "¿Qué estaciones concentran más denuncias de robo por cada millón de personas que entran, y cuánto cambia el orden si solo se cuentan las denuncias?",
    { x: 0.6, y: 2.95, w: 8.4, h: 0.9, fontSize: 17, color: GRIS });
regla(s, 0.6, 4.05, 8.8);
txt(s, "Sebastián Córdoba", { x: 0.6, y: 4.2, w: 8.8, h: 0.3, fontSize: 15, bold: true });
txt(s, "Licenciatura en Ciencia de Datos, ITAM · jcordob5@itam.mx", { x: 0.6, y: 4.53, w: 8.8, h: 0.26, fontSize: 12, color: GRIS });

/* 2 · el problema */
s = nueva({
  seccion: "El problema", titulo: "La lista pública de “estaciones peligrosas” solo cuenta denuncias",
  dice: "Primero, el problema. La prensa publica cada cierto tiempo cuáles son las estaciones más peligrosas del metro y se lo atribuye a la Fiscalía. Encontré cuatro listas. No coinciden entre sí, ninguna explica cómo se hizo y las cuatro cuentan casos sin dividir entre cuánta gente pasa. Importa porque el metro es donde la gente de la ciudad se siente más insegura, el 77.7 por ciento según el INEGI, y porque quien reparte policías entre estaciones solo tiene esa lista.",
});
titulo(s, "La lista pública de “estaciones peligrosas” solo cuenta denuncias");
bajada(s, "Y es la única que tiene quien reparte la vigilancia entre estaciones.");
let y = bloque(s, 0.6, 1.85, 5.2, "Lo que se publica",
  "La prensa publica listas de las estaciones más peligrosas y se las atribuye a la Fiscalía. Encontré cuatro: Infobae (2024, 11 estaciones), Expansión (2024, 10), N+ (2023, 9) y ADN40 (2026, 5, de detenciones). No coinciden entre sí y ninguna explica su método. Las cuatro cuentan casos sin dividir entre cuánta gente pasa por cada estación.", 1.32);
bloque(s, 0.6, y + 0.15, 5.2, "Quién la usa",
  "La Secretaría de Seguridad Ciudadana, cuya Policía Auxiliar y Bancaria vigila el metro, y la gerencia de seguridad del Metro.", 0.45);
y = cifra(s, 6.3, 1.8, 3.1, "77.7 %", "de las personas de 18 años o más en la Ciudad de México se siente insegura en el transporte público, más que en cualquier otro lugar.", 44, 0.9);
txt(s, "INEGI, ENVIPE 2024", { x: 6.3, y: y + 0.05, w: 3.1, h: 0.2, fontSize: 9, color: GRIS_CLARO });
regla(s, 0.6, 4.55, 8.8);
pie(s, [fuerte("Denuncia: ", GRIS), { text: "aquí, una carpeta de investigación, el expediente que abre la Fiscalía General de Justicia de la Ciudad de México (FGJ) por cada denuncia. " },
        fuerte("INEGI: ", GRIS), { text: "Instituto Nacional de Estadística y Geografía. " },
        fuerte("ENVIPE: ", GRIS), { text: "su Encuesta Nacional de Victimización y Percepción sobre Seguridad Pública." }], 4.65, 0.55);

/* 3 · por qué contar no basta, y la pregunta */
s = nueva({
  seccion: "El problema", titulo: "Contar denuncias es, en buena parte, contar pasajeros",
  dice: "Contar no basta, porque una estación por la que entra mucha gente junta más denuncias aunque cada pasajero corra el mismo riesgo. En la lista de Infobae, cuatro de las once estaciones están entre las siete por donde entra más gente de toda la red, y Cuatro Caminos no tiene ni una denuncia en la Fiscalía de la Ciudad porque está en el Estado de México. De ahí sale mi pregunta. Por cada millón de entradas, ¿qué estaciones concentran más denuncias y cuánto cambia el orden frente al conteo?",
});
titulo(s, "Contar denuncias es, en buena parte, contar pasajeros");
bajada(s, "Una estación por la que entra mucha gente junta más denuncias aunque cada pasajero corra el mismo riesgo.");
antetitulo(s, 0.6, 1.88, 4.6, "Cuatro estaciones de la lista de Infobae");
tabla(s, [
  ["Estación", "Lugar por entradas", "Denuncias 2019–2024"],
  ["Indios Verdes", "2", "114"],
  ["Constitución de 1917", "3", "94"],
  ["Cuatro Caminos", "4", [fuerte("0"), { text: " (Estado de México)" }]].map((c) => Array.isArray(c) ? { text: c } : c),
  ["Universidad", "7", "28"],
], { x: 0.6, y: 2.15, w: 4.6, colW: [1.85, 1.05, 1.7], rowH: 0.3, fontSize: 12 });
txt(s, "Lugar entre las 163 estaciones de la red. Cuatro de las once de Infobae están entre las siete con más entradas.",
    { x: 0.6, y: 4.02, w: 4.6, h: 0.45, fontSize: 11, color: GRIS });
regla(s, 5.6, 1.88, 3.8, NARANJA);
antetitulo(s, 5.6, 1.97, 3.8, "La pregunta");
txt(s, "En las 124 estaciones de paso del metro de la Ciudad de México, ¿cuáles concentran más denuncias de robo a pasajero por millón de entradas, de 2019 a 2024, y cuánto cambia el orden frente al conteo?",
    { x: 5.6, y: 2.27, w: 3.8, h: 1.95, fontSize: 15, bold: true });
regla(s, 0.6, 4.55, 8.8);
pie(s, [fuerte("Entradas: ", GRIS), { text: "personas que cruzan el torniquete de una estación. " },
        fuerte("Estación de paso: ", GRIS), { text: "la que tiene una sola línea; la diapositiva 5 explica por qué solo esas. " },
        fuerte("Conteo: ", GRIS), { text: "ordenar por número de denuncias." }], 4.65, 0.55);

/* 4 · los datos */
s = nueva({
  seccion: "Los datos", titulo: "Tres archivos abiertos dan las denuncias, las entradas y el lugar",
  dice: "Los datos son tres archivos abiertos. Las denuncias vienen de las carpetas de investigación de la Fiscalía. Tomo un solo delito, robo a pasajero a bordo del metro, y son 8,366 carpetas en seis años, contadas por la fecha del robo. Las entradas vienen de la afluencia diaria que publica el Metro. Y el mapa de estaciones dice a qué estación pertenece cada denuncia, que es la más cercana si está a 150 metros o menos. Con eso, la tasa es denuncias entre millones de entradas, por estación y por año.",
});
titulo(s, "Tres archivos abiertos dan las denuncias, las entradas y el lugar");
bajada(s, "Los tres son públicos: cualquiera puede descargarlos y repetir el cálculo.");
const fuenteDatos = (x, ante, valor, texto) => {
  regla(s, x, 1.88, 2.75, NARANJA);
  antetitulo(s, x, 1.97, 2.75, ante);
  txt(s, valor, { x, y: 2.25, w: 2.75, h: 0.55, fontSize: 32, bold: true, color: NARANJA });
  txt(s, texto, { x, y: 2.85, w: 2.75, h: 1.25, fontSize: 12 });
};
fuenteDatos(0.6, "Denuncias · Fiscalía (FGJ)", "8,366",
  "carpetas de “robo a pasajero a bordo de metro”, con y sin violencia, de 2019 a 2024. Cada una cuenta en la fecha del robo. El archivo tiene corte al 31 de enero de 2025.");
fuenteDatos(3.625, "Entradas · Metro (STC)", "6,600 M",
  "entradas por torniquete en toda la red de 2019 a 2024, por estación y por día. STC: Sistema de Transporte Colectivo, el organismo que opera el metro. M: millones.");
fuenteDatos(6.65, "Lugar · mapa de estaciones", "150 m",
  "Cada denuncia va a la estación más cercana si su coordenada cae a 150 m o menos. La distancia mediana es de 31 m.");
regla(s, 0.6, 4.25, 8.8, NARANJA);
antetitulo(s, 0.6, 4.34, 8.8, "La tasa");
txt(s, [fuerte("denuncias de una estación en el año  ÷  millones de entradas de esa estación ese año")],
    { x: 0.6, y: 4.62, w: 8.8, h: 0.3, fontSize: 15 });
txt(s, "Se lee como denuncias por millón de entradas.", { x: 0.6, y: 4.97, w: 8.8, h: 0.22, fontSize: 11, color: GRIS });

/* 5 · correspondencias y el universo */
s = nueva({
  seccion: "Los datos", titulo: "Donde se cambia de línea, el torniquete no cuenta a todos y la tasa no sirve",
  dice: "Antes de comparar hay que ver dónde la tasa sirve. Las diez estaciones con más denuncias de toda la red son de correspondencia, donde se cruzan líneas, y su tasa sale casi tres veces más alta. Pero quien llega transbordando no cruzó el torniquete de esa estación, así que el denominador se queda corto. Con casi dos transbordos por cada entrada se explicaría toda la diferencia. Aquí se cayó mi primera hipótesis, que bastaba dividir para comparar toda la red. Dejo fuera esas 28 y las 11 del Estado de México, y quedan 124 estaciones de paso con 2,945 denuncias.",
});
titulo(s, "Donde se cambia de línea, el torniquete no cuenta a todos y la tasa no sirve");
bajada(s, "Estación de correspondencia: donde se cruzan dos o más líneas y se puede transbordar sin salir.");
cifra(s, 0.6, 1.85, 2.2, "2.10", "denuncias por millón de entradas en las 28 estaciones de correspondencia", 40, 0.8);
cifra(s, 3.0, 1.85, 2.2, "0.71", "en las 124 estaciones de paso", 40, 0.62, TINTA);
txt(s, "Las 10 estaciones con más denuncias de toda la red son de correspondencia. Quien llega transbordando no cruzó el torniquete de esa estación, así que sus entradas se quedan cortas. Con casi dos transbordos por cada entrada se explicaría toda la diferencia, y ese flujo es verosímil.",
    { x: 0.6, y: 3.42, w: 4.6, h: 1.1, fontSize: 12.5 });
regla(s, 5.6, 1.88, 3.8, NARANJA);
antetitulo(s, 5.6, 1.97, 3.8, "Qué queda para comparar");
const paso = (yy, num, texto, final) => {
  txt(s, num, { x: 5.6, y: yy, w: 0.85, h: 0.3, fontSize: 15, bold: true, color: final ? NARANJA_TEXTO : TINTA, align: "right" });
  txt(s, texto, { x: 6.55, y: yy + 0.03, w: 2.85, h: 0.3, fontSize: 11.5, color: final ? TINTA : GRIS, bold: !!final });
};
paso(2.28, "163", "estaciones en la red");
paso(2.56, "− 11", "en el Estado de México: otra fiscalía");
paso(2.84, "− 28", "de correspondencia");
paso(3.12, "124", "estaciones de paso", true);
regla(s, 5.6, 3.5, 3.8);
paso(3.6, "8,366", "denuncias, 2019–2024");
paso(3.88, "6,766", "ubicadas en alguna estación");
paso(4.16, "2,945", "en las 124 de paso", true);
regla(s, 0.6, 4.6, 8.8);
txt(s, "Las 28 correspondencias quedan fuera porque su tasa no se puede medir con datos abiertos, lo cual no quiere decir que sean seguras.",
    { x: 0.6, y: 4.7, w: 8.8, h: 0.45, fontSize: 13, bold: true });

/* 6 · hallazgo 1: dividir cambia el orden */
s = nueva({
  seccion: "Lo que encontré", titulo: "Dividir cambia el orden: de las 10 primeras por conteo, solo 3 siguen arriba por tasa",
  dice: "El primer hallazgo es que dividir sí cambia el orden. La correlación de Spearman compara posiciones. Uno es el mismo orden y cero, ninguna relación. Entre conteo y tasa sale 0.454, y de las diez primeras por conteo solo tres siguen arriba por tasa. Antes de calcular escribí qué me haría aceptar que el conteo bastaba, 0.9 y nueve de diez, y no se acerca. Bajan las grandes terminales. Indios Verdes es la primera por conteo y la 73 por tasa, porque tiene muchísima afluencia y una tasa ordinaria. Suben estaciones medianas como Villa de Aragón, Nativitas y Portales, que no aparecen en ninguna lista publicada.",
});
titulo(s, "Dividir cambia el orden: de las 10 primeras por conteo, solo 3 siguen arriba por tasa");
bajada(s, "Las 124 estaciones de paso, 2019–2024. Aquí la tasa es la cruda: denuncias entre entradas, todavía sin modelo.");
y = imagen(s, "conteo_vs_tasa.png", 0.6, 1.85, 5.0,
  "Gráfica de dispersión: lugar por número de denuncias contra lugar por denuncias por millón de entradas en las 124 estaciones de paso.");
txt(s, "Cada punto es una estación. Si los dos órdenes coincidieran, los puntos caerían sobre la diagonal.",
    { x: 0.6, y: y + 0.06, w: 5.0, h: 0.4, fontSize: 10, color: GRIS });
cifra(s, 5.9, 1.8, 3.5, "ρ = 0.454", "correlación de Spearman entre los dos órdenes: vale 1 si ordenan igual y 0 si no se parecen.", 32, 0.6);
y = bloque(s, 5.9, 3.02, 3.5, "Qué me habría hecho descartar la tasa",
  "0.9 o más, con 9 de 10 en común. Lo escribí antes de calcular. Con otros radios y mínimos de denuncias da entre 0.10 y 0.46.", 0.62, 11.5);
bloque(s, 5.9, y + 0.08, 3.5, "Quién se mueve",
  "Indios Verdes baja del lugar 1 al 73. Suben estaciones medianas que no salen en ninguna lista, como Villa de Aragón, Nativitas y Portales.", 0.62, 11.5);

/* 7 · hallazgo 2: pocas denuncias, el modelo */
s = nueva({
  seccion: "Lo que encontré", titulo: "Con pocas denuncias la tasa engaña; el modelo la ajusta según la evidencia",
  dice: "El segundo hallazgo es que con pocas denuncias la tasa engaña. Tlaltenco tiene cinco denuncias y una tasa de casi el doble del conjunto, pero su intervalo va de 0.44 a 3.20, así que no se sabe cuál es su tasa. Por eso uso un modelo de conteos que acerca la tasa de cada estación a la de una estación típica, y la acerca más cuanto menos evidencia tiene. A eso le llamo tasa encogida. Con ella, 25 estaciones se distinguen de la típica, no las 39 de las pruebas una por una. Y con menos de quince denuncias, la estación se marca como evidencia insuficiente.",
});
titulo(s, "Con pocas denuncias la tasa engaña; el modelo la ajusta según la evidencia");
bajada(s, "Intervalo al 95 %: el rango de tasas compatibles con los datos. Mientras menos denuncias, más ancho.");
y = imagen(s, "intervalos.png", 0.6, 1.9, 5.0,
  "Intervalos al 95 % de la tasa de Tlaltenco (5 denuncias), Indios Verdes (114) y Merced (90), con la tasa del conjunto de 0.71.");
txt(s, "Tasa cruda de tres estaciones, 2019–2024. La línea punteada es la tasa del conjunto de las 124.",
    { x: 0.6, y: y + 0.06, w: 5.0, h: 0.4, fontSize: 10, color: GRIS });
y = bloque(s, 5.9, 1.88, 3.5, "El problema",
  "Tlaltenco tiene 5 denuncias. Su tasa, 1.37, casi duplica la del conjunto, pero su intervalo va de 0.44 a 3.20: con esos datos no se sabe cuál es.", 0.85, 12);
bloque(s, 5.9, y + 0.1, 3.5, "Lo que hace el modelo",
  "Un modelo de conteos (binomial negativo, con un efecto propio de cada estación) acerca la tasa de cada estación a la de una estación típica, y la acerca más cuanto menos denuncias tiene. A eso le llamo tasa encogida.", 1.2, 12);
regla(s, 0.6, 4.6, 8.8);
txt(s, [fuerte("25 estaciones se distinguen de la típica "), { text: "(su intervalo no la incluye): 14 por arriba y 11 por abajo. Con pruebas una por una salían 39. Además, una estación con menos de 15 denuncias se marca como evidencia insuficiente." }],
    { x: 0.6, y: 4.7, w: 8.8, h: 0.5, fontSize: 12 });

/* 8 · hallazgo 3: dos objetivos */
s = nueva({
  seccion: "Lo que encontré", titulo: "Conteo y tasa sirven a objetivos distintos",
  dice: "El tercer hallazgo es que la lista que sirve depende de para qué se use. Elegí diez estaciones con los datos de 2019 a 2023 y medí qué pasó en 2024, un año que el modelo no vio. Las diez por conteo cubren 92 denuncias, más del doble que las diez por tasa. Pero las diez por tasa cubren 0.77 denuncias por millón de entradas contra 0.57, un 35 por ciento más por pasajero, con un tercio de la afluencia que vigilar. Cubrir volumen y proteger igual a cada pasajero son objetivos distintos, y hoy solo se publica la primera lista sin decir cuál se persigue.",
});
titulo(s, "Conteo y tasa sirven a objetivos distintos");
bajada(s, "Prueba fuera de muestra: elegí 10 estaciones con los datos de 2019 a 2023 y medí qué pasó en 2024, un año que el modelo no vio.");
tabla(s, [
  ["Elegir 10 estaciones por…", "Denuncias de 2024 que cubren", "Denuncias por millón de entradas", "Entradas que vigilar"],
  ["conteo", { text: "92", options: { bold: true } }, "0.57", "160 millones"],
  ["tasa encogida", "41", { text: "0.77", options: { bold: true, color: NARANJA_TEXTO } }, "53 millones"],
], { x: 0.6, y: 1.95, w: 8.8, colW: [2.6, 2.1, 2.2, 1.9], rowH: [0.42, 0.42, 0.42], fontSize: 15, tamCabeza: 10.5 });
bloque(s, 0.6, 3.45, 4.2, "Si el objetivo es cubrir más denuncias",
  "conviene el conteo, que cubre más del doble. Para eso es una buena regla.", 0.5);
bloque(s, 5.2, 3.45, 4.2, "Si es proteger igual a cada pasajero",
  "conviene la tasa: 35 % más denuncias por pasajero vigilado, con un tercio de la afluencia.", 0.5);
regla(s, 0.6, 4.6, 8.8);
txt(s, "Hoy solo se publica la lista por conteo, y nadie dice qué objetivo persigue.",
    { x: 0.6, y: 4.72, w: 8.8, h: 0.35, fontSize: 15, bold: true });

/* 9 · la lista de prioridad */
s = nueva({
  seccion: "Qué recomiendo", titulo: "La lista de prioridad junta los dos objetivos",
  dice: "Faltaba una lista que juntara las dos. Es la de prioridad y cabe en tres frases. Cada estación tiene un lugar por conteo y otro por tasa. Su prioridad es el promedio de los dos. Y solo entran estaciones con quince denuncias o más. Zócalo es segunda por conteo y séptima por tasa, con promedio 4.5, y queda primera en prioridad. Indios Verdes es primera y 67, con promedio 34, y queda en el lugar 26. Probada igual que las otras, con veinte estaciones cubre 99 denuncias en 2024 y más denuncias por pasajero que las otras dos. Se calcula a mano y no pierde frente a ninguna, aunque no digo que sea la mejor posible.",
});
titulo(s, "La lista de prioridad junta los dos objetivos");
bajada(s, "En la aplicación se llama Prioridad (volumen y riesgo). La regla tiene tres pasos.");
const pasoRegla = (yy, n, t) => {
  txt(s, String(n), { x: 0.6, y: yy - 0.04, w: 0.4, h: 0.45, fontSize: 26, bold: true, color: NARANJA });
  txt(s, t, { x: 1.05, y: yy, w: 3.65, h: 0.62, fontSize: 13 });
};
pasoRegla(1.9, 1, "Cada estación tiene dos lugares: uno por conteo y otro por tasa encogida.");
pasoRegla(2.55, 2, "Su prioridad es el promedio de los dos. El promedio más bajo va primero.");
pasoRegla(3.2, 3, "Solo entran estaciones con 15 denuncias o más. Las demás van al final.");
antetitulo(s, 5.1, 1.88, 4.3, "Cuatro ejemplos, con 2019–2024");
tabla(s, [
  ["Estación", "Conteo", "Tasa", "Promedio", "Prioridad"],
  ["Zócalo/Tenochtitlan", "2", "7", "4.5", fuerte("1", NARANJA_TEXTO)],
  ["Merced", "4", "6", "5", fuerte("2", NARANJA_TEXTO)],
  ["Villa de Aragón", "15", "3", "9", fuerte("4", NARANJA_TEXTO)],
  ["Indios Verdes", "1", "67", "34", fuerte("26", NARANJA_TEXTO)],
], { x: 5.1, y: 2.15, w: 4.3, colW: [1.7, 0.6, 0.55, 0.75, 0.7], rowH: 0.3, fontSize: 12 });
regla(s, 0.6, 3.95, 8.8, NARANJA);
antetitulo(s, 0.6, 4.04, 8.8, "Probada igual que las otras dos: 20 estaciones elegidas con 2019–2023, medidas en 2024");
txt(s, [{ text: "Cubre " }, fuerte("99 denuncias"), { text: ", entre las 73 de la tasa y las 135 del conteo, y " }, fuerte("0.68 por millón de entradas"),
        { text: ", más que las dos (0.61 y 0.58). Se calcula a mano y no pierde frente a ninguna de las otras dos, aunque no afirmo que sea la mejor posible." }],
    { x: 0.6, y: 4.32, w: 8.8, h: 0.75, fontSize: 13 });

/* 10 · las tres listas de hoy, y la demostración */
s = nueva({
  seccion: "Qué recomiendo", titulo: "Para desplegar hoy: tres listas, y cuatro estaciones están en las tres",
  escena: "DEMOSTRACIÓN EN VIVO, unos 40 segundos. Si la aplicación no carga, sigo con esta lámina.",
  dice: "Esto es lo que entregaría hoy, ya con los seis años. Son las tres listas lado a lado. Zócalo, Merced, Portales y Etiopía están en las tres. En la aplicación se ve así. Abre en la lista de prioridad. Si cambio a conteo, Indios Verdes queda arriba. Si cambio a tasa, que es la encogida, baja al lugar 67. Las estaciones con menos de quince denuncias se dibujan huecas, como Hangares, que está entre las diez primeras por tasa con solo doce. Y la pestaña Dónde desplegar tiene las tres listas con lo que cubrió cada una en 2024.",
  extra: 20,
});
titulo(s, "Para desplegar hoy: tres listas, y cuatro estaciones están en las tres");
bajada(s, "Las 10 primeras de cada lista con los seis años, 2019–2024. En naranja, las que aparecen en las tres.");
const EN_LAS_TRES = new Set(["Zócalo/Tenochtitlan", "Merced", "Portales", "Etiopía"]);
const columna = (x, ante, sub, filas) => {
  regla(s, x, 1.88, 2.75, NARANJA);
  antetitulo(s, x, 1.97, 2.75, ante);
  txt(s, sub, { x, y: 2.2, w: 2.75, h: 0.2, fontSize: 9.5, color: GRIS });
  filas.forEach(([n, nombre, nota], i) => {
    const marcada = EN_LAS_TRES.has(nombre);
    const runs = [{ text: `${n}  `, options: { color: GRIS_CLARO, bold: true } },
                  { text: nombre, options: { bold: marcada, color: marcada ? NARANJA_TEXTO : TINTA } }];
    if (nota) runs.push({ text: `  ${nota}`, options: { color: GRIS, fontSize: 9 } });
    txt(s, runs, { x, y: 2.48 + i * 0.215, w: 2.75, h: 0.21, fontSize: 11.5 });
  });
};
columna(0.6, "Por conteo", "más denuncias", [
  [1, "Indios Verdes"], [2, "Zócalo/Tenochtitlan"], [3, "Constitución de 1917"], [4, "Merced"], [5, "Buenavista"],
  [6, "Insurgentes"], [7, "Tasqueña"], [8, "Polanco"], [9, "Etiopía"], [10, "Portales", "y Revolución, empatadas"]]);
columna(3.625, "Por tasa encogida", "más denuncias por millón de entradas", [
  [1, "Bosque de Aragón"], [2, "Ciudad Deportiva"], [3, "Villa de Aragón"], [4, "Portales"], [5, "Nativitas"],
  [6, "Merced"], [7, "Zócalo/Tenochtitlan"], [8, "Ricardo Flores Magón"], [9, "Etiopía"], [10, "Hangares", "evidencia insuficiente"]]);
columna(6.65, "Prioridad (volumen y riesgo)", "promedio de los dos lugares", [
  [1, "Zócalo/Tenochtitlan"], [2, "Merced"], [3, "Portales"], [4, "Villa de Aragón"], [5, "Nativitas"],
  [6, "Etiopía"], [7, "Insurgentes"], [8, "Revolución"], [9, "Polanco"], [10, "Niños Héroes"]]);
regla(s, 0.6, 4.75, 8.8);
txt(s, [fuerte("Aplicación: "), { text: APP + ". " },
        { text: "Etiopía es Etiopía/Plaza de la Transparencia; Niños Héroes, Niños Héroes/Poder Judicial CDMX.", options: { color: GRIS } }],
    { x: 0.6, y: 4.83, w: 8.8, h: 0.4, fontSize: 10.5 });

/* 11 · recomendaciones */
s = nueva({
  seccion: "Qué recomiendo", titulo: "Tres recomendaciones",
  dice: "Tres recomendaciones, en orden de lo que cambia con menos esfuerzo. Publicar las tres listas y decir qué objetivo se persigue; no hacen falta datos nuevos, todo se rehace con un comando. Elegir la lista según el objetivo. Si se busca que cada pasajero tenga la misma protección, sirve la tasa, o la de prioridad si también importa el volumen; si se busca cubrir más denuncias, el conteo es una buena regla. Y no mover policías por estaciones con poca evidencia o cuyo intervalo incluye la tasa típica.",
});
titulo(s, "Tres recomendaciones");
bajada(s, "En orden de lo que cambia con menos esfuerzo.");
const reco = (yy, n, cabeza, detalle) => {
  txt(s, String(n), { x: 0.6, y: yy - 0.05, w: 0.45, h: 0.5, fontSize: 28, bold: true, color: NARANJA });
  txt(s, cabeza, { x: 1.15, y: yy, w: 8.25, h: 0.32, fontSize: 16, bold: true });
  txt(s, detalle, { x: 1.15, y: yy + 0.36, w: 8.25, h: 0.48, fontSize: 13, color: GRIS });
  regla(s, 0.6, yy + 0.92, 8.8);
};
reco(1.9, 1, "Publicar las tres listas y decir qué objetivo se persigue.",
  "No hacen falta datos nuevos: todo sale de archivos públicos y se rehace con un comando.");
reco(2.92, 2, "Elegir la lista según el objetivo.",
  "Para proteger igual a cada pasajero, la tasa, o la de prioridad si también importa el volumen. Para cubrir más denuncias, el conteo es una buena regla.");
reco(3.94, 3, "No mover vigilancia por poca evidencia.",
  "Ni por estaciones con menos de 15 denuncias ni por las que tienen un intervalo que incluye la tasa típica.");
txt(s, "Cada lista debe llevar su fecha de corte (en este trabajo, 31 de enero de 2025), porque la Fiscalía corrige sus carpetas después de publicarlas.",
    { x: 0.6, y: 4.9, w: 8.2, h: 0.38, fontSize: 10.5, color: GRIS });

/* 12 · límites */
s = nueva({
  seccion: "Límites", titulo: "Todo se mide con denuncias, y la mayoría de los delitos no se denuncia",
  dice: "Los límites. El más grande es que todo esto son denuncias. La cifra negra en la Ciudad es de 93 por ciento. De cada cien delitos, siete llegan a una carpeta. Si eso cambia de una estación a otra, una tasa alta puede ser más disposición a denunciar y no más robo. Descarté la causa más obvia, una agencia del Ministerio Público dentro de la estación, pero no todas. Las 28 correspondencias quedan fuera porque no hay datos de transbordos. Y más información sobre cada estación no predice mejor el año siguiente, porque de un año a otro domina el ruido.",
});
titulo(s, "Todo se mide con denuncias, y la mayoría de los delitos no se denuncia");
bajada(s, "Lo que este trabajo no puede decir.");
y = cifra(s, 0.6, 1.8, 3.0, "93 %", "es la cifra negra en la Ciudad de México: los delitos que no se denuncian o que no llegan a carpeta. De cada 100, llegan 7.", 54, 1.05);
txt(s, "INEGI, ENVIPE 2024. Todos los delitos de 2023, no solo los del metro.", { x: 0.6, y: y + 0.05, w: 3.0, h: 0.4, fontSize: 9, color: GRIS_CLARO });
y = bloque(s, 4.0, 1.88, 5.4, "Si el subregistro cambia de una estación a otra",
  "una tasa alta puede ser más disposición a denunciar y no más robo. Descarté la causa más obvia, una agencia del Ministerio Público (la oficina donde se denuncia) dentro de la estación, pero no todas.", 0.85, 12.5);
y = bloque(s, 4.0, y + 0.08, 5.4, "Sin datos de transbordos",
  "las 28 correspondencias quedan fuera. El Metro publica entradas, no transbordos.", 0.45, 12.5);
bloque(s, 4.0, y + 0.08, 5.4, "Más información no predice mejor",
  "Agregué al modelo la línea, los delitos alrededor, el tamaño y la tendencia de cada estación, y la lista del año siguiente no mejora: de un año a otro domina el ruido de conteos chicos.", 0.65, 12.5);

/* 13 · cierre */
s = nueva({
  titulo: "Cierre: la respuesta",
  dice: "Cierro con la respuesta. Por pasajero, el orden de las estaciones cambia, y qué lista usar depende del objetivo, que hoy nadie declara. La aplicación y el repositorio, con el código y los datos, están en esas dos direcciones. Gracias.",
});
regla(s, 0.6, 0.85, 1.2, NARANJA);
antetitulo(s, 0.6, 0.98, 8.8, "La respuesta");
txt(s, "Por pasajero, el orden de las estaciones cambia. Qué lista usar depende del objetivo, y hoy nadie lo declara.",
    { x: 0.6, y: 1.35, w: 8.6, h: 1.25, fontSize: 24, bold: true });
txt(s, "Gracias.", { x: 0.6, y: 2.75, w: 8.8, h: 0.6, fontSize: 30, bold: true, color: NARANJA });
regla(s, 0.6, 3.6, 8.8);
txt(s, [fuerte("Aplicación   "), { text: APP }], { x: 0.6, y: 3.75, w: 8.8, h: 0.3, fontSize: 14 });
txt(s, [fuerte("Código y datos   "), { text: REPO }], { x: 0.6, y: 4.12, w: 8.8, h: 0.3, fontSize: 14 });
const PRINCIPALES = diapositivas.length;

/* =================================================================== ANEXO */
const anexo = (titulo_, corto, respuesta) => {
  const sl = nueva({ seccion: "anexo", anexo: true, titulo: titulo_, corto, respuesta });
  titulo(sl, titulo_, 20);
  return sl;
};

/* A0 · índice del anexo (se llena al final, cuando ya se sabe en qué número cae cada una) */
s = nueva({ titulo: "Anexo: índice", anexo: true, respuesta: "Índice del anexo. Para responder una pregunta, ir directo al número de diapositiva." });
const indice = s;

anexo("Las cuatro listas publicadas, de cerca", "Las cuatro listas publicadas",
  "Si preguntan de dónde salen las listas, son las cuatro que se pudieron abrir y leer completas. Expansión coincide exactamente con las diez primeras por conteo de los datos abiertos, y eso confirma que esas listas son conteos. El reporte del Consejo de Evaluación que citan no está publicado o no se encontró.");
s = diapositivas[diapositivas.length - 1].slide;
bajada(s, "Ninguna declara método ni divide entre cuánta gente pasa por cada estación.");
tabla(s, [
  ["Medio y fecha", "Qué lista da", "De qué", "Lo que hay que saber"],
  ["Infobae, 11 ene 2024", "11 estaciones, sin cifras", "robo a pasajeros", "Incluye Cuatro Caminos, que está en el Estado de México y tiene cero carpetas de la FGJ"],
  ["Expansión, 30 nov 2024", "10 estaciones", "robo dentro de las instalaciones", "Son exactamente las 10 primeras por conteo de los datos abiertos. Publica 902 carpetas de enero a septiembre de 2024; los datos abiertos dan 896"],
  ["N+, 18 may 2023", "9 estaciones", "robo sin violencia", "Explica que Pantitlán encabeza “por la gran afluencia de personas”"],
  ["ADN40, 12 ene 2026", "5 estaciones", "detenciones por robo de celular", "No son carpetas de investigación"],
], { x: 0.6, y: 1.85, w: 8.8, colW: [1.75, 1.6, 1.75, 3.7], fontSize: 11, valign: "top" });
pie(s, "Infobae y Expansión dicen basarse en un reporte del Consejo de Evaluación de la Ciudad de México. Ninguna lo enlaza y no se encontró publicado.", 4.85, 0.35);

anexo("Hipótesis de viabilidad: el criterio de rechazo se escribió antes de calcular", "Hipótesis de viabilidad (C1–C3, T1–T5)",
  "Si preguntan cómo sé que no acomodé el criterio, cada prueba tenía su criterio escrito antes de correrla, y la regla era parar en la primera que fallara. C2 falló y por eso el trabajo se acotó a las 124 estaciones de paso.");
s = diapositivas[diapositivas.length - 1].slide;
tabla(s, [
  ["", "Afirmación", "Se rechaza si", "Resultado", "Veredicto"],
  ["C1", "En toda la red, conteo y tasa ordenan distinto", "ρ ≥ 0.9 y 9 de 10 en común", "ρ = 0.693; 8 en común", "se sostiene"],
  ["C2", "La tasa de las correspondencias es comparable con la de las de paso", "7 o más correspondencias entre las 10 primeras por tasa, o 12 entre las 20", "9 de 10 y 17 de 20", fuerte("rechazada", NARANJA_TEXTO)],
  ["T1–T4", "Una agencia del Ministerio Público en la estación infla sus denuncias", "el exceso persiste en la denuncia por internet; Observatorio sin anomalía", "persiste: 3.5 veces por internet; Observatorio en el percentil 15", fuerte("rechazada", NARANJA_TEXTO)],
  ["T5", "En las 124 de paso, conteo y tasa ordenan distinto", "ρ ≥ 0.9 y 9 de 10 en común", "ρ = 0.454; 3 en común; igual en nueve variantes", "se sostiene"],
  ["C3", "Las denuncias crecen en proporción a las entradas", "2020 o 2021 fuera de ±25 % de la tasa de 2019", "0.50 y 0.68 veces la de 2019", "no se sostiene"],
], { x: 0.6, y: 1.5, w: 8.8, colW: [0.6, 2.55, 2.35, 2.2, 1.1], fontSize: 10.5, valign: "top" });
pie(s, "ρ: correlación de Spearman entre dos órdenes (1, mismo orden; 0, sin relación). C3 comparaba contra un 2019 que tiene su propio quiebre; la diapositiva de los tres periodos lo explica.", 4.85, 0.38);

anexo("Hipótesis del modelo, registradas antes de ajustarlo", "Hipótesis del modelo (M1–M7)",
  "Si preguntan por qué creerle a estas pruebas, las siete quedaron escritas y fechadas antes del primer ajuste. La de encoger se rechazó y se reporta; la de predecir 2024 pasa por tres milésimas y así se dice.");
s = diapositivas[diapositivas.length - 1].slide;
tabla(s, [
  ["", "Afirmación", "Se rechaza si", "Resultado"],
  ["M1", "Hace falta la binomial negativa: la Poisson no basta", "p > 0.05 en la razón de verosimilitudes, o AIC a favor de la Poisson", "LR = 21.4, p < 0.0001; se sostiene"],
  ["M2", "Las estaciones difieren de verdad entre sí", "p > 0.05 contra σv = 0", "LR = 91.3; σv = 0.40; se sostiene"],
  ["M3", "Encoger conserva el orden y saca de las 10 primeras a las de menos de 15 denuncias", "ρ < 0.9, o una de menos de 15 denuncias entre las 10 primeras", [fuerte("rechazada", NARANJA_TEXTO), { text: ": Hangares (12 denuncias) queda en el lugar 10" }]],
  ["M4", "Menos de 39 distinguibles, y conserva 12 o más de las 19 robustas", "39 o más, o menos de 12", "25 distinguibles; conserva 19 de 19"],
  ["M5", "El orden de 2019–2023 predice 2024 mejor que la tasa cruda y que el conteo", "ρ ≤ 0.30, o menor que alguno de los dos", "0.303 contra 0.261 y 0.289; se sostiene por 0.003"],
  ["M6", "Las 10 primeras por tasa cubren más denuncias por millón en 2024 que las 10 por conteo", "no superarlas", "0.77 contra 0.57; se sostiene"],
  ["M7", "Quitar abril a junio de 2020 no cambia el orden", "ρ < 0.98", "ρ = 0.9985; se sostiene"],
].map((f) => f.map((c) => Array.isArray(c) ? { text: c } : c)),
  { x: 0.6, y: 1.35, w: 8.8, colW: [0.5, 3.1, 2.65, 2.55], fontSize: 10, valign: "top" });
pie(s, "Fijadas el 20 de septiembre de 2026 a las 19:43, antes del primer ajuste del modelo (19:50). LR: razón de verosimilitudes. AIC: criterio de Akaike. σv: cuánto difieren las estaciones entre sí.", 4.82, 0.4);

anexo("El modelo, término por término", "El modelo, término por término",
  "Si preguntan por qué no usé una librería, ninguna de las instaladas ajustaba una binomial negativa con efecto aleatorio; son nueve parámetros y una integral por estación. Si preguntan por qué 0.63 y no 0.71, es porque 0.71 es el total de denuncias entre el total de entradas, que pesa más a las estaciones grandes; 0.63 es la estación típica del modelo en un año promedio.");
s = diapositivas[diapositivas.length - 1].slide;
txt(s, [{ text: "y(s,t) ~ NB(μ(s,t), φ),  con  v(s) ~ Normal(0, σv²)", options: { breakLine: true } },
        { text: "log μ(s,t) = log E(s,t) + α + v(s) + γ(t)" }],
    { x: 0.6, y: 1.32, w: 8.8, h: 0.5, fontSize: 14, bold: true });
const termino = (yy, simbolo, que) => {
  txt(s, simbolo, { x: 0.6, y: yy, w: 1.35, h: 0.4, fontSize: 12, bold: true, color: NARANJA_TEXTO });
  txt(s, que, { x: 2.0, y: yy, w: 7.4, h: 0.42, fontSize: 12 });
};
termino(1.95, "y(s,t)", "denuncias de la estación s en el año t: 715 celdas, 124 estaciones por hasta seis años, sin abril a junio de 2020");
termino(2.38, "NB, φ", "binomial negativa: admite más variación que la Poisson. φ = 16.5 (intervalo 9.2 a 29.5): 24 % de varianza extra en una celda típica");
termino(2.81, "E(s,t)", "millones de entradas de esa estación en los meses abiertos; convierte el conteo en tasa");
termino(3.24, "exp(α)", "0.633 denuncias por millón de entradas (0.580 a 0.691): la estación típica en un año promedio");
termino(3.67, "v(s), σv", "el efecto de cada estación. σv = 0.402: el 95 % de las estaciones cae entre 0.45 y 2.2 veces la típica");
termino(4.1, "exp(γ(t))", "el efecto de año: 1.67 en 2019; 0.96, 1.11, 1.11 y 0.73; 0.70 en 2024");
regla(s, 0.6, 4.65, 8.8);
pie(s, "Se publica exp(α + v(s)), la tasa encogida. La binomial negativa gana a la Poisson (LR = 21.4; AIC 19.4 menor), y la diferencia importa: la Poisson daría 37 estaciones distinguibles y la binomial negativa, 25. Ajuste por máxima verosimilitud marginal con cuadratura de Gauss–Hermite.", 4.72, 0.5);

anexo("Encoger en vez de corregir por comparaciones múltiples", "Encoger y comparaciones múltiples",
  "Si preguntan por qué no corregí por comparaciones múltiples, es porque esa corrección ensancha todos los intervalos por igual y trata igual a Merced, con 90 denuncias, que a Hangares, con 12. El modelo estima cuánto varían de verdad las estaciones y encoge a cada una según su evidencia.");
s = diapositivas[diapositivas.length - 1].slide;
cifra(s, 0.6, 1.4, 2.6, "39 → 25", "estaciones distinguibles de la típica: con pruebas una por una y con el modelo. Por azar se esperaban unas 6.", 34, 0.85);
y = bloque(s, 3.6, 1.45, 5.8, "Qué conserva y qué descarta",
  "19 de las 39 seguían distinguiéndose al quitar cualquier año (las robustas). El modelo conserva las 19, descarta 14 de las 20 frágiles y no agrega ninguna nueva.", 0.65, 12);
y = bloque(s, 3.6, y + 0.08, 5.8, "Cuánto encoge",
  "Cada estación conserva una parte de su distancia a la típica: la mediana es 0.60 con menos de 15 denuncias y 0.83 con 40 o más. Bosque de Aragón baja de 2.08 a 1.40; Obrera sube de 0.04 a 0.28.", 0.65, 12);
regla(s, 0.6, 3.55, 8.8);
txt(s, [fuerte("Las 14 por arriba: "), { text: "Bosque de Aragón, Ciudad Deportiva, Villa de Aragón, Portales, Nativitas, Merced, Zócalo/Tenochtitlan, Etiopía, Camarones, Moctezuma, Insurgentes, Revolución, Niños Héroes y Polanco." }],
    { x: 0.6, y: 3.65, w: 8.8, h: 0.5, fontSize: 12 });
txt(s, [fuerte("Encoger no basta: "), { text: "Hangares, con 12 denuncias, queda en el lugar 10 con un intervalo de 0.90 a 2.52 veces la típica. Por eso la aplicación marca como evidencia insuficiente todo lo que tiene menos de 15 denuncias." }],
    { x: 0.6, y: 4.25, w: 8.8, h: 0.5, fontSize: 12 });
pie(s, "Tasqueña, Indios Verdes y Constitución de 1917 no se distinguen por abajo (0.83, 1.01 y 0.88 veces la típica, con intervalos que incluyen 1): son terminales con tasa en la media.", 4.85, 0.35);

anexo("Las correspondencias, en números", "Las correspondencias, en números",
  "Si preguntan por Hidalgo y Guerrero, necesitarían ocho y siete transbordos por cada entrada para bajar a la tasa de las de paso. Ahí el transbordo no alcanza a explicarlo, y queda como hallazgo abierto.");
s = diapositivas[diapositivas.length - 1].slide;
bajada(s, "Las 10 estaciones con más denuncias de toda la red, 2019–2024. Las diez son de correspondencia.");
tabla(s, [
  ["Estación", "Líneas", "Denuncias", "Entradas (M)", "Tasa"],
  ["Pantitlán", "1, 5, 9, A", "491", "306", "1.60"], ["Hidalgo", "2, 3", "483", "76", "6.38"],
  ["Pino Suárez", "1, 2", "288", "94", "3.07"], ["Chabacano", "2, 8, 9", "254", "69", "3.69"],
  ["Tacubaya", "1, 7, 9", "228", "143", "1.60"], ["Balderas", "1, 3", "207", "58", "3.56"],
  ["Zapata", "3, 12", "180", "61", "2.96"], ["Centro Médico", "3, 9", "177", "56", "3.17"],
  ["Guerrero", "3, B", "163", "28", "5.79"], ["Tacuba", "2, 7", "158", "72", "2.20"],
], { x: 0.6, y: 1.85, w: 5.0, colW: [1.5, 1.0, 0.85, 0.95, 0.7], rowH: 0.24, fontSize: 10.5, margin: [1, 5, 1, 5] });
y = bloque(s, 6.0, 1.88, 3.4, "Por tasa también",
  "9 de las 10 primeras por tasa son correspondencias; por azar se esperaban 1.7.", 0.62, 12);
y = bloque(s, 6.0, y + 0.08, 3.4, "Cuánto transbordo haría falta",
  "Para bajar a 0.71 harían falta 3,583 millones de transbordos en seis años, 1.98 veces sus entradas: un flujo verosímil.", 0.85, 12);
bloque(s, 6.0, y + 0.08, 3.4, "Lo que no alcanza a explicar",
  "Hidalgo y Guerrero necesitarían 8.0 y 7.2 veces sus entradas.", 0.45, 12);
txt(s, "Tasa: denuncias por millón de entradas. Entradas en millones, 2019–2024.", { x: 0.6, y: 4.72, w: 5.0, h: 0.22, fontSize: 10, color: GRIS });

anexo("Una agencia del Ministerio Público en la estación no explica el exceso", "La agencia del Ministerio Público",
  "Si preguntan si la tasa mide dónde se puede denunciar, era la sospecha natural, y se probó por cuatro vías con los datos de la FGJ, que traen la agencia que abrió cada carpeta. Las cuatro dicen que no.");
s = diapositivas[diapositivas.length - 1].slide;
bajada(s, "Hidalgo tiene una agencia dentro y 6.38 denuncias por millón, 2.7 veces la mediana de correspondencias comparables; Guerrero, 5.79 y 3.0 veces.");
const via = (yy, n, t) => {
  txt(s, String(n), { x: 0.6, y: yy - 0.04, w: 0.4, h: 0.45, fontSize: 24, bold: true, color: NARANJA });
  txt(s, t, { x: 1.1, y: yy, w: 8.3, h: 0.65, fontSize: 13 });
};
via(1.95, 1, "Las carpetas que abre la agencia de Hidalgo caen en 97 estaciones; solo el 13.8 % es de Hidalgo.");
via(2.6, 2, "Observatorio, la única estación de paso con agencia, está en el percentil 15 mientras tuvo agencia, y su tasa no cambia al cerrarla (0.34 y 0.35).");
via(3.25, 3, "El exceso de Hidalgo y Guerrero sigue en la Denuncia Digital, por internet, donde no hace falta ir a ninguna agencia: 3.5 veces.");
via(3.9, 4, "El exceso sube de 2.6 a 4.7 veces entre 2019 y 2024, mientras las agencias del metro pasan de abrir el 57 % de las carpetas al 17 %.");
pie(s, "El filtro de agencia se quitó del análisis. El exceso de Hidalgo y Guerrero queda como hallazgo abierto.", 4.8, 0.3);

anexo("En el tiempo hay tres periodos, y el modelo los respeta", "Tres periodos en el tiempo",
  "Si preguntan por la pandemia, con los vagones vacíos la tasa cae a la mitad, así que abril a junio de 2020 sale del modelo, y el orden es el mismo con y sin esos meses. Si preguntan por 2019, el quiebre no tiene explicación en estos datos y el efecto de año lo absorbe.");
s = diapositivas[diapositivas.length - 1].slide;
y = imagen(s, "c3_tasa_vs_afluencia.png", 0.6, 1.35, 3.6,
  "Serie mensual de denuncias por millón de entradas y de entradas en la red, 2019 a 2024.");
y = bloque(s, 4.6, 1.4, 4.8, "El quiebre de 2019",
  "Las denuncias de la red caen de unas 330 al mes (enero a mayo de 2019) a unas 135 desde septiembre, con la afluencia plana. No tiene explicación en estos datos.", 0.85, 12);
y = bloque(s, 4.6, y + 0.08, 4.8, "El confinamiento",
  "De abril a junio de 2020 la tasa cae a 0.55 veces la base: con vagones vacíos, las denuncias no crecen en proporción a las entradas. Esos meses salen del modelo, y con y sin ellos el orden es el mismo (ρ = 0.9985).", 1.05, 12);
bloque(s, 4.6, y + 0.08, 4.8, "Tasa de las 124 en cada periodo",
  "1.24 de enero a agosto de 2019, 0.35 en el confinamiento y 0.61 el resto del tiempo.", 0.45, 12);

anexo("Fuera de muestra, completo: 10 y 20 estaciones, con su techo", "Fuera de muestra, completo",
  "Si preguntan qué tan buena es la regla por conteo, es casi tan buena como el oráculo para cubrir volumen (92 contra 100). Por eso no se recomienda cambiarla cuando el objetivo es volumen.");
s = diapositivas[diapositivas.length - 1].slide;
bajada(s, "Estaciones elegidas con 2019–2023 y lo que cubrieron en 2024. Ese año hubo 341 denuncias y 747 millones de entradas en el conjunto.");
tabla(s, [
  ["Estaciones", "Lista", "Denuncias de 2024", "% de las 341", "Por millón de entradas", "Entradas (M)"],
  ["10", "conteo", "92", "27.0", "0.57", "160"], ["10", "tasa encogida", "41", "12.0", "0.77", "53"],
  ["10", "prioridad", "59", "17.3", "0.75", "79"], ["10", "oráculo", "100", "29.3", "0.70", "143"],
  ["20", "conteo", "135", "39.6", "0.58", "233"], ["20", "tasa encogida", "73", "21.4", "0.61", "120"],
  ["20", "prioridad", "99", "29.0", "0.68", "146"], ["20", "oráculo", "163", "47.8", "0.72", "227"],
], { x: 0.6, y: 1.9, w: 8.8, colW: [1.1, 1.7, 1.55, 1.3, 1.75, 1.4], rowH: 0.28, fontSize: 11.5 });
pie(s, "Oráculo: la lista que se armaría con el conteo real de 2024; es el techo. Con 10 estaciones, la tasa encogida también supera a la tasa cruda (28 denuncias y 0.69).", 4.8, 0.38);

anexo("Cómo se eligió la regla de prioridad", "Cómo se eligió la regla de prioridad",
  "Si preguntan si la regla se eligió después de ver los resultados, en parte sí, y se dice. El criterio principal se escribió antes y no lo cumplió ninguna regla; se aplicó la regla de reserva, y la exigencia de ganar en los cuatro casos se fijó después de ver la tabla.");
s = diapositivas[diapositivas.length - 1].slide;
via(1.5, 1, "Se probaron 13 reglas fuera de muestra en dos años: 2023, con ajuste 2019–2022, y 2024, con ajuste 2019–2023; con 10 y con 20 estaciones.");
via(2.2, 2, "Criterio escrito antes de ver la tabla: cubrir al menos el 60 % de lo que cubre el conteo con la mayor tasa, con 10 y 20 estaciones y en los dos años. No lo cumplió ninguna: la mejor regla cambia de año y de tamaño.");
via(3.05, 3, "Regla de reserva: la más simple de decir entre las que superan al conteo en denuncias por millón y a la tasa en denuncias cubiertas en los cuatro casos. Esta exigencia se fijó después de ver la tabla.");
via(3.9, 4, "Con remuestreo de estaciones (bootstrap), su ventaja sobre el conteo es positiva en el 99.4 % de las remuestras en 2024 con 20 estaciones, y en el 78 % en 2023.");

anexo("Predecir el año siguiente tiene un techo bajo, y más información no lo sube", "Predecir el año siguiente",
  "Si preguntan si se podría predecir mejor, se probó con un protocolo escrito antes, siete modelos y tres años de prueba. Ninguno cumplió el criterio de mejora. Lo que cambia de un año al siguiente es ruido de conteos pequeños.");
s = diapositivas[diapositivas.length - 1].slide;
bloque(s, 0.6, 1.4, 3.6, "Con el modelo base",
  "ρ entre la tasa predicha con 2019–2023 y la observada en 2024: 0.303 (bootstrap: 0.117 a 0.464), contra 0.261 de la tasa cruda y 0.289 del conteo. Si la tasa predicha fuera la verdadera, el puro ruido de un año daría 0.376.", 1.55, 12);
tabla(s, [
  ["Métrica", "Base", "Mejor nuevo", "Cuál"],
  ["ρ predicha contra observada, 2024", "0.303", "0.324", "entorno"],
  ["10 primeras por tasa, 2024, por millón", "0.773", "0.799", "línea"],
  ["20 primeras por tasa, 2024, por millón", "0.610", "0.658", "entorno"],
  ["10 primeras por tasa, 2022, por millón", "1.220", "1.150", "entorno"],
  ["Modelos que ganan en 4 o más de 6 casos", "—", "ninguno", "—"],
  ["σv en el ajuste completo", "0.402", "0.282", "todas"],
], { x: 4.6, y: 1.4, w: 4.8, colW: [2.55, 0.6, 0.85, 0.8], fontSize: 10, rowH: 0.27 });
pie(s, "Covariables: línea; carpetas de cualquier delito y de robo a transeúnte a 500 m (entorno); tamaño; tendencia propia de cada estación. Explican el 51 % de la varianza entre estaciones, pero no mejoran la lista del año siguiente. La tendencia empeora: 0.56 contra 0.77 en 2024, con 10 estaciones.", 4.6, 0.6);

anexo("Lo que falta en los datos, y hacia dónde sesga", "Lo que falta en los datos",
  "Si preguntan por qué no imputé las carpetas sin coordenadas, es porque repartirlas supondría que faltan al azar entre estaciones, y eso es justo lo que no se sabe. El sesgo es a la baja en los años recientes, y se declara.");
s = diapositivas[diapositivas.length - 1].slide;
via(1.45, 1, "1,041 carpetas sin coordenadas, que no se imputan. No faltan al azar: van de 47 en 2019 a 455 en 2023, y 715 son de la Denuncia Digital. Los años recientes salen bajos.");
via(2.2, 2, "559 carpetas con coordenadas caen a más de 150 m de cualquier estación. Con 100 y 250 m, el orden por tasa se parece al de 150 m con ρ de 0.99 o más.");
via(2.95, 3, "Control externo: Expansión pidió por transparencia las carpetas de enero a septiembre de 2024 y publicó 902. En los datos abiertos, por fecha del hecho, son 896.");
via(3.7, 4, "El archivo de afluencia trae 395 grafías para 195 puntos estación-línea. Se cruzaron tras normalizar los nombres, con tres casos resueltos a mano.");
pie(s, "Lo ocurrido a fines de 2024 y denunciado después del 31 de enero de 2025 no está en el archivo.", 4.75, 0.3);

anexo("Los supuestos que sostienen el resultado", "Los supuestos",
  "Si preguntan por un supuesto en particular, la tabla de supuestos completa, con cómo se verificó cada uno, está en el escrito.");
s = diapositivas[diapositivas.length - 1].slide;
tabla(s, [
  ["Supuesto", "Por qué vale aquí", "Qué cuesta o cómo se verificó"],
  ["Se miden denuncias, no robos", "Es lo que existe en la fuente", "Cifra negra de 93 %; no se sabe si varía entre estaciones"],
  ["La exposición son las entradas", "En una estación de paso todos cruzan el torniquete", "Falla en las 28 correspondencias: se acota"],
  ["Se cuenta por fecha del hecho", "La pregunta es dónde y cuándo ocurrió", "Lo denunciado después del corte no está"],
  ["Un mes con cero entradas es una estación cerrada", "Coincide con cierres de las líneas 12 y 1 y con la pandemia", "Esos meses salen; 9 denuncias quedan sin denominador"],
  ["El efecto de estación es constante en seis años", "Se recomienda un orden para el año siguiente", "Una tendencia por estación empeoró la predicción"],
  ["Intervalos de Bayes empírico", "Toman como fijos los parámetros de la red", "Son algo estrechos: se leen con cuidado cuando rozan 1"],
], { x: 0.6, y: 1.4, w: 8.8, colW: [2.7, 3.0, 3.1], fontSize: 10.5, valign: "top" });

anexo("Qué cambiaría la recomendación, y qué sigue", "Qué cambiaría la recomendación",
  "Si preguntan qué haría con más tiempo, reconstruiría los transbordos con la Encuesta Origen-Destino y pediría la afluencia por hora.");
s = diapositivas[diapositivas.length - 1].slide;
y = bloque(s, 0.6, 1.4, 4.2, "Si cambian estos supuestos",
  "Si el subregistro variara mucho entre estaciones, el orden por tasa mediría dónde se denuncia y no dónde se roba. Con una matriz de transbordos, las 28 correspondencias entrarían al orden. Si las carpetas sin coordenadas faltaran más en unas estaciones que en otras, el efecto de año no bastaría.", 2.0, 12);
bloque(s, 5.2, 1.4, 4.2, "Trabajo futuro",
  "Reconstruir la exposición de las correspondencias con la Encuesta Origen-Destino 2017 del INEGI. Pedir al Metro la afluencia por hora. Explicar el exceso de Hidalgo y Guerrero y el quiebre de 2019. Cruzar una medida de victimización por estación cuando exista.", 2.0, 12);
regla(s, 0.6, 3.95, 8.8);
txt(s, [fuerte("La franja de la mañana: "), { text: "cuatro de cada diez denuncias de las 124 declaran un hecho de las 6:00 a las 9:59. Eso dice cuándo se denuncia más, no cuándo es más riesgoso por pasajero, porque el Metro no publica afluencia por hora. Con esa advertencia, sirve para la franja del despliegue." }],
    { x: 0.6, y: 4.08, w: 8.8, h: 0.75, fontSize: 12 });

anexo("La aplicación", "La aplicación (captura)",
  "Si la demostración en vivo falla, esta captura muestra la pestaña Dónde desplegar. La aplicación también funciona sin conexión.");
s = diapositivas[diapositivas.length - 1].slide;
y = imagen(s, "app_captura_listas.png", 0.6, 1.35, 5.0,
  "Captura de la aplicación, pestaña Dónde desplegar, con las tres listas y lo que cubrió cada una en 2024.");
txt(s, "Pestaña Dónde desplegar: listas elegidas con 2019–2023 y lo que cubrieron en 2024. Captura del 24 de octubre de 2026.",
    { x: 0.6, y: y + 0.05, w: 5.0, h: 0.4, fontSize: 9.5, color: GRIS });
txt(s, [
  { text: "Página estática: HTML, CSS y JavaScript propios y un archivo de datos de 170 KB. Sin servidor; funciona sin conexión.", options: { breakLine: true } },
  { text: "Tres botones: conteo, tasa y prioridad. Abre en prioridad.", options: { breakLine: true } },
  { text: "Las correspondencias se dibujan chicas y con trama, para no sugerir que son comparables.", options: { breakLine: true } },
  { text: "Los estatus (por arriba, por abajo, no distinguible) se distinguen por forma, no solo por color.", options: { breakLine: true } },
  { text: "Las estaciones con menos de 15 denuncias se dibujan huecas.", options: { breakLine: true } },
  { text: "Los números escritos en la página se comprueban contra el modelo cada vez que se regenera." },
], { x: 6.3, y: 1.4, w: 3.1, h: 3.7, fontSize: 11, paraSpaceAfter: 6 });
pie(s, APP, 5.0, 0.22);

anexo("Cómo se reproduce todo, y cómo usé IA generativa", "Reproducir todo, y el uso de IA",
  "Si preguntan qué hizo la IA y qué hice yo, la herramienta escribió el código y redactó los documentos de cada fase; las decisiones de encuadre, supuestos y qué se afirma son mías, y cada cifra se recalculó sobre los archivos del repositorio. Todo está documentado en el repositorio.");
s = diapositivas[diapositivas.length - 1].slide;
y = bloque(s, 0.6, 1.4, 4.2, "Cuatro comandos",
  [{ text: "python src/descarga.py --fuente estaciones", options: { bold: true, breakLine: true } },
   { text: "python src/metro/correr.py", options: { bold: true, breakLine: true } },
   { text: "bash docs/escrito/compila.sh", options: { bold: true, breakLine: true } },
   { text: "node src/presentacion/genera.js", options: { bold: true, breakLine: true } },
   { text: "Bajan los tres archivos y anotan su hash, corren el pipeline con sus comprobaciones, compilan el escrito y arman esta presentación." }], 2.2, 11.5);
bloque(s, 5.2, 1.4, 4.2, "Uso de IA generativa",
  "Trabajé con Claude Code (Anthropic). Escribió el código del pipeline, del modelo y de la aplicación, propuso criterios de rechazo que quedaron escritos antes de correr y redactó los documentos de cada fase. Las decisiones son mías: el encuadre, los supuestos, qué se afirma y qué se descarta. Cada cifra se recalculó sobre los archivos del repositorio.", 2.2, 11.5);
pie(s, `Repositorio: ${REPO}. El uso de IA, por tipo, está en docs/uso-ia.md.`, 4.75, 0.4);

/* el índice del anexo, ya con los números */
titulo(indice, "Anexo", 26);
ruta(indice, "anexo");
bajada(indice, "No se presenta. Sirve para responder preguntas: cada línea dice en qué diapositiva está la respuesta.");
const entradas = diapositivas.slice(PRINCIPALES + 1).map((d, i) => [PRINCIPALES + 2 + i, d.corto]);
const mitad = Math.ceil(entradas.length / 2);
[entradas.slice(0, mitad), entradas.slice(mitad)].forEach((grupo, k) => {
  grupo.forEach(([n, t], i) => {
    txt(indice, [{ text: `${n}  `, options: { bold: true, color: NARANJA_TEXTO } }, { text: t }],
        { x: 0.6 + k * 4.5, y: 1.95 + i * 0.36, w: 4.3, h: 0.3, fontSize: 12 });
  });
});

/* ============================================================ tiempos y notas */
const palabras = (t) => (t.match(/[0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ.,%]+/g) || []).filter((w) => /[0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ]/.test(w)).length;
const mmss = (seg) => `${Math.floor(seg / 60)}:${String(seg % 60).padStart(2, "0")}`;
let reloj = 0;
const filas = [];
diapositivas.forEach((d, i) => {
  const n = i + 1;
  if (!d.anexo) {
    const p = palabras(d.dice);
    const seg = Math.ceil((p / PALABRAS_POR_MINUTO * 60 + d.extra) / 5) * 5;
    const cab = `TIEMPO ESTIMADO ${mmss(seg)} · de ${mmss(reloj)} a ${mmss(reloj + seg)} · ${p} palabras${d.extra ? ` más ${d.extra} s de demostración` : ""}`;
    d.slide.addNotes([cab, d.escena || "", d.dice].filter(Boolean).join("\n\n"));
    filas.push([n, d.titulo, mmss(reloj), mmss(seg), p]);
    reloj += seg;
  } else {
    d.slide.addNotes(`ANEXO · no se presenta; sirve para responder preguntas.\n\n${d.respuesta}`);
  }
});
if (reloj > TOPE_SEGUNDOS) throw new Error(`La parte principal dura ${mmss(reloj)}: pasa de diez minutos; mover algo al anexo.`);

const anexoN = diapositivas.length - PRINCIPALES;
const leeme = `# Presentación final

*Generado por \`src/presentacion/genera.js\`; no se edita a mano.*

| Archivo | Qué es |
|---|---|
| [\`presentacion.pdf\`](presentacion.pdf) | Con esto se comparte pantalla |
| [\`presentacion-notas.pdf\`](presentacion-notas.pdf) | Cada diapositiva con su guion debajo, para ensayar |
| [\`presentacion.pptx\`](presentacion.pptx) | La fuente, con el guion en las notas del orador |

**${PRINCIPALES} diapositivas principales y ${anexoN} de anexo.** La parte principal dura unos
**${mmss(reloj)}** a ${PALABRAS_POR_MINUTO} palabras por minuto, con la demostración en vivo
incluida. El anexo no se presenta: sirve para responder preguntas, y su primera diapositiva
es un índice.

La historia va en el orden que pide la rúbrica: el problema, los datos, lo que encontré, qué
recomiendo y los límites. Cada sigla, término y cifra se define en pantalla la primera vez
que aparece.

## El reloj

| # | Diapositiva | Entra | Dura | Palabras del guion |
|---|---|---|---|---|
${filas.map((f) => `| ${f.join(" | ")} |`).join("\n")}

## Rehacerla

\`\`\`bash
npm install pptxgenjs
node src/presentacion/genera.js
python src/presentacion/a_pdf.py docs/presentacion/presentacion.pptx \\
       docs/presentacion/presentacion.pdf --notas docs/presentacion/presentacion-notas.pdf
\`\`\`

\`a_pdf.py\` dibuja el PDF desde el propio \`.pptx\` (necesita \`python-pptx\` y \`reportlab\`)
y avisa si algún texto no cabe en su caja.
`;

fs.mkdirSync(path.dirname(SALIDA), { recursive: true });
pres.writeFile({ fileName: SALIDA }).then(() => {
  fs.writeFileSync(LEEME, leeme);
  console.log(`${SALIDA}: ${PRINCIPALES} principales + ${anexoN} de anexo; parte principal ${mmss(reloj)}`);
  filas.forEach((f) => console.log(`  ${String(f[0]).padStart(2)}  ${f[2]}  ${f[3]}  ${String(f[4]).padStart(3)} pal.  ${f[1]}`));
});
