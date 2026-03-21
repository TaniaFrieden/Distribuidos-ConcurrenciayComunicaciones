#!/bin/bash

set -euo pipefail

readonly NOMBRE_SCRIPT="$(basename "$0")"
readonly IMAGEN_SERVIDOR="server:latest"
readonly IMAGEN_CLIENTE="client:latest"
readonly NOMBRE_RED="testing_net"
readonly SUBRED_RED="172.25.125.0/24"

mostrar_uso() {
    echo "Uso: ./$NOMBRE_SCRIPT <archivo-salida> <cantidad-clientes>" >&2
}

validar_argumentos() {
    if [[ $# -ne 2 ]]; then
        mostrar_uso
        exit 1
    fi

    if ! [[ $2 =~ ^[0-9]+$ ]]; then
        echo "La cantidad de clientes debe ser un entero mayor o igual a 0." >&2
        exit 1
    fi
}

escribir_encabezado() {
    local archivo_salida=$1

    cat <<EOF > "$archivo_salida"
name: tp0
services:
  server:
    container_name: server
    image: $IMAGEN_SERVIDOR
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
    volumes:
      - ./server/config.ini:/config.ini:ro
    networks:
      - $NOMBRE_RED

EOF
}

agregar_servicio_cliente() {
    local archivo_salida=$1
    local id_cliente=$2

    cat <<EOF >> "$archivo_salida"
  client${id_cliente}:
    container_name: client${id_cliente}
    image: $IMAGEN_CLIENTE
    entrypoint: /client
    environment:
      - CLI_ID=${id_cliente}
    volumes:
      - ./client/config.yaml:/config.yaml:ro
      - ./.data:/data:ro
    networks:
      - $NOMBRE_RED
    depends_on:
      - server

EOF
}

agregar_definicion_red() {
    local archivo_salida=$1

    cat <<EOF >> "$archivo_salida"
networks:
  $NOMBRE_RED:
    ipam:
      driver: default
      config:
        - subnet: $SUBRED_RED
EOF
}

main() {
    local archivo_salida=$1
    local cantidad_clientes=$2

    escribir_encabezado "$archivo_salida"

    for ((id_cliente = 1; id_cliente <= cantidad_clientes; id_cliente++)); do
        agregar_servicio_cliente "$archivo_salida" "$id_cliente"
    done

    agregar_definicion_red "$archivo_salida"
}

validar_argumentos "$@"
main "$1" "$2"
