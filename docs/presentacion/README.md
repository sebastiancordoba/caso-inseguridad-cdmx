# Presentación final

*Generado por `src/presentacion/genera.js`; no se edita a mano.*

| Archivo | Qué es |
|---|---|
| [`presentacion.pdf`](presentacion.pdf) | Con esto se comparte pantalla |
| [`presentacion-notas.pdf`](presentacion-notas.pdf) | Cada diapositiva con su guion debajo, para ensayar |
| [`presentacion.pptx`](presentacion.pptx) | La fuente, con el guion en las notas del orador |

**13 diapositivas principales y 17 de anexo.** La parte principal dura unos
**9:05** a 140 palabras por minuto, con la demostración en vivo
incluida. El anexo no se presenta: sirve para responder preguntas, y su primera diapositiva
es un índice.

La historia va en el orden que pide la rúbrica: el problema, los datos, lo que encontré, qué
recomiendo y los límites. Cada sigla, término y cifra se define en pantalla la primera vez
que aparece.

## El reloj

| # | Diapositiva | Entra | Dura | Palabras del guion |
|---|---|---|---|---|
| 1 | Portada: la pregunta | 0:00 | 0:30 | 66 |
| 2 | La lista pública de «estaciones peligrosas» solo cuenta denuncias | 0:30 | 0:35 | 80 |
| 3 | Contar denuncias es, en buena parte, contar pasajeros | 1:05 | 0:40 | 88 |
| 4 | Tres archivos abiertos dan las denuncias, las entradas y el lugar | 1:45 | 0:40 | 90 |
| 5 | Donde se cambia de línea, el torniquete no cuenta a todos y la tasa no sirve | 2:25 | 0:45 | 100 |
| 6 | Dividir cambia el orden: de las 10 primeras por conteo, solo 3 siguen arriba por tasa | 3:10 | 0:45 | 103 |
| 7 | Con pocas denuncias la tasa engaña; el modelo la ajusta según la evidencia | 3:55 | 0:45 | 101 |
| 8 | Conteo y tasa sirven a objetivos distintos | 4:40 | 0:45 | 103 |
| 9 | La lista de prioridad junta los dos objetivos | 5:25 | 0:50 | 113 |
| 10 | Para desplegar hoy: tres listas, y cuatro estaciones están en las tres | 6:15 | 1:05 | 98 |
| 11 | Tres recomendaciones | 7:20 | 0:40 | 87 |
| 12 | Todo se mide con denuncias, y la mayoría de los delitos no se denuncia | 8:00 | 0:45 | 100 |
| 13 | Cierre: la respuesta | 8:45 | 0:20 | 40 |

## Rehacerla

```bash
npm install pptxgenjs
node src/presentacion/genera.js
python src/presentacion/a_pdf.py docs/presentacion/presentacion.pptx \
       docs/presentacion/presentacion.pdf --notas docs/presentacion/presentacion-notas.pdf
```

`a_pdf.py` dibuja el PDF desde el propio `.pptx` (necesita `python-pptx` y `reportlab`)
y avisa si algún texto no cabe en su caja.
