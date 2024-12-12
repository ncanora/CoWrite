package main

import (
	"github.com/gorilla/websocket"
)

type Message struct {
	Command        string          `json:"command"`
	ClientName     string          `json:"clientName,omitempty"`
	Key            string          `json:"key,omitempty"`
	StartIndex     int             `json:"startIndex,omitempty"`
	EndIndex       int             `json:"endIndex,omitempty"`
	Content        string          `json:"content,omitempty"`
	CursorLocation int             `json:"cursorLocation,omitempty"`
	ClientList     []string        `json:"clientList,omitempty"`
	Conn           *websocket.Conn `json:"-"`
}
