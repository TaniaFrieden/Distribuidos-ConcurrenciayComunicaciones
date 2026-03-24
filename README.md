# TP0: Docker + Comunicaciones + Concurrencia

En el presente repositorio se provee un esqueleto básico de cliente/servidor, en donde todas las dependencias del mismo se encuentran encapsuladas en containers. Los alumnos deberán resolver una guía de ejercicios incrementales, teniendo en cuenta las condiciones de entrega descritas al final de este enunciado.

 El cliente (Golang) y el servidor (Python) fueron desarrollados en diferentes lenguajes simplemente para mostrar cómo dos lenguajes de programación pueden convivir en el mismo proyecto con la ayuda de containers, en este caso utilizando [Docker Compose](https://docs.docker.com/compose/).

## Instrucciones de uso
El repositorio cuenta con un **Makefile** que incluye distintos comandos en forma de targets. Los targets se ejecutan mediante la invocación de:  **make \<target\>**. Los target imprescindibles para iniciar y detener el sistema son **docker-compose-up** y **docker-compose-down**, siendo los restantes targets de utilidad para el proceso de depuración.

Los targets disponibles son:

| target  | accion  |
|---|---|
|  `docker-compose-up`  | Inicializa el ambiente de desarrollo. Construye las imágenes del cliente y el servidor, inicializa los recursos a utilizar (volúmenes, redes, etc) e inicia los propios containers. |
| `docker-compose-down`  | Ejecuta `docker-compose stop` para detener los containers asociados al compose y luego  `docker-compose down` para destruir todos los recursos asociados al proyecto que fueron inicializados. Se recomienda ejecutar este comando al finalizar cada ejecución para evitar que el disco de la máquina host se llene de versiones de desarrollo y recursos sin liberar. |
|  `docker-compose-logs` | Permite ver los logs actuales del proyecto. Acompañar con `grep` para lograr ver mensajes de una aplicación específica dentro del compose. |
| `docker-image`  | Construye las imágenes a ser utilizadas tanto en el servidor como en el cliente. Este target es utilizado por **docker-compose-up**, por lo cual se lo puede utilizar para probar nuevos cambios en las imágenes antes de arrancar el proyecto. |
| `build` | Compila la aplicación cliente para ejecución en el _host_ en lugar de en Docker. De este modo la compilación es mucho más veloz, pero requiere contar con todo el entorno de Golang y Python instalados en la máquina _host_. |

### Servidor

Se trata de un "echo server", en donde los mensajes recibidos por el cliente se responden inmediatamente y sin alterar. 

Se ejecutan en bucle las siguientes etapas:

1. Servidor acepta una nueva conexión.
2. Servidor recibe mensaje del cliente y procede a responder el mismo.
3. Servidor desconecta al cliente.
4. Servidor retorna al paso 1.


### Cliente
 se conecta reiteradas veces al servidor y envía mensajes de la siguiente forma:
 
1. Cliente se conecta al servidor.
2. Cliente genera mensaje incremental.
3. Cliente envía mensaje al servidor y espera mensaje de respuesta.
4. Servidor responde al mensaje.
5. Servidor desconecta al cliente.
6. Cliente verifica si aún debe enviar un mensaje y si es así, vuelve al paso 2.

### Ejemplo

Al ejecutar el comando `make docker-compose-up`  y luego  `make docker-compose-logs`, se observan los siguientes logs:

```
client1  | 2024-08-21 22:11:15 INFO     action: config | result: success | client_id: 1 | server_address: server:12345 | loop_amount: 5 | loop_period: 5s | log_level: DEBUG
client1  | 2024-08-21 22:11:15 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°1
server   | 2024-08-21 22:11:14 DEBUG    action: config | result: success | port: 12345 | listen_backlog: 5 | logging_level: DEBUG
server   | 2024-08-21 22:11:14 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:15 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:15 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°1
server   | 2024-08-21 22:11:15 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:20 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:20 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°2
server   | 2024-08-21 22:11:20 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:20 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°2
server   | 2024-08-21 22:11:25 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:25 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°3
client1  | 2024-08-21 22:11:25 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°3
server   | 2024-08-21 22:11:25 INFO     action: accept_connections | result: in_progress
server   | 2024-08-21 22:11:30 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:30 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°4
server   | 2024-08-21 22:11:30 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:30 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°4
server   | 2024-08-21 22:11:35 INFO     action: accept_connections | result: success | ip: 172.25.125.3
server   | 2024-08-21 22:11:35 INFO     action: receive_message | result: success | ip: 172.25.125.3 | msg: [CLIENT 1] Message N°5
client1  | 2024-08-21 22:11:35 INFO     action: receive_message | result: success | client_id: 1 | msg: [CLIENT 1] Message N°5
server   | 2024-08-21 22:11:35 INFO     action: accept_connections | result: in_progress
client1  | 2024-08-21 22:11:40 INFO     action: loop_finished | result: success | client_id: 1
client1 exited with code 0
```


## Parte 1: Introducción a Docker
En esta primera parte del trabajo práctico se plantean una serie de ejercicios que sirven para introducir las herramientas básicas de Docker que se utilizarán a lo largo de la materia. El entendimiento de las mismas será crucial para el desarrollo de los próximos TPs.

### Ejercicio N°1:
Definir un script de bash `generar-compose.sh` que permita crear una definición de Docker Compose con una cantidad configurable de clientes.  El nombre de los containers deberá seguir el formato propuesto: client1, client2, client3, etc. 

El script deberá ubicarse en la raíz del proyecto y recibirá por parámetro el nombre del archivo de salida y la cantidad de clientes esperados:

`./generar-compose.sh docker-compose-dev.yaml 5`

Considerar que en el contenido del script pueden invocar un subscript de Go o Python:

```
#!/bin/bash
echo "Nombre del archivo de salida: $1"
echo "Cantidad de clientes: $2"
python3 mi-generador.py $1 $2
```

En el archivo de Docker Compose de salida se pueden definir volúmenes, variables de entorno y redes con libertad, pero recordar actualizar este script cuando se modifiquen tales definiciones en los sucesivos ejercicios.

### Ejercicio N°2:
Modificar el cliente y el servidor para lograr que realizar cambios en el archivo de configuración no requiera reconstruír las imágenes de Docker para que los mismos sean efectivos. La configuración a través del archivo correspondiente (`config.ini` y `config.yaml`, dependiendo de la aplicación) debe ser inyectada en el container y persistida por fuera de la imagen (hint: `docker volumes`).


### Ejercicio N°3:
Crear un script de bash `validar-echo-server.sh` que permita verificar el correcto funcionamiento del servidor utilizando el comando `netcat` para interactuar con el mismo. Dado que el servidor es un echo server, se debe enviar un mensaje al servidor y esperar recibir el mismo mensaje enviado.

En caso de que la validación sea exitosa imprimir: `action: test_echo_server | result: success`, de lo contrario imprimir:`action: test_echo_server | result: fail`.

El script deberá ubicarse en la raíz del proyecto. Netcat no debe ser instalado en la máquina _host_ y no se pueden exponer puertos del servidor para realizar la comunicación (hint: `docker network`). `


### Ejercicio N°4:
Modificar servidor y cliente para que ambos sistemas terminen de forma _graceful_ al recibir la signal SIGTERM. Terminar la aplicación de forma _graceful_ implica que todos los _file descriptors_ (entre los que se encuentran archivos, sockets, threads y procesos) deben cerrarse correctamente antes que el thread de la aplicación principal muera. Loguear mensajes en el cierre de cada recurso (hint: Verificar que hace el flag `-t` utilizado en el comando `docker compose down`).

## Parte 2: Repaso de Comunicaciones

Las secciones de repaso del trabajo práctico plantean un caso de uso denominado **Lotería Nacional**. Para la resolución de las mismas deberá utilizarse como base el código fuente provisto en la primera parte, con las modificaciones agregadas en el ejercicio 4.

### Ejercicio N°5:
Modificar la lógica de negocio tanto de los clientes como del servidor para nuestro nuevo caso de uso.

#### Cliente
Emulará a una _agencia de quiniela_ que participa del proyecto. Existen 5 agencias. Deberán recibir como variables de entorno los campos que representan la apuesta de una persona: nombre, apellido, DNI, nacimiento, numero apostado (en adelante 'número'). Ej.: `NOMBRE=Santiago Lionel`, `APELLIDO=Lorca`, `DOCUMENTO=30904465`, `NACIMIENTO=1999-03-17` y `NUMERO=7574` respectivamente.

Los campos deben enviarse al servidor para dejar registro de la apuesta. Al recibir la confirmación del servidor se debe imprimir por log: `action: apuesta_enviada | result: success | dni: ${DNI} | numero: ${NUMERO}`.



#### Servidor
Emulará a la _central de Lotería Nacional_. Deberá recibir los campos de la cada apuesta desde los clientes y almacenar la información mediante la función `store_bet(...)` para control futuro de ganadores. La función `store_bet(...)` es provista por la cátedra y no podrá ser modificada por el alumno.
Al persistir se debe imprimir por log: `action: apuesta_almacenada | result: success | dni: ${DNI} | numero: ${NUMERO}`.

#### Comunicación:
Se deberá implementar un módulo de comunicación entre el cliente y el servidor donde se maneje el envío y la recepción de los paquetes, el cual se espera que contemple:
* Definición de un protocolo para el envío de los mensajes.
* Serialización de los datos.
* Correcta separación de responsabilidades entre modelo de dominio y capa de comunicación.
* Correcto empleo de sockets, incluyendo manejo de errores y evitando los fenómenos conocidos como [_short read y short write_](https://cs61.seas.harvard.edu/site/2018/FileDescriptors/).


### Ejercicio N°6:
Modificar los clientes para que envíen varias apuestas a la vez (modalidad conocida como procesamiento por _chunks_ o _batchs_). 
Los _batchs_ permiten que el cliente registre varias apuestas en una misma consulta, acortando tiempos de transmisión y procesamiento.

La información de cada agencia será simulada por la ingesta de su archivo numerado correspondiente, provisto por la cátedra dentro de `.data/datasets.zip`.
Los archivos deberán ser inyectados en los containers correspondientes y persistido por fuera de la imagen (hint: `docker volumes`), manteniendo la convencion de que el cliente N utilizara el archivo de apuestas `.data/agency-{N}.csv` .

En el servidor, si todas las apuestas del *batch* fueron procesadas correctamente, imprimir por log: `action: apuesta_recibida | result: success | cantidad: ${CANTIDAD_DE_APUESTAS}`. En caso de detectar un error con alguna de las apuestas, debe responder con un código de error a elección e imprimir: `action: apuesta_recibida | result: fail | cantidad: ${CANTIDAD_DE_APUESTAS}`.

La cantidad máxima de apuestas dentro de cada _batch_ debe ser configurable desde config.yaml. Respetar la clave `batch: maxAmount`, pero modificar el valor por defecto de modo tal que los paquetes no excedan los 8kB. 

Por su parte, el servidor deberá responder con éxito solamente si todas las apuestas del _batch_ fueron procesadas correctamente.

### Ejercicio N°7:

Modificar los clientes para que notifiquen al servidor al finalizar con el envío de todas las apuestas y así proceder con el sorteo.
Inmediatamente después de la notificacion, los clientes consultarán la lista de ganadores del sorteo correspondientes a su agencia.
Una vez el cliente obtenga los resultados, deberá imprimir por log: `action: consulta_ganadores | result: success | cant_ganadores: ${CANT}`.

El servidor deberá esperar la notificación de las 5 agencias para considerar que se realizó el sorteo e imprimir por log: `action: sorteo | result: success`.
Luego de este evento, podrá verificar cada apuesta con las funciones `load_bets(...)` y `has_won(...)` y retornar los DNI de los ganadores de la agencia en cuestión. Antes del sorteo no se podrán responder consultas por la lista de ganadores con información parcial.

Las funciones `load_bets(...)` y `has_won(...)` son provistas por la cátedra y no podrán ser modificadas por el alumno.

No es correcto realizar un broadcast de todos los ganadores hacia todas las agencias, se espera que se informen los DNIs ganadores que correspondan a cada una de ellas.

## Parte 3: Repaso de Concurrencia
En este ejercicio es importante considerar los mecanismos de sincronización a utilizar para el correcto funcionamiento de la persistencia.

### Ejercicio N°8:

Modificar el servidor para que permita aceptar conexiones y procesar mensajes en paralelo. En caso de que el alumno implemente el servidor en Python utilizando _multithreading_,  deberán tenerse en cuenta las [limitaciones propias del lenguaje](https://wiki.python.org/moin/GlobalInterpreterLock).

## Condiciones de Entrega
Se espera que los alumnos realicen un _fork_ del presente repositorio para el desarrollo de los ejercicios y que aprovechen el esqueleto provisto tanto (o tan poco) como consideren necesario.

Cada ejercicio deberá resolverse en una rama independiente con nombres siguiendo el formato `ej${Nro de ejercicio}`. Se permite agregar commits en cualquier órden, así como crear una rama a partir de otra, pero al momento de la entrega deberán existir 8 ramas llamadas: ej1, ej2, ..., ej7, ej8.
 (hint: verificar listado de ramas y últimos commits con `git ls-remote`)

Se espera que se redacte una sección del README en donde se indique cómo ejecutar cada ejercicio y se detallen los aspectos más importantes de la solución provista, como ser el protocolo de comunicación implementado (Parte 2) y los mecanismos de sincronización utilizados (Parte 3).

Se proveen [pruebas automáticas](https://github.com/7574-sistemas-distribuidos/tp0-tests) de caja negra. Se exige que la resolución de los ejercicios pase tales pruebas, o en su defecto que las discrepancias sean justificadas y discutidas con los docentes antes del día de la entrega. 

El incumplimiento de las pruebas es condición de desaprobación, pero su cumplimiento no es suficiente para la aprobación.  Se pide a los alumnos leer atentamente y **tener en cuenta** los criterios de corrección informados  [en el campus](https://campusgrado.fi.uba.ar/mod/page/view.php?id=73393).
Respetar el formato y contenido las entradas de logs descritas en los ejercicios, pues son las que se chequean en cada uno de los tests.

## Seccion de Entrega

Esta seccion resume como ejecutar cada ejercicio y los aspectos principales de la solucion implementada.

### Requisitos

- Docker y Docker Compose instalados
- `make`
- permisos de ejecucion para los scripts:

```bash
chmod +x generar-compose.sh
chmod +x validar-echo-server.sh
```

### Flujo comun de ejecucion

Para la mayoria de los ejercicios el flujo base es:

```bash
./generar-compose.sh docker-compose-dev.yaml <cantidad_clientes>
make docker-compose-up
make docker-compose-logs
make docker-compose-down
```

### Como ejecutar cada ejercicio

#### Ejercicio 1

Pararse en la rama `ej1` y generar el compose con la cantidad de clientes deseada:

```bash
git switch ej1
./generar-compose.sh docker-compose-dev.yaml 5
make docker-compose-up
make docker-compose-logs
make docker-compose-down
```

#### Ejercicio 2

Pararse en `ej2`, levantar el entorno y modificar `client/config.yaml` o `server/config.ini`. La configuracion se inyecta por volumen, por lo que no hace falta reconstruir imagen para que el cambio exista dentro del container.

```bash
git switch ej2
./generar-compose.sh docker-compose-dev.yaml 1
make docker-compose-up
make docker-compose-logs
make docker-compose-down
```

#### Ejercicio 3

Pararse en `ej3`, levantar solo el servidor y ejecutar el script de validacion:

```bash
git switch ej3
./generar-compose.sh docker-compose-dev.yaml 0
make docker-compose-up
sh validar-echo-server.sh
make docker-compose-down
```

#### Ejercicio 4

Pararse en `ej4` y ejecutar normalmente el compose. El graceful shutdown se observa cuando se baja el entorno:

```bash
git switch ej4
./generar-compose.sh docker-compose-dev.yaml 1
make docker-compose-up
make docker-compose-down
```

#### Ejercicio 5

Pararse en `ej5` y levantar un cliente para observar el envio de una apuesta y su almacenamiento:

```bash
git switch ej5
./generar-compose.sh docker-compose-dev.yaml 1
make docker-compose-up
make docker-compose-logs
make docker-compose-down
```

#### Ejercicio 6

Pararse en `ej6`. Cada cliente lee su archivo `.data/agency-N.csv` y envia apuestas en batches:

```bash
git switch ej6
./generar-compose.sh docker-compose-dev.yaml 1
make docker-compose-up
make docker-compose-logs
make docker-compose-down
```

#### Ejercicio 7

Pararse en `ej7`. Despues de enviar los batches, cada cliente notifica fin y consulta sus ganadores:

```bash
git switch ej7
./generar-compose.sh docker-compose-dev.yaml 5
make docker-compose-up
make docker-compose-logs
make docker-compose-down
```

#### Ejercicio 8

Pararse en `ej8`. El servidor procesa conexiones en paralelo y mantiene sincronizado el estado compartido:

```bash
git switch ej8
./generar-compose.sh docker-compose-dev.yaml 5
make docker-compose-up
make docker-compose-logs
make docker-compose-down
```

### Protocolo de comunicacion implementado

La parte de comunicaciones evoluciona a lo largo del TP:

- `ej5`: protocolo textual para una apuesta individual
  `APUESTA|agencia|nombre|apellido|dni|fecha_nacimiento|numero`
- `ej6`: batches con encabezado
  `BATCH|cantidad`
- `ej7` y `ej8`: se agregan comandos de control
  `FIN|id_agencia`
  `WINNERS|id_agencia`

Se eligio un protocolo textual simple, sin JSON ni librerias de serializacion, para mantener separada la capa de comunicacion del modelo de dominio.

### Mecanismos de sincronizacion utilizados

En `ej8`, el servidor se alinea con el modelo de **Estado Mutable Compartido**:

- el hilo principal acepta conexiones
- por cada conexion crea un thread
- los datos compartidos se protegen con locks

Locks utilizados:

- `_estado_lock`: protege shutdown, agencias finalizadas y estado del sorteo
- `_persistencia_lock`: protege persistencia y estructura de ganadores
- `_clientes_lock`: protege sockets activos
- `_threads_lock`: protege la lista de threads

### Resumen de cada ejercicio

#### Ejercicio 1

Se implemento `generar-compose.sh` para generar dinamicamente un `docker-compose` con una cantidad configurable de clientes. Se eligio resolverlo en Bash porque era suficiente para construir el archivo de salida de forma simple, sin sumar dependencias ni complejidad extra. La decision principal fue usar un loop para crear `client1`, `client2`, ..., `clientN`, evitando duplicar manualmente bloques YAML.

#### Ejercicio 2

Se desacoplo la configuracion de las imagenes Docker montando `config.ini` y `config.yaml` como volumenes externos de solo lectura. Se eligio esta solucion porque la configuracion cambia con mas frecuencia que la aplicacion, y conviene que viva fuera de la imagen para poder modificarla sin reconstruir todo el entorno.

#### Ejercicio 3

Se implemento `validar-echo-server.sh`, que usa `netcat` dentro de un contenedor temporal para verificar el echo server sin instalar nada en el host. Se eligio correr `nc` desde un contenedor conectado a la red Docker del proyecto porque asi la validacion se hace en el mismo entorno de red en el que vive el servidor, sin depender de herramientas externas ni abrir puertos hacia afuera.

#### Ejercicio 4

Se agrego graceful shutdown en cliente y servidor, asegurando cierre correcto de sockets y salida ordenada ante `SIGTERM`. Se tomo esta decision porque un cierre abrupto deja recursos abiertos y vuelve inestable el sistema, especialmente cuando despues aparecen mas estado, mas conexiones y mas coordinacion entre procesos.

#### Ejercicio 5

Se cambio la logica al caso de loteria y se implemento un protocolo textual propio para enviar y almacenar apuestas individuales. Se eligio un protocolo manual de texto y no JSON porque era una forma simple de controlar exactamente el formato del mensaje, hacerlo facil de generar desde Go y de parsear desde Python, y mantener separada la capa de comunicacion del modelo de dominio.

#### Ejercicio 6

Se agrego procesamiento por batches, lectura de apuestas desde `.data/agency-N.csv` y envio de batches sin cargar todo el archivo en memoria. Se eligio un encabezado `BATCH|cantidad` porque era simple de generar y de parsear. Tambien se corrigio la lectura del CSV para hacerla en streaming, de modo que en memoria solo exista el batch actual y no toda la agencia completa, lo que hace la solucion mas razonable para archivos de mayor tamaño.

#### Ejercicio 7

Se agregaron las notificaciones de fin y la consulta de ganadores. El servidor espera a todas las agencias antes de habilitar el sorteo y responde solo los ganadores de la agencia consultante. Se eligio este esquema porque el problema necesitaba una forma clara de saber cuando todas las agencias habian terminado antes de avanzar, y porque cada cliente solo necesita la informacion correspondiente a su propia agencia. Ademas, los ganadores se guardan por agencia en memoria para no releer el archivo completo en cada consulta.

#### Ejercicio 8

Se implemento un servidor concurrente con multithreading, un thread por conexion y proteccion de secciones criticas mediante locks sobre estado mutable compartido. Se eligio este enfoque porque era una forma directa de paralelizar la atencion de clientes sin cambiar por completo la estructura previa del servidor. La sincronizacion con locks se uso para proteger el estado compartido del sorteo, la persistencia, los sockets activos y la lista de threads, manteniendo consistencia mientras varios clientes operan al mismo tiempo.
