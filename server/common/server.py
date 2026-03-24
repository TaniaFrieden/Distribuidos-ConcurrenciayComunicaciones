import socket
import logging
import os
import threading

from common.utils import Bet, has_won, store_bets


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._server_socket.settimeout(1)
        self._shutting_down = False
        self._agencias_finalizadas = set()
        self._sorteo_realizado = False
        total_agencias = os.getenv("TOTAL_AGENCIES")
        if total_agencias is None:
            raise ValueError("TOTAL_AGENCIES no definido")

        self._total_agencias = int(total_agencias)
        self._ganadores_por_agencia = {}

    def shutdown(self):
        with self._estado_lock:
            self._shutting_down = True

        with self._clientes_lock:
            for client_socket in list(self._client_sockets):
                client_socket.close()
                logging.info('action: close_socket | result: success')
            self._client_sockets.clear()

        if self._server_socket is not None:
            self._server_socket.close()
            self._server_socket = None
            logging.info('action: close_socket | result: success')

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        while not self.__esta_apagandose():
            try:
                client_sock = self.__accept_new_connection()
            except OSError as e:
                if self.__esta_apagandose():
                    break

                logging.error(f'action: accept_connections | result: fail | error: {e}')
                continue

            if client_sock is None:
                continue

            thread = threading.Thread(target=self.__handle_client_connection, args=(client_sock,))
            thread.start()
            with self._threads_lock:
                self._threads.append(thread)

        with self._threads_lock:
            threads = list(self._threads)

        for thread in threads:
            thread.join()

        logging.info('action: shutdown | result: success')

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        with self._clientes_lock:
            self._client_sockets.add(client_sock)

        reader = client_sock.makefile('r', encoding='utf-8', newline='\n')

        try:
            encabezado = self.__recv_line(reader)

            if encabezado.startswith('BATCH|'):
                self.__procesar_batch(encabezado, reader, client_sock)
            elif encabezado.startswith('FIN|'):
                self.__procesar_fin(encabezado, client_sock)
            elif encabezado.startswith('WINNERS|'):
                self.__procesar_consulta_ganadores(encabezado, client_sock)
            else:
                raise ValueError('comando invalido')
        except OSError as e:
            if not self.__esta_apagandose():
                client_sock.sendall(b'ERROR\n')
        except (ValueError, KeyError) as e:
            client_sock.sendall(b'ERROR\n')
        finally:
            reader.close()
            client_sock.close()
            with self._clientes_lock:
                self._client_sockets.discard(client_sock)

    def __procesar_batch(self, encabezado, reader, client_sock):
        apuestas = self.__recv_batch(encabezado, reader)
        store_bets(apuestas)
        self.__registrar_ganadores(apuestas)
        for apuesta in apuestas:
            logging.info(
                f'action: apuesta_almacenada | result: success | dni: {apuesta.document} | numero: {apuesta.number}'
            )
        logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(apuestas)}')
        client_sock.sendall(b'OK\n')

    def __procesar_fin(self, encabezado, client_sock):
        _, agencia = encabezado.split('|', 1)
        sorteo_recien_realizado = False

        with self._estado_lock:
            self._agencias_finalizadas.add(agencia)

            if not self._sorteo_realizado and len(self._agencias_finalizadas) >= self._total_agencias:
                self._sorteo_realizado = True
                sorteo_recien_realizado = True

        if sorteo_recien_realizado:
            logging.info('action: sorteo | result: success')

        client_sock.sendall(b'OK\n')

    def __procesar_consulta_ganadores(self, encabezado, client_sock):
        _, agencia = encabezado.split('|', 1)

        with self._estado_lock:
            sorteo_realizado = self._sorteo_realizado

        if not sorteo_realizado:
            client_sock.sendall(b'PENDING\n')
            return

        ganadores = self._ganadores_por_agencia.get(agencia, [])

        respuesta = "WINNERS|{}".format(len(ganadores))
        client_sock.sendall((respuesta + "\n").encode('utf-8'))

    def __registrar_ganadores(self, apuestas):
        for apuesta in apuestas:
            if not has_won(apuesta):
                continue

            agencia = str(apuesta.agency)
            if agencia not in self._ganadores_por_agencia:
                self._ganadores_por_agencia[agencia] = []

            self._ganadores_por_agencia[agencia].append(apuesta.document)

    def __recv_batch(self, encabezado, reader):
        tipo, cantidad = encabezado.split('|', 1)
        if tipo != 'BATCH':
            raise ValueError('encabezado de batch invalido')

        cantidad_apuestas = int(cantidad)
        if cantidad_apuestas <= 0:
            raise ValueError('cantidad de apuestas invalida')

        apuestas = []
        for _ in range(cantidad_apuestas):
            apuestas.append(self.__parse_bet_line(self.__recv_line(reader)))

        return apuestas

    def __parse_bet_line(self, linea):
        campos = linea.split('|')
        if len(campos) != 6:
            raise ValueError('cantidad de campos invalida')

        return Bet(
            campos[0],
            campos[1],
            campos[2],
            campos[3],
            campos[4],
            campos[5],
        )

    def __recv_line(self, reader):
        linea = reader.readline()
        if linea == '':
            raise OSError('connection closed before end of message')

        return linea.rstrip('\n')

    def __esta_apagandose(self):
        with self._estado_lock:
            return self._shutting_down

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        try:
            c, addr = self._server_socket.accept()
        except socket.timeout:
            return None
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
