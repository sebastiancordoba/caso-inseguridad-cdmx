# El problema, acotado

*Versión vigente desde el 2026-09-14. Sustituye a las secciones 1 a 3 de
`entrega-2026-09-14.md` (archivo de trabajo, no publicado), que quedan como registro de lo que se
llevó a la reunión. Por qué cambió: los sinodales pidieron acotar la pregunta a ciertos
delitos, y la rúbrica pide una pregunta «acotada y factible» (§1.1). Todo lo que aquí se
afirma sobre los datos se verificó el 2026-09-14; el detalle está en
[`../datos/FUENTES.md`](../datos/FUENTES.md).*

## La pregunta

> **¿La inseguridad que sienten los habitantes de cada alcaldía en las calles que usan
> sigue al robo a transeúnte que se denuncia en esa alcaldía?** Ciudad de México, del
> tercer trimestre de 2019 al cuarto de 2024.

Un delito, un lugar, una unidad. El lugar de la pregunta y el lugar del delito son el
mismo: la calle.

## Por qué importa, y a quién

**La afirmación que se pone a prueba.** El Gobierno de la Ciudad lee las dos cifras juntas
y saca de ellas una causa: su comunicado del 18 de octubre de 2022 dice que la baja en la
percepción de inseguridad «es producto de la reducción de los delitos de alto impacto», con
cifras de toda la ciudad. El robo a transeúnte en vía pública es una de esas categorías de
alto impacto en la clasificación de la FGJ, y es la más frecuente: **55,429 carpetas** en
la ventana, más que el robo de vehículo (44,449).

**Qué decisión cambia la respuesta.**
- Si la percepción en la calle sigue al robo denunciado en la calle, bajar ese robo es una
  palanca directa sobre el miedo, y la autoridad puede medir su efecto con la ENSU.
- Si no lo sigue, el miedo responde a otra cosa, o el robo en la calle ocurre y no se
  denuncia. La brecha por alcaldía dice dónde pasa cada cosa, y cada una pide una respuesta
  distinta: patrullaje e iluminación en un caso, facilitar la denuncia en el otro.

**Quién la usa:** la Secretaría de Seguridad Ciudadana y las alcaldías, que reportan su
desempeño con las dos cifras; y la ciudadanía y la sociedad civil, que leen esos reportes.

## Qué se mide, exactamente

| Pieza | Definición operativa | Fuente |
|---|---|---|
| Percepción | Porcentaje que responde «Inseguro(a)» a la pregunta 1.2 de la ENSU, *«En términos de delincuencia, dígame si en (LUGAR) se siente seguro(a) o inseguro(a)»*, con LUGAR = «las calles que habitualmente usa» (variable `BP1_2_03`). Ponderado con `FAC_SEL`; error estándar con el diseño muestral (`UPM_DIS`, `EST_DIS`) | Microdatos trimestrales de la ENSU, tabla del cuestionario básico |
| Delito | Carpetas con delito «ROBO A TRANSEUNTE EN VIA PUBLICA CON VIOLENCIA» (44,958) o «… SIN VIOLENCIA» (10,458), contadas por fecha del hecho y por `alcaldia_hecho`, en tasa por 100 mil habitantes | Carpetas de la FGJ; población del Censo 2020 |
| Unidad | Alcaldía por trimestre: 16 × 21 = **336 observaciones** (2019-T3 a 2024-T4, sin 2020-T2, que la pandemia impidió levantar) | La ENSU trata a cada alcaldía como «ciudad de interés» (Iztapalapa = 76, Milpa Alta = 78…) |

**Volumen por alcaldía y trimestre:** de unas 13 carpetas en Milpa Alta a unas 435 en
Iztapalapa. Alcanza en las dieciséis. Solo el 1.3 % de estas carpetas no trae alcaldía.

## Supuestos que se declaran

*La rúbrica pide la razón por la que cada decisión es válida aquí, no la descripción de lo
que se hizo (§2.1).*

