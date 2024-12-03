package main

import (
	"log"
	"net/http"

	"github.com/gorilla/websocket"
)

var upgrader = websocket.Upgrader{
	ReadBufferSize:  1024,
	WriteBufferSize: 1024,
}

func reader(conn *websocket.Conn) string {
	for {
		messageType, p, err := conn.ReadMessage()
		if err != nil {
			log.Println(err)
			return ""
		}

		log.Println(string(p))

		if err := conn.WriteMessage(messageType, p); err != nil {
			log.Println(err)
			return ""
		}
		conn.WriteMessage(1, []byte(p))
	}
}

func wsEndpoint(w http.ResponseWriter, r *http.Request) {
	upgrader.CheckOrigin = func(r *http.Request) bool { return true }

	ws, err := upgrader.Upgrade(w, r, nil)

	if err != nil {
		log.Println(err)
	}

	log.Println("Client Connected")
	ws.WriteMessage(1, []byte("Hello Client!"))
	reader(ws)
}

func setupServer() {
	http.HandleFunc("/ws", wsEndpoint)
}
func main() {
	//fmt.Println("Starting server on port 8080")
	//setupServer()
	//log.Fatal(http.ListenAndServe(":8081", nil))
	file, error := initializeFile("test")

	if error != nil {
		log.Fatal(error)
	}
	c := createMessageChannel(100)
	cm := NewClientManager()
	testAddContent2(c, file)
	go executeClientInstructions(c, cm, file)

	for {

	}
}
