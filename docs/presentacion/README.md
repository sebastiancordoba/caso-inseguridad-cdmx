# Presentación final

*Generado por `src/presentacion/genera.js`; no se edita a mano.*

| Archivo | Qué es |
|---|---|
| [`presentacion.pdf`](presentacion.pdf) | Con esto se comparte pantalla |
| [`presentacion-notas.pdf`](presentacion-notas.pdf) | Cada diapositiva con su guion debajo, para ensayar |
| [`presentacion.pptx`](presentacion.pptx) | La fuente, con el guion en las notas del orador |

**13 diapositivas principales y 17 de anexo.** La parte principal dura unos
**9:25** a 140 palabras por minuto, con la demostración en vivo
incluida. El anexo no se presenta: sirve para responder preguntas, y su primera diapositiva
es un índice.

La historia va en el orden que pide la rúbrica: el problema, los datos, lo que encontré, qué
recomiendo y los límites. Cada sigla, término y cifra se define en pantalla la primera vez
que aparece.

## El reloj

| # | Diapositiva | Entra | Dura | Palabras del guion |
|---|---|---|---|---|
| 1 | Portada: la pregunta | 0:00 | 0:30 | 66 |
| 2 | La lista pública de “estaciones peligrosas” solo cuenta denuncias | 0:30 | 0:35 | 80 |
| 3 | Contar denuncias es, en buena parte, contar pasajeros | 1:05 | 0:40 | 89 |
| 4 | Tres archivos abiertos dan las denuncias, las entradas y el lugar | 1:45 | 0:40 | 91 |
| 5 | Donde se cambia de línea, el torniquete no cuenta a todos y la tasa no sirve | 2:25 | 0:45 | 100 |
| 6 | Dividir cambia el orden: de las 10 primeras por conteo, solo 3 siguen arriba por tasa | 3:10 | 0:50 | 106 |
| 7 | Con pocas denuncias la tasa engaña; el modelo la ajusta según la evidencia | 4:00 | 0:50 | 106 |
| 8 | Conteo y tasa sirven a objetivos distintos | 4:50 | 0:50 | 106 |
| 9 | La lista de prioridad junta los dos objetivos | 5:40 | 0:55 | 121 |
| 10 | Para desplegar hoy: tres listas, y cuatro estaciones están en las tres | 6:35 | 1:05 | 99 |
| 11 | Tres recomendaciones | 7:40 | 0:40 | 88 |
| 12 | Todo se mide con denuncias, y la mayoría de los delitos no se denuncia | 8:20 | 0:45 | 101 |
| 13 | Cierre: la respuesta | 9:05 | 0:20 | 40 |

## Rehacerla

```bash
npm install pptxgenjs
node src/presentacion/genera.js
python src/presentacion/a_pdf.py docs/presentacion/presentacion.pptx \
       docs/presentacion/presentacion.pdf --notas docs/presentacion/presentacion-notas.pdf
```

`a_pdf.py` dibuja el PDF desde el propio `.pptx` (necesita `python-pptx` y `reportlab`)
y avisa si algún texto no cabe en su caja.