1. **Cada alcaldía se compara consigo misma** (efectos fijos de alcaldía) porque lo que
   distorsiona la comparación entre alcaldías casi no cambia en cinco años: la población
   residente, la gente de paso que infla los robos de Cuauhtémoc o Benito Juárez sin vivir
   ahí, la costumbre de denunciar.
2. **Lo que le pasa a toda la ciudad a la vez se descuenta** (efectos fijos de trimestre):
   la pandemia de 2020, campañas del gobierno central. El supuesto es que pegó parejo en
   las dieciséis alcaldías.
3. **La encuesta tiene margen de error**: unas 300 viviendas por alcaldía y trimestre. Se
   usa el error estándar del diseño, no la cifra puntual como si fuera exacta.
4. **Quien responde «No aplica» o «No sabe» queda fuera del denominador.** La pregunta es
   por quien sí usa las calles de su alcaldía.
5. **Se cuenta por fecha del hecho, no de la denuncia**, porque la pregunta es por lo que
   pasó en el trimestre. Costo declarado: lo ocurrido a fines de 2024 y denunciado después
   de enero de 2025 no está en los datos, y el último trimestre sale subcontado.
6. **La FGJ corrige sus registros después de publicarlos** (nota técnica del 29 de julio de
   2020: el delito y el lugar pueden cambiar a diario, cada semana y cada mes). Se trabaja
   sobre una descarga fija, identificada por su hash en `datos/crudos/MANIFIESTO.md`.
7. **Se usa `alcaldia_hecho`, no `alcaldia_catalogo`**: la segunda está vacía en cerca del
   99 % de los registros de todos los años.
8. **Asociación, no causa.** Los sinodales confirmaron el 14 de septiembre que no esperan
   causalidad. El diseño dice si percepción y robo se mueven juntos dentro de cada
   alcaldía, no que uno cause al otro.

## Hipótesis

**H1 — La percepción en la calle sigue al robo en la calle.** Dentro de cada alcaldía, en
los trimestres con más robo a transeúnte denunciado por cada 100 mil habitantes, una
proporción mayor de la gente se siente insegura en las calles que usa.
- *Se contrasta con:* el panel, con efectos fijos de alcaldía y de trimestre.
- *Se descarta si:* la asociación dentro de alcaldía es nula o negativa.

**H2 — Pesa más el robo con violencia.** La percepción en la calle se asocia más con el
robo a transeúnte con violencia que con el robo sin violencia.
- *Se contrasta con:* el mismo modelo con las dos series por separado.
- *Se descarta si:* las dos pesan igual, o pesa más el robo sin violencia.

*Punto de comparación, no hipótesis:* el mismo modelo con el resto de las carpetas, para
ver si la percepción en la calle responde a su delito o a cualquier delito.

## Objetivos

**General.** Medir si la inseguridad que se siente en las calles de cada alcaldía acompaña
al robo a transeúnte que ahí se denuncia, y señalar dónde se separan, para que la
autoridad y la ciudadanía sepan qué lee de verdad esa percepción.

1. **Construir el panel** alcaldía-trimestre con la percepción en las calles (y su error
   estándar) y el robo a transeúnte con y sin violencia, documentando cada inconsistencia
   de las fuentes. → *Entrega:* tabla procesada, reproducible desde `src/`, y la sección de
   datos del escrito (D2).
2. **Contrastar H1 y H2**, y verificar los supuestos en lugar de solo declararlos: con un
   trimestre de rezago, sin 2020, sacando una alcaldía a la vez, sin Cuauhtémoc y Benito
   Juárez, y con el error muestral de la ENSU. → *Entrega:* tabla de resultados y de
   robustez (D4).
3. **Medir la brecha por alcaldía**: dónde la gente siente más, o menos, inseguridad en la
   calle de la que explican los robos denunciados. → *Entrega:* la base de las
   recomendaciones al tomador de decisiones (D7).
