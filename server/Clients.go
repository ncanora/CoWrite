package main

import (
	"github.com/gorilla/websocket"
)

type Client struct {
	Conn           *websocket.Conn
	Name           string
	cursorLocation int64
}

type ClientManager struct {
	clients []Client
}

func NewClientManager() *ClientManager {
	return &ClientManager{clients: make([]Client, 4)}
}

func (cm *ClientManager) AddClient(client Client) {
	cm.clients = append(cm.clients, client)
}

func (cm *ClientManager) RemoveClientByName(client Client) {
	for i, c := range cm.clients {
		if c.Name == client.Name {
			cm.clients = append(cm.clients[:i], cm.clients[i+1:]...)
			break
		}
	}
}

func (cm *ClientManager) GetClientByName(name string) *Client {
	for _, c := range cm.clients {
		if c.Name == name {
			return &c
		}
	}
	return nil
}
