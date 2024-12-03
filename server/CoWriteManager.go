package main

import (
	"fmt"
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

			case "REMOVE":
				removeContent(message, cm)

			case "NEWCLIENT":
				addClient(message, cm)

			case "REMOVECLIENT":
				removeClient(message, cm)

			default:
				continue
			}
		default:

			continue
		}
	}
}

func addContent(message Message, cm *ClientManager, file *CoWriteFile) {
	// Step 1: Validate StartIndex
	if message.StartIndex < 0 || message.StartIndex > int64(len(file.Content)) {
		fmt.Printf("Invalid StartIndex: %d\n", message.StartIndex)
		return
	}

	// Step 2: Insert content at StartIndex
	updatedContent := append(file.Content[:message.StartIndex],
		append([]byte(message.Content), file.Content[message.StartIndex:]...)...)

	// Step 3: Update in-memory content
	file.Content = updatedContent

	// Step 4: Write back to the file
	err := os.WriteFile(file.Name, file.Content, 0644)
	if err != nil {
		fmt.Printf("Failed to write updated content to file: %v\n", err)
	}
	fmt.Printf("Added content: %s\n", message.Content)
}

func removeContent(message Message, cm *ClientManager) {

}

func addClient(message Message, cm *ClientManager) {

}

func removeClient(message Message, cm *ClientManager) {

}

func testAddContent(channel *chan Message) {
	// Initialize random seed for generating random content
	rand.Seed(time.Now().UnixNano())

	// Define some random test messages
	testMessages := []Message{
		{Command: "ADD", StartIndex: 0, Content: "Hello, "},
		{Command: "ADD", StartIndex: 7, Content: "world! "},
		{Command: "ADD", StartIndex: 6, Content: "beautiful "},
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
					StartIndex: int64(startIndex),
					Content:    string(randomContent),
				}

				fmt.Printf("Sending message: %+v\n", msg)
				*channel <- msg
			}

			time.Sleep(2 * time.Second)
		}
	}()
}
