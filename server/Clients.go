package main

import (
	"log"

	"github.com/gorilla/websocket"
)

type Client struct {
	Conn           *websocket.Conn
	Name           string
	CursorLocation int
	LineNumber     int
	Send           chan []byte
}

type ClientManager struct {
	Clients map[string]*Client
	File    *CoWriteFile
}

func NewClientManager(file *CoWriteFile) *ClientManager {
	return &ClientManager{Clients: make(map[string]*Client), File: file}
}

func (cm *ClientManager) AddClient(client Client) {
	cm.Clients[client.Name] = &client
}

func (cm *ClientManager) RemoveClientByName(clientName string) {
	if client, exists := cm.Clients[clientName]; exists {
		if client.Send != nil {
			close(client.Send)
		}
		delete(cm.Clients, clientName)
	}
}

func (cm *ClientManager) GetClientByName(name string) *Client {
	if client, exists := cm.Clients[name]; exists {
		return client
	}
	return nil
}

func (cm *ClientManager) GetClients() map[string]*Client {
	return cm.Clients
}

func (cm *ClientManager) UpdateLineLocation(client *Client) {
	if client.CursorLocation < 0 || int(client.CursorLocation) > len(cm.File.Content) {
		client.LineNumber = -1
		return
	}

	lineNum := 0
	currentIndex := 0

	for i, char := range cm.File.Content {
		if currentIndex >= client.CursorLocation {
			break
		}
		if char == '\n' {
			// Increment line number when encountering a newline
			lineNum++
		}
		currentIndex = i + 1 // Move to the next character index
	}

	client.LineNumber = lineNum
}

func clientWriter(client *Client) {
	defer func() {
		client.Conn.Close()
	}()

	for {
		message, ok := <-client.Send
		if !ok {
			// The channel was closed.
			return
		}

		err := client.Conn.WriteMessage(websocket.TextMessage, message)
		if err != nil {
			log.Println("Error writing message to client:", err)
			return
		}
	}
}
