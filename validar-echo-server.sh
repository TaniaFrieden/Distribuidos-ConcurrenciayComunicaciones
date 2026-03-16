#!/bin/sh

set -eu

readonly NOMBRE_CONTENEDOR_SERVIDOR="server"
readonly NOMBRE_RED="tp0_testing_net"
readonly PUERTO_SERVIDOR="12345"
readonly IMAGEN_NETCAT="busybox:latest"
readonly MENSAJE_PRUEBA="mensaje-prueba-echo"

main() {
    if ! docker network inspect "$NOMBRE_RED" >/dev/null 2>&1; then
        echo "action: test_echo_server | result: fail"
        exit 0
    fi

    if docker run --rm --network "$NOMBRE_RED" "$IMAGEN_NETCAT" sh -c \
        "respuesta=\$(printf '%s' '$MENSAJE_PRUEBA' | nc -w 2 '$NOMBRE_CONTENEDOR_SERVIDOR' '$PUERTO_SERVIDOR' || true); [ \"\$respuesta\" = '$MENSAJE_PRUEBA' ]" \
        >/dev/null 2>&1; then
        echo "action: test_echo_server | result: success"
    else
        echo "action: test_echo_server | result: fail"
    fi
}

main
