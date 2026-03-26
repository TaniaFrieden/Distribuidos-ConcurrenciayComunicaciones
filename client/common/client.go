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

const (
	tiempoEsperaGanadores = 100 * time.Millisecond
	maxIntentosGanadores  = 100
	timeoutConexion       = 5 * time.Second
)

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
	conn, err := net.DialTimeout("tcp", c.config.ServerAddress, timeoutConexion)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}

	if err := conn.SetDeadline(time.Now().Add(timeoutConexion)); err != nil {
		conn.Close()
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

func (c *Client) tamanioBatch() int {
	if c.config.MaxBatchAmount <= 0 {
		return 1
	}

	return c.config.MaxBatchAmount
}

func (c *Client) apuestaDesdeRegistro(registro []string) (apuesta, error) {
	if len(registro) != 5 {
		return apuesta{}, fmt.Errorf("registro invalido, se esperaban 5 columnas y llegaron %d", len(registro))
	}

	return apuesta{
		Agency:    c.config.ID,
		FirstName: strings.TrimSpace(registro[0]),
		LastName:  strings.TrimSpace(registro[1]),
		Document:  strings.TrimSpace(registro[2]),
		Birthdate: strings.TrimSpace(registro[3]),
		Number:    strings.TrimSpace(registro[4]),
	}, nil
}

func (c *Client) enviarApuestasDesdeArchivo(stop <-chan struct{}) error {
	archivo, err := os.Open(c.rutaArchivoAgencia())
	if err != nil {
		return err
	}
	defer archivo.Close()

	lector := csv.NewReader(archivo)
	tamanioBatch := c.tamanioBatch()
	batch := make([]apuesta, 0, tamanioBatch)

	for {
		registro, err := lector.Read()
		if err == io.EOF {
			if len(batch) == 0 {
				return nil
			}

			return c.enviarBatch(batch, stop)
		}
		if err != nil {
			return err
		}

		apuestaActual, err := c.apuestaDesdeRegistro(registro)
		if err != nil {
			return err
		}

		batch = append(batch, apuestaActual)
		if len(batch) < tamanioBatch {
			continue
		}

		if err := c.enviarBatch(batch, stop); err != nil {
			return err
		}

		batch = make([]apuesta, 0, tamanioBatch)
	}
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
	for intento := 1; intento <= maxIntentosGanadores && !c.estaApagandose(stop); intento++ {
		respuesta, err := c.enviarComando("WINNERS|" + c.config.ID)
		if err != nil {
			return err
		}

		if respuesta == "PENDING" {
			time.Sleep(tiempoEsperaGanadores)
			continue
		}

		partes := strings.Split(respuesta, "|")
		if len(partes) < 2 || partes[0] != "WINNERS" {
			return fmt.Errorf("respuesta invalida al consultar ganadores")
		}

		log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %s", partes[1])
		return nil
	}

	if !c.estaApagandose(stop) {
		return fmt.Errorf("se agoto la espera de ganadores")
	}

	log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(stop <-chan struct{}) {
	if c.estaApagandose(stop) {
		log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
		return
	}

	if err := c.enviarApuestasDesdeArchivo(stop); err != nil {
		log.Errorf("action: apuesta_enviada | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return
	}

	if c.estaApagandose(stop) {
		log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
		return
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
}
