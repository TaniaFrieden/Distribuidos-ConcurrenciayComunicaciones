import socket
import logging

from common.utils import Bet, store_bets


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._client_socket = None
        self._shutting_down = False

    def shutdown(self):
        self._shutting_down = True

        if self._client_socket is not None:
            self._client_socket.close()
            self._client_socket = None
            logging.info('action: close_socket | result: success')

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

        while not self._shutting_down:
            try:
                client_sock = self.__accept_new_connection()
            except OSError as e:
                if self._shutting_down:
                    break

                logging.error(f'action: accept_connections | result: fail | error: {e}')
                continue

            self.__handle_client_connection(client_sock)

        logging.info('action: shutdown | result: success')

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        self._client_socket = client_sock
        reader = client_sock.makefile('r', encoding='utf-8', newline='\n')

        try:
            apuestas = self.__recv_batch(reader)
            store_bets(apuestas)
            for apuesta in apuestas:
                logging.info(
                    f'action: apuesta_almacenada | result: success | dni: {apuesta.document} | numero: {apuesta.number}'
                )
            logging.info(f'action: apuesta_recibida | result: success | cantidad: {len(apuestas)}')
            client_sock.sendall(b'OK\n')
        except OSError as e:
            if not self._shutting_down:
                logging.error(f'action: apuesta_recibida | result: fail | cantidad: 0 | error: {e}')
                logging.error(f'action: apuesta_almacenada | result: fail | error: {e}')
                client_sock.sendall(b'ERROR\n')
        except (ValueError, KeyError) as e:
            logging.error(f'action: apuesta_recibida | result: fail | cantidad: 0 | error: {e}')
            logging.error(f'action: apuesta_almacenada | result: fail | error: {e}')
            client_sock.sendall(b'ERROR\n')
        finally:
            reader.close()
            client_sock.close()
            self._client_socket = None

    def __recv_batch(self, reader):
        encabezado = self.__recv_line(reader)
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

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c
