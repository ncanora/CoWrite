package main

import (
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"os"
	"time"
)

type CoWriteFile struct {
	Name    string
	Content []byte
}

// initializeFile creates or loads a .txt file into memory
func initializeFile(name string) (*CoWriteFile, error) {
	if len(name) < 4 || name[len(name)-4:] != ".txt" {
		name += ".txt"
	}

	// create the file if it doesn't exist
	var content []byte
	if _, err := os.Stat(name); os.IsNotExist(err) {
		err = os.WriteFile(name, []byte{}, 0644)
		if err != nil {
			return nil, fmt.Errorf("failed to create file: %w", err)
		}
		content = []byte{}
	} else {
		// Load
		var err error
		content, err = os.ReadFile(name)
		if err != nil {
			return nil, fmt.Errorf("failed to read file: %w", err)
		}
	}

	return &CoWriteFile{
		Name:    name,
		Content: content,
	}, nil
}

func createMessageChannel(value int) *chan Message {
	ch := make(chan Message, value)
	return &ch
}

func executeClientInstructions(c *chan Message, cm *ClientManager, file *CoWriteFile) {
	for {
		// Check if there's a message in the channel
		select {
		case message := <-(*c): // block until a message is received in channel
			switch message.Command {
			case "ADD":
				addContent(message, cm, file)
				broadcastMessage(message, cm) // Broadcast the ADD message

			case "REMOVE":
				removeContent(message, cm, file)
				broadcastMessage(message, cm) // Broadcast the REMOVE message

			case "NEWCLIENT":
				addClient(message, cm)

			case "REMOVECLIENT":
				removeClient(message, cm)

			case "CURSOR_MOVE":
				moveClient(message, cm)
				broadcastMessage(message, cm) // Broadcast the CLIENTMOVE message
			default:
				continue
			}
		default:
			continue
		}
	}
}

func addContent(message Message, cm *ClientManager, file *CoWriteFile) {
	// Validate index
	if message.StartIndex < 0 || message.StartIndex > int(len(file.Content)) {
		fmt.Printf("Invalid StartIndex: %d\n", message.StartIndex)
		return
	}

	updatedContent := append(file.Content[:message.StartIndex],
		append([]byte(message.Content), file.Content[message.StartIndex:]...)...)

	// Update in-memory content
	file.Content = updatedContent
	cm.File.Content = updatedContent
	// write-back to file
	err := os.WriteFile(file.Name, file.Content, 0644)
	if err != nil {
		fmt.Printf("Failed to write updated content to file: %v\n", err)
	}
	fmt.Printf("Added content: %s\n", message.Content)
}

func removeContent(message Message, cm *ClientManager, file *CoWriteFile) {
	// Validate indices
	if message.StartIndex < 0 || message.EndIndex > int(len(file.Content)) || message.StartIndex > message.EndIndex {
		fmt.Printf("Invalid StartIndex: %d\n", message.StartIndex)
		return
	}

	// construct slice without removed content
	updatedContent := append(file.Content[:message.StartIndex], file.Content[message.EndIndex:]...)

	file.Content = updatedContent
	cm.File.Content = updatedContent

	err := os.WriteFile(file.Name, file.Content, 0644)
	if err != nil {
		fmt.Printf("Failed to write updated content to file: %v\n", err)
	}

	fmt.Printf("Removed content between %d and %d\n", message.StartIndex, message.EndIndex)
}

func addClient(message Message, cm *ClientManager) {
	client := Client{
		Conn:           message.Conn,
		Name:           message.ClientName,
		CursorLocation: -1,
		LineNumber:     -1,
		Send:           make(chan []byte),
	}
	cm.AddClient(client)
	go clientWriter(&client)

	// Send current document content to the new client
	docMessage := Message{
		Command: "DOCUMENT",
		Content: string(cm.File.Content), // Ensure this contains the current content
	}
	msgBytes, err := json.Marshal(docMessage)
	if err != nil {
		log.Println("Error marshalling document message:", err)
		return
	}
	client.Send <- msgBytes
}

func removeClient(message Message, cm *ClientManager) {

}

func moveClient(message Message, cm *ClientManager) {
	client := cm.GetClientByName(message.ClientName)
	if client == nil {
		fmt.Printf("Client %s not found\n", message.ClientName)
		return
	}

	client.CursorLocation = message.CursorLocation
}

func broadcastMessage(message Message, cm *ClientManager) {
	msgBytes, err := json.Marshal(message)
	if err != nil {
		log.Println("Error marshalling message:", err)
		return
	}

	for _, client := range cm.Clients {
		if client.Name == message.ClientName {
			// Skip the originating client if necessary
			continue
		}
		if client.Send == nil {
			continue // Skip uninitialized clients
		}
		select {
		case client.Send <- msgBytes:
		default:
			log.Println("Client send channel blocked, removing client:", client.Name)
			cm.RemoveClientByName(client.Name)
		}
	}
}

func testAddContent(channel *chan Message, cm *ClientManager, file *CoWriteFile) {
	// Initialize random seed for generating random content
	rand.Seed(time.Now().UnixNano())

	// Define some random test messages
	testMessages := []Message{
		{Command: "ADD", StartIndex: 0, Content: "Hello, "},
		{Command: "ADD", StartIndex: 7, Content: "world! "},
		{Command: "ADD", StartIndex: 6, Content: "beautiful "},
		{Command: "REMOVE", StartIndex: 6, EndIndex: 17},
	}

	// Push the test messages into the channel
	go func() {
		for _, msg := range testMessages {
			fmt.Printf("Sending message: %+v\n", msg)
			*channel <- msg
			time.Sleep(500 * time.Millisecond) // Simulate slight delay between messages
		}
	}()
}

func testAddContent2(channel *chan Message, file *CoWriteFile) {
	// Initialize random seed for generating random content
	rand.Seed(time.Now().UnixNano())

	// Define possible characters for random content
	characters := "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ  \n"

	// Periodically send a batch of messages
	go func() {
		for {
			// Generate a random number of messages (e.g., 5-10)
			numMessages := rand.Intn(6) + 5

			for i := 0; i < numMessages; i++ {

				currentLength := len(file.Content)

				// Randomize start index within bounds
				startIndex := rand.Intn(currentLength + 5)

				contentLength := rand.Intn(16) + 5
				randomContent := make([]byte, contentLength)
				for j := range randomContent {
					randomContent[j] = characters[rand.Intn(len(characters))]
				}

				msg := Message{
					Command:    "ADD",
					StartIndex: int(startIndex),
					Content:    string(randomContent),
				}

				fmt.Printf("Sending message: %+v\n", msg)
				*channel <- msg
			}

			time.Sleep(2 * time.Second)
		}
	}()
}