4. **Construir el dashboard** descrito abajo. → *Entrega:* aplicación funcional con
   repositorio público e instrucciones de instalación (D5).

## El dashboard

**Para quién:** alguien de la SSC o de una alcaldía, o un periodista, que quiere saber si en
su alcaldía el miedo en la calle va con los robos, y desde cuándo no.

**Sí se pueden ver percepción y robos en el mismo mapa**, en dos capas que no se confunden:

- **Fondo, los polígonos de las alcaldías:** coloreados por el porcentaje que se siente
  inseguro en sus calles. Es la única escala en la que la ENSU mide.
- **Encima, los robos:** los robos a transeúnte del trimestre elegido, como hexágonos o como
  puntos, a partir de las coordenadas de cada carpeta. Se ve dónde ocurren dentro de cada
  alcaldía.
- **La advertencia, en la leyenda:** la percepción solo existe por alcaldía; que un robo
  caiga en una esquina no dice nada del miedo en esa esquina.

**Controles:**
- deslizador de trimestre (2019-T3 a 2024-T4, con 2020-T2 marcado como faltante);
- robo con violencia, sin violencia o ambos (H2);
- vista alterna del mapa: **la brecha**, en dos colores, «más miedo del que explican los
  robos» contra «menos».

**Al elegir una alcaldía:** sus dos series lado a lado —percepción con su banda de error y
tasa de robo— con la pandemia y la fecha de corte marcadas, y una frase que diga qué se ve.

**Tecnología:** Streamlit, que la rúbrica nombra como forma admisible (§1.2), con el mapa
en pydeck o Plotly y los datos ya procesados en `datos/procesados/`. Mínimo viable, por las
horas: mapa con las dos capas, deslizador y series por alcaldía. La vista de dispersión y
la metodología van en una pestaña aparte si alcanza.

## Qué queda fuera, y por qué

| Fuera | Por qué | Destino |
|---|---|---|
| Robo en transporte público | Menos de 12 carpetas por trimestre en Milpa Alta, Cuajimalpa y Magdalena Contreras; 7 % sin alcaldía; y la ENSU pregunta a residentes mientras el robo se registra donde está la estación | Trabajo futuro |
| Demora entre hecho y denuncia | Era la H2 de la versión del 14; no cabe en las horas | Trabajo futuro |
| Colonia | La ENSU no estima por debajo de alcaldía | — |
| Causalidad | No la esperan los sinodales, y 336 observaciones con la pandemia dentro no la sostienen | — |
| ENVIPE, C5 | No entran al modelo: la ENVIPE da el contexto de la cifra negra; el C5 abierto solo trae incidentes viales | Contexto y limitaciones del escrito |

## Qué ya existe y qué se hace distinto

Resumen de [`revision-literatura.md`](revision-literatura.md):
- **Prieto Curiel y Bishop (2016)** encuentran que el robo a persona es el delito que más se
  asocia con la percepción, pero con encuestas de victimización, en un corte transversal y
  sin la CDMX.
- **Bastién Olvera y Grabinsky (2023)** cruzan la ENSU con las denuncias de la FGJ por
  alcaldía en dos trimestres, sin modelo y con el total de delitos.
- **Innes (2004)** da el marco: los delitos que se ven en el espacio público funcionan como
  señales y pesan más que el resto.

**Lo distinto aquí:** empareja el lugar de la percepción con el lugar del delito —la calle
con la calle—, sigue a cada alcaldía trimestre por trimestre con denuncias oficiales, y
separa el robo con violencia del robo sin violencia.

## Para el escrito

- La rúbrica exige **documentar el uso de IA generativa** (§1.1, fila «Herramientas»).
- Secciones: Contexto, Definición del problema, Supuestos, Resultados y discusión,
  Conclusiones (§1.2). Formato IEEE, 5 a 8 páginas. Entrega: 8 de octubre.
