# TP0: Docker + Comunicaciones + Concurrencia

## Datos del alumno

- Nombre: Tania Friedenberger
- Padrón: 108823


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
  `WINNERS|cantidad|dni1|dni2|...`


### Mecanismos de sincronizacion utilizados

En `ej8`, el servidor se alinea con el modelo de Estado Mutable Compartido:

- el hilo principal acepta conexiones
- por cada conexion crea un thread
- los datos compartidos se protegen con locks
- ademas, se agregan timeouts en sockets y un limite de espera en la consulta de ganadores para reducir el riesgo de bloqueos eternos ante fallas de red o clientes incompletos

Locks utilizados:

- `_estado_lock`: protege shutdown, agencias finalizadas y estado del sorteo
- `_persistencia_lock`: protege persistencia y estructura de ganadores
- `_clientes_lock`: protege sockets activos
- `_threads_lock`: protege la lista de threads

### Resumen de cada ejercicio

#### Ejercicio 1

Se implementó `generar-compose.sh` para generar dinámicamente un archivo `docker-compose` con una cantidad configurable de clientes. La solución se resolvió en Bash porque el problema consistía principalmente en construir texto estructurado y no requería incorporar dependencias adicionales ni una herramienta más compleja. El script se organizó en funciones: una parte valida los argumentos de entrada, otra escribe el bloque fijo del compose y otra agrega los servicios cliente. La decisión principal fue usar un loop para construir automáticamente `client1`, `client2`, ..., `clientN`, evitando duplicar manualmente bloques YAML y permitiendo que el mismo script funcione para cualquier cantidad de clientes.

#### Ejercicio 2

Se desacopló la configuración de las imágenes Docker montando `config.ini` y `config.yaml` como volúmenes externos de solo lectura. La implementación consistió en dejar de copiar esos archivos dentro de las imágenes y, en cambio, montarlos desde el host en el `docker-compose` generado. De esta forma, tanto el cliente como el servidor leen su configuración desde archivos externos inyectados al arrancar el container. Se eligió esta solución porque la configuración cambia con más frecuencia que la aplicación y conviene que viva fuera de la imagen para poder modificarla sin reconstruir todo el entorno.

#### Ejercicio 3

Se implementó `validar-echo-server.sh`, que usa `netcat` dentro de un contenedor temporal para verificar el echo server sin instalar nada en el host. La validación se hace levantando un container auxiliar conectado a la misma red Docker del proyecto, desde donde se envía un mensaje al servidor y se comprueba que la respuesta sea la esperada. Según el resultado, el script emite el log `action: test_echo_server | result: success` o `fail`. 

#### Ejercicio 4

Se agregó graceful shutdown en cliente y servidor, asegurando cierre correcto de sockets y salida ordenada ante `SIGTERM`. La implementación consistió en registrar explícitamente la señal en ambos procesos, cerrar los sockets activos cuando llega la orden de apagado y hacer que los loops principales salgan por un camino controlado en lugar de abortar abruptamente. En el cliente se usa un canal interno para propagar el estado de apagado al loop de trabajo, y en el servidor se marca un flag de shutdown y se cierran los sockets para desbloquear llamadas de red pendientes.

#### Ejercicio 5

Se cambió la lógica del sistema al caso de lotería y se implementó un protocolo textual propio para enviar y almacenar apuestas individuales. La solución toma los datos de la apuesta desde variables de entorno en el cliente, construye un mensaje textual con formato `APUESTA|...`, lo envía por socket controlando el caso de short write y espera una confirmación explícita del servidor. Del lado del servidor, la línea recibida se reconstruye hasta el delimitador de fin, se parsea, se valida y se transforma en un objeto del dominio antes de persistirse con `store_bets(...)`.

#### Ejercicio 6

Se incorporó el procesamiento por batches para que cada cliente deje de enviar apuestas individuales y pase a trabajar sobre su archivo .data/agency-N.csv. La solución se diseñó para leer ese archivo en streaming, registro por registro, y acumular apuestas hasta alcanzar el tamaño máximo configurado para el batch. De este modo, el cliente solo mantiene en memoria el conjunto que está procesando en ese momento, en lugar de cargar toda la agencia completa, lo que vuelve la implementación más razonable y escalable frente a archivos de mayor tamaño.

Para el protocolo se definió un encabezado BATCH|cantidad, seguido por una línea por apuesta. Este formato se eligió porque permite que el servidor sepa de antemano cuántas apuestas debe recibir y procesar en esa conexión, manteniendo un parseo simple y ordenado. A partir de ese encabezado, el servidor reconstruye exactamente la cantidad esperada de apuestas, valida cada una, persiste el batch completo y responde éxito solo si todo el conjunto fue recibido y procesado correctamente.

#### Ejercicio 7

Se extendió el protocolo incorporando dos mensajes nuevos: uno para notificar la finalización del envío de apuestas por parte de cada agencia y otro para consultar los resultados del sorteo. Del lado del cliente, la implementación quedó organizada en tres etapas encadenadas: primero se envían todos los batches del archivo, después se notifica `FIN|id_agencia` y recién entonces se comienza a consultar `WINNERS|id_agencia`. Si el sorteo todavía no está habilitado, el servidor responde `PENDING` y el cliente reintenta luego de una espera corta; cuando el sorteo ya fue habilitado, responde con `WINNERS|cantidad|dni1|dni2|...`.

La solución se diseñó como una sincronización por barrera: el servidor no considera realizado el sorteo hasta haber recibido la notificación de todas las agencias esperadas. Recién a partir de ese momento habilita la respuesta a las consultas de ganadores, evitando devolver información parcial. Además, la consulta se resuelve por agencia, de modo que cada cliente recibe únicamente los resultados que le corresponden.

#### Ejercicio 8

Se implementó un servidor concurrente basado en multithreading: el hilo principal permanece dedicado a aceptar nuevas conexiones y, por cada cliente aceptado, crea un worker encargado de procesar esa sesión en paralelo con las demás.

Como el servidor pasa a tener varios threads activos compartiendo memoria dentro del mismo proceso, fue necesario introducir sincronización explícita sobre el estado mutable compartido. Para eso se incorporaron locks con responsabilidades diferenciadas: uno para el estado global del servidor y del sorteo, otro para la persistencia y la estructura de ganadores, otro para el conjunto de sockets activos y otro para la lista de threads lanzados. Esta separación evita usar un lock único demasiado grande y reduce el riesgo de inconsistencias o carreras cuando varios clientes envían apuestas, notifican fin o consultan ganadores al mismo tiempo.

Además, se reforzó el comportamiento de cierre y tolerancia a bloqueos mediante timeouts en el socket de escucha y en los sockets cliente, limpieza de threads finalizados y espera controlada de workers durante el shutdown. Del lado del cliente también se acotó la espera de resultados con un límite de reintentos en la consulta de ganadores.
