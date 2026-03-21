package common

import (
	"bufio"
	"encoding/json"
	"io"
	"net"
	"strings"
	"sync"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
	FirstName     string
	LastName      string
	Document      string
	Birthdate     string
	Number        string
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
	mu     sync.Mutex
}

type betMessage struct {
	Agency    string `json:"agency"`
	FirstName string `json:"first_name"`
	LastName  string `json:"last_name"`
	Document  string `json:"document"`
	Birthdate string `json:"birthdate"`
	Number    string `json:"number"`
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

func (c *Client) isShuttingDown(stop <-chan struct{}) bool {
	select {
	case <-stop:
		return true
	default:
		return false
	}
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(stop <-chan struct{}) {
	if c.isShuttingDown(stop) {
		log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
		return
	}

	if err := c.createClientSocket(); err != nil {
		if c.isShuttingDown(stop) {
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return
		}
		return
	}

	conn := c.currentConnection()
	if conn == nil {
		log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
		return
	}

	messageData, err := json.Marshal(betMessage{
		Agency:    c.config.ID,
		FirstName: c.config.FirstName,
		LastName:  c.config.LastName,
		Document:  c.config.Document,
		Birthdate: c.config.Birthdate,
		Number:    c.config.Number,
	})
	if err != nil {
		c.closeConnection()
		log.Errorf("action: apuesta_enviada | result: fail | dni: %v | numero: %v | error: %v",
			c.config.Document,
			c.config.Number,
			err,
		)
		return
	}

	message := append(messageData, '\n')
	for len(message) > 0 {
		n, err := conn.Write(message)
		if err != nil {
			c.closeConnection()
			if c.isShuttingDown(stop) {
				log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
				return
			}
			log.Errorf("action: apuesta_enviada | result: fail | dni: %v | numero: %v | error: %v",
				c.config.Document,
				c.config.Number,
				err,
			)
			return
		}

		if n == 0 {
			c.closeConnection()
			log.Errorf("action: apuesta_enviada | result: fail | dni: %v | numero: %v | error: %v",
				c.config.Document,
				c.config.Number,
				io.ErrShortWrite,
			)
			return
		}

		message = message[n:]
	}

	response, err := bufio.NewReader(conn).ReadString('\n')
	c.closeConnection()

	if err != nil {
		if c.isShuttingDown(stop) || err == io.EOF {
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return
		}
		log.Errorf("action: apuesta_enviada | result: fail | dni: %v | numero: %v | error: %v",
			c.config.Document,
			c.config.Number,
			err,
		)
		return
	}

	if strings.TrimSpace(response) != "OK" {
		log.Errorf("action: apuesta_enviada | result: fail | dni: %v | numero: %v | error: invalid response",
			c.config.Document,
			c.config.Number,
		)
		return
	}

	log.Infof("action: apuesta_enviada | result: success | dni: %v | numero: %v",
		c.config.Document,
		c.config.Number,
	)
}
