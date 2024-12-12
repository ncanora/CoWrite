package main

import (
	"encoding/json"
	"log"
	"net/http"
	"time"

	"github.com/gorilla/websocket"
)

const (
	writeWait      = 60 * time.Second    // Time allowed to write a message to the client.
	pongWait       = 60 * time.Second    // Time allowed to read the next pong message from the client.
	pingPeriod     = (pongWait * 9) / 10 // Send pings at this period. Must be less than pongWait.
	maxMessageSize = 512                 // Maximum message size allowed from client.
)

var c *chan Message

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
}

func reader(conn *websocket.Conn, messages *chan Message) {
	defer conn.Close()

	// Set maximum message size
	conn.SetReadLimit(maxMessageSize)
	// Set initial read deadline
	conn.SetReadDeadline(time.Now().Add(pongWait))
	// Handle Pong messages to reset read deadline
	conn.SetPongHandler(func(appData string) error {
		conn.SetReadDeadline(time.Now().Add(pongWait))
		return nil
	})

	// Create a ticker to send Ping messages periodically
	pingTicker := time.NewTicker(pingPeriod)
	defer pingTicker.Stop()

	// Create a channel to signal when to stop the ping goroutine
	done := make(chan struct{})

	// Start a goroutine to send Ping messages
	go func() {
		for {
			select {
			case <-pingTicker.C:
				// Send Ping message
				err := conn.WriteMessage(websocket.PingMessage, []byte{})
				if err != nil {
					log.Println("Error sending Ping:", err)
					conn.Close()
					return
				}
			case <-done:
				return
			}
		}
	}()

	for {
		_, p, err := conn.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				log.Printf("Read error: %v", err)
			} else {
				log.Printf("Read error: %v", err)
			}
			// Signal the ping goroutine to stop
			close(done)
			return
		}

		var msg Message
		err = json.Unmarshal(p, &msg)
		if err != nil {
			log.Println("Error unmarshalling message:", err)
			continue
		}

		if msg.Command == "NEWCLIENT" {
			msg.Conn = conn
		}

		*messages <- msg
	}
}

func wsEndpoint(w http.ResponseWriter, r *http.Request) {
	upgrader.CheckOrigin = func(r *http.Request) bool { return true }

	ws, err := upgrader.Upgrade(w, r, nil)

	if err != nil {
		log.Println(err)
	}

	log.Println("Client Connected")
	go reader(ws, c)
}

func setupServer() {
	http.HandleFunc("/ws", wsEndpoint)
	fs := http.FileServer(http.Dir("./JSClient"))
	http.Handle("/", fs)
}

func main() {
	// Initialize the file
	file, err := initializeFile("test")
	if err != nil {
		log.Fatal("Error initializing file:", err)
	}

	// Create message channel
	c = createMessageChannel(100)

	// Create client manager
	cm := NewClientManager(file)

	// Start the goroutine to execute client instructions
	go executeClientInstructions(c, cm, file)

	// Set up the server
	setupServer()

	// Start the server
	log.Println("Server started on port 8080")
	log.Fatal(http.ListenAndServe(":8080", nil))

	// Keep the main function running (optional if needed)
	// for {
	// 	time.Sleep(1 * time.Second)
	// }
}
