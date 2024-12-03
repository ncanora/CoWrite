package main

type Message struct {
	Command    string `json:"command"`    // Command type
	ClientName string `json:"clientName"` // For NEWCLIENT/REMOVECLIENT
	StartIndex int64  `json:"startIndex"` // for ADD/REMOVE
	EndIndex   int64  `json:"endIndex"`   // for ADD/REMOVE
	Content    string `json:"content"`    // for ADD
}
