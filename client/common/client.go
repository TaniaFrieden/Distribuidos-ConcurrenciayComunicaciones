package common

import (
	"bufio"
	"fmt"
	"io"
	"net"
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
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
	mu     sync.Mutex
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
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		if c.isShuttingDown(stop) {
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return
		}

		// Create the connection the server in every loop iteration. Send an
		if err := c.createClientSocket(); err != nil {
			if c.isShuttingDown(stop) {
				log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
				return
			}
			return
		}

		message := []byte(fmt.Sprintf(
			"[CLIENT %v] Message N°%v\n",
			c.config.ID,
			msgID,
		))

		for len(message) > 0 {
			n, err := c.conn.Write(message)
			if err != nil {
				c.closeConnection()
				if c.isShuttingDown(stop) {
					log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
					return
				}
				log.Errorf("action: send_message | result: fail | client_id: %v | error: %v",
					c.config.ID,
					err,
				)
				return
			}

			if n == 0 {
				c.closeConnection()
				log.Errorf("action: send_message | result: fail | client_id: %v | error: %v",
					c.config.ID,
					io.ErrShortWrite,
				)
				return
			}

			message = message[n:]
		}

		msg, err := bufio.NewReader(c.conn).ReadString('\n')
		c.closeConnection()

		if err != nil {
			if c.isShuttingDown(stop) || err == io.EOF {
				log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
				return
			}
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
			c.config.ID,
			msg,
		)

		// Wait a time between sending one message and the next one
		select {
		case <-stop:
			log.Infof("action: shutdown | result: success | client_id: %v", c.config.ID)
			return
		case <-time.After(c.config.LoopPeriod):
		}

	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
