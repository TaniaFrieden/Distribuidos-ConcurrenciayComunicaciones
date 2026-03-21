package common

import (
	"bufio"
	"encoding/csv"
	"fmt"
	"io"
	"net"
	"os"
	"strings"
	"sync"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID             string
	ServerAddress  string
	MaxBatchAmount int
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
	mu     sync.Mutex
}

type apuesta struct {
	Agency    string
	FirstName string
	LastName  string
	Document  string
	Birthdate string
	Number    string
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}

	c.mu.Lock()
	c.conn = conn
	c.mu.Unlock()

	return nil
}

func (c *Client) closeConnection() {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.conn == nil {
		return
	}

	c.conn.Close()
	c.conn = nil
	log.Infof("action: close_socket | result: success | client_id: %v", c.config.ID)
}

func (c *Client) Close() {
	c.closeConnection()
}

func (c *Client) currentConnection() net.Conn {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.conn
}

func (c *Client) estaApagandose(stop <-chan struct{}) bool {
	select {
	case <-stop:
		return true
	default:
		return false
	}
}

func (c *Client) rutaArchivoAgencia() string {
	return fmt.Sprintf("/data/agency-%s.csv", c.config.ID)
}

func (c *Client) cargarApuestas() ([]apuesta, error) {
	archivo, err := os.Open(c.rutaArchivoAgencia())
	if err != nil {
		return nil, err
	}
	defer archivo.Close()

	lector := csv.NewReader(archivo)
	registros, err := lector.ReadAll()
	if err != nil {
		return nil, err
	}

	apuestas := make([]apuesta, 0, len(registros))
	for _, registro := range registros {
		if len(registro) != 5 {
			return nil, fmt.Errorf("registro invalido, se esperaban 5 columnas y llegaron %d", len(registro))
		}

		apuestas = append(apuestas, apuesta{
			Agency:    c.config.ID,
			FirstName: strings.TrimSpace(registro[0]),
			LastName:  strings.TrimSpace(registro[1]),
			Document:  strings.TrimSpace(registro[2]),
			Birthdate: strings.TrimSpace(registro[3]),
			Number:    strings.TrimSpace(registro[4]),
		})
	}

	return apuestas, nil
}

func (c *Client) serializarBatch(batch []apuesta) []byte {
	var mensaje strings.Builder
	mensaje.WriteString(fmt.Sprintf("BATCH|%d\n", len(batch)))

	for _, apuesta := range batch {
		mensaje.WriteString(fmt.Sprintf(
			"%s|%s|%s|%s|%s|%s\n",
			apuesta.Agency,
			apuesta.FirstName,
			apuesta.LastName,
			apuesta.Document,
			apuesta.Birthdate,
			apuesta.Number,
		))
	}

	return []byte(mensaje.String())
}

func (c *Client) enviarTodo(conn net.Conn, mensaje []byte) error {
	for len(mensaje) > 0 {
		n, err := conn.Write(mensaje)
		if err != nil {
			return err
		}

		if n == 0 {
			return io.ErrShortWrite
		}

		mensaje = mensaje[n:]
	}

	return nil
}

func (c *Client) enviarBatch(batch []apuesta, stop <-chan struct{}) error {
	if err := c.createClientSocket(); err != nil {
		return err
	}
	defer c.closeConnection()

	conn := c.currentConnection()
	if conn == nil {
		return fmt.Errorf("no se pudo obtener la conexion actual")
	}

	if err := c.enviarTodo(conn, c.serializarBatch(batch)); err != nil {
		return err
	}

	respuesta, err := bufio.NewReader(conn).ReadString('\n')
	if err != nil {
		if c.estaApagandose(stop) || err == io.EOF {
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return nil
		}
		return err
	}

	if strings.TrimSpace(respuesta) != "OK" {
		return fmt.Errorf("respuesta invalida del servidor")
	}

	return nil
}

func (c *Client) enviarComando(comando string) (string, error) {
	if err := c.createClientSocket(); err != nil {
		return "", err
	}
	defer c.closeConnection()

	conn := c.currentConnection()
	if conn == nil {
		return "", fmt.Errorf("no se pudo obtener la conexion actual")
	}

	if err := c.enviarTodo(conn, []byte(comando+"\n")); err != nil {
		return "", err
	}

	respuesta, err := bufio.NewReader(conn).ReadString('\n')
	if err != nil {
		return "", err
	}

	return strings.TrimSpace(respuesta), nil
}

func (c *Client) notificarFin() error {
	respuesta, err := c.enviarComando("FIN|" + c.config.ID)
	if err != nil {
		return err
	}

	if respuesta != "OK" {
		return fmt.Errorf("respuesta invalida al notificar fin")
	}

	return nil
}

func (c *Client) consultarGanadores(stop <-chan struct{}) error {
	for !c.estaApagandose(stop) {
		respuesta, err := c.enviarComando("WINNERS|" + c.config.ID)
		if err != nil {
			return err
		}

		if respuesta == "PENDING" {
			time.Sleep(100 * time.Millisecond)
			continue
		}

		partes := strings.Split(respuesta, "|")
		if len(partes) < 2 || partes[0] != "WINNERS" {
			return fmt.Errorf("respuesta invalida al consultar ganadores")
		}

		log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %s", partes[1])
		return nil
	}

	log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
	return nil
}

func (c *Client) lotes(apuestas []apuesta) [][]apuesta {
	tamanioBatch := c.config.MaxBatchAmount
	if tamanioBatch <= 0 {
		tamanioBatch = 1
	}

	var lotes [][]apuesta
	for inicio := 0; inicio < len(apuestas); inicio += tamanioBatch {
		fin := inicio + tamanioBatch
		if fin > len(apuestas) {
			fin = len(apuestas)
		}

		lotes = append(lotes, apuestas[inicio:fin])
	}

	return lotes
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(stop <-chan struct{}) {
	if c.estaApagandose(stop) {
		log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
		return
	}

	apuestas, err := c.cargarApuestas()
	if err != nil {
		log.Errorf("action: apuesta_enviada | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return
	}

	for _, batch := range c.lotes(apuestas) {
		if c.estaApagandose(stop) {
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return
		}

		if err := c.enviarBatch(batch, stop); err != nil {
			if c.estaApagandose(stop) {
				log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
				return
			}

			log.Errorf("action: apuesta_enviada | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}
	}

	if err := c.notificarFin(); err != nil {
		log.Errorf("action: consulta_ganadores | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return
	}

	if err := c.consultarGanadores(stop); err != nil {
		if c.estaApagandose(stop) {
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return
		}

		log.Errorf("action: consulta_ganadores | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return
	}

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
