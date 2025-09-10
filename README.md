                      _.-- Ficha tecnica del desarrollo --._


En este apartado se explicara brevemente el funcionamiento del programa.

Siga las instruccionees para ejecutar el programa

1- Dentro del repositorio encontraras 2 carpetas con archivos dedicados. dichos archivos disponen de acuerdo al sistema operativo compatible 

2- Es recomendable de momento clonar el repositorio para ejecutar el programa

3-  una vez clonado el repositorio, debes hacer lo siguiente:

  -  Dentro de la carpeta contenedora de acuerdo al   
     sistema operativo de tu eleccion
     (tanto en Windows como Linux funcionan de formas distintas por su configuracion)

     - Abres la carpeta "Ejecutable" y encontraras 2 archivos

     - ValidadorFacturas.exe |Para windows|
     - ValidadorFacturas.build |para Linux|
     - facturas_registro.txt |en ambos sistemas|

4- luego de encontrar los respectivos archivos en la carpeta. Procedes a ejecutar el archivo "ValidadorFacturas"

5- Se abrira una pequeña ventana con 3 parametros donde el usuario puede llenar los datos correspondientes para realizar el proceso de almacenamiento de registros
|resaltando que se usan datos ficticios al no contar con la base de datos real de la DIAN por temas legales|

6- De la mano de las Expresiones regulares basado en Lenguas y Automatas expresamos lo siguiente
 - Tenemos una cadena de caracteres limitadas para registrar el NIT. Sabiendo esto, aplicamos la expresion regular | \d{6,10}-\d | dentro del codigo se tienen en cuenta el limite de caracteres y la denominacion como se trabaja con el NIT, teniendo 9 caracteres numericos limitados a 9, para luego dividir la seccion por "-" y se complemennta con 1 digito faltante para que sea aceptado bajo el codigo y el reglamento sobre el NIT

 - Se usa la expresion regular | YYYY-MM-DD | para asignar las fechas, en este caso se hace exclusivamente en caracteres numericos, para que no hayan incosistencias si se usan caracteres alfa numericos

 - Por ultimo valor, se solicita al usuario que digite el valor, en este caso hablamos de valores numericos enteros en terminos de dinero, donde pueda quedar evidenciado en el sistema los valores asigandos por el usuario.

7- Finalmente el usuario si lo requiere, puede verificar el historial de todos los valores que quedan registardos de forma local en el archivo junto al ejectitable. dicho archivo conocido como |facturas_registro.txt| ira guardando regularmente cada registro que se haga en el ejecutable, organizandolo de forma comoda para la visualizacion posterior.


Dicho prototipo se encuentra en evaluaciones y revisiones diarias para ajustar su funcionamiento de acuerdo a los requerimientos y su optimo funcionamiento