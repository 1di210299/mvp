Miguelito recuerda siempre si es que vas a subir nuevos codigos, agregarlo en un commit para github para tenerlo mas monitoreado 

ademas, siempre recuerda que si vas a subir nuevos codigos pero tambien tienes bases de datos pesadas, esas no las subas al github por que no aguanta bases de datos

siempre llena el archivo .gitignore y agrega los tipo de files que no vas a subir como en mi caso el .env, si es que no quieres usar un excel, json o csv puedes

agregar .csv, .json, .xlsx

comandos basicos para github son estos

git init 
git add .  (agrega todos los archivos)
git commit -m "aqui pones una descripcion de lo has actualizado o subido"
git push origin main (sube todos los cambios al repositorio)

si no te deje subir el archivo avergua por que

el git que fuerza subir todo pero no es recomendable es:

git push origin main force


miguelito y pedrito y jorgio
