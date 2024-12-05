package main

import (
	"encoding/json"
	"log"
	"net/http"

	"github.com/gorilla/websocket"
)

var c *chan Message

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
}

func reader(conn *websocket.Conn, messages *chan Message) string {
	for {
		_, p, err := conn.ReadMessage()
		if err != nil {
			log.Println(err)
			return ""
		}

		log.Println("Received from client:", string(p))

		// Try to unmarshal into a single Message first
		var msg Message
		err = json.Unmarshal(p, &msg)
		if err == nil {
			if msg.Command == "NEWCLIENT" {
				msg.Conn = conn // Attach the connection to the message
			}
			*messages <- msg
			log.Println("Message passed to channel:", msg)
			continue
		}

		// If unmarshalling into a single Message fails, try unmarshalling into a slice of Messages
		var msgs []Message
		err = json.Unmarshal(p, &msgs)
		if err == nil {
			for _, m := range msgs {
				if m.Command == "NEWCLIENT" {
					m.Conn = conn // Attach the connection to the message
				}
				*messages <- m
				log.Println("Message passed to channel:", m)
			}
		} else {
			log.Println("Error unmarshalling message:", err)
		}
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
