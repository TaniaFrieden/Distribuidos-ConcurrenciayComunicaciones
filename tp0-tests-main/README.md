# TP0 Tests Automáticos

Test automáticos que ayudan a la depuración del [TP0](https://github.com/7574-sistemas-distribuidos/tp0-base).

### Advertencias

- Antes de cada test se detienen y eliminan todos los contenedores, imágenes y redes del sistema.

- Antes de cada test se resetea la rama actual y se cambia a la rama a verificar, lo que eliminará cambios no incluídos en un commit.

## Instalación

Instalar paquetes requeridos (se recomienda usar pyenv or virtualenv)

```
pip install -r requirements.txt
```

## Ejecución

El repositorio cuenta con un **Makefile** que incluye distintos comandos en forma de targets. Los targets se ejecutan mediante la invocación de: `REPO_PATH=path/to/repo make \<target\>` Donde `REPO_PATH` es una variable de entorno , cuyo valor es la ruta absoluta a la raíz de la carpeta de la implementación del TP a validar, no el url remoto de git. 

Los targets disponibles son:

| target | accion |
|--------|--------|
| `deliver`   | Ejecuta los tests sobre REPO_PATH y si todos ellos pasan muestra un texto de entrega de ejemplo. |
| `test`      | Ejecuta los tests  sobre REPO_PATH. Se puede editar el archivo `pytest.ini` para modificar el timeout y los ejercicios a probar. |
| `test-logs` | Permite ver los logs actuales del proyecto. Acompañar con `grep` para lograr ver mensajes de una aplicación específica dentro del compose. |



