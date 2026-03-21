import socket
import logging
import json

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

        try:
            bet_data = json.loads(self.__recv_line(client_sock))
            bet = Bet(
                bet_data["agency"],
                bet_data["first_name"],
                bet_data["last_name"],
                bet_data["document"],
                bet_data["birthdate"],
                bet_data["number"],
            )
            store_bets([bet])
            logging.info(
                f'action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}'
            )
            client_sock.sendall(b'OK\n')
        except OSError as e:
            if not self._shutting_down:
                logging.error(f'action: apuesta_almacenada | result: fail | error: {e}')
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            logging.error(f'action: apuesta_almacenada | result: fail | error: {e}')
        finally:
            client_sock.close()
            self._client_socket = None

    def __recv_line(self, client_sock):
        chunks = []

        while True:
            data = client_sock.recv(1024)
            if not data:
                raise OSError('connection closed before end of message')

            chunks.append(data)
            if b'\n' in data:
                break

        return b''.join(chunks).split(b'\n', 1)[0].decode('utf-8')

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
