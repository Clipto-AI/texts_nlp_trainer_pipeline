package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

func promptOff(inputText string) string {
	return fmt.Sprintf("extract labels from the text for quick search:\n%s", inputText)
}

type Message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type Payload struct {
	Messages []Message `json:"messages"`
}

type APIResponse struct {
	Choices []struct {
		Message struct {
			Content string `json:"content"`
		} `json:"message"`
	} `json:"choices"`
}

func main() {
	text := "Elon Musk in conversation with another person"
	url := "http://192.168.2.112:8009/v1/chat/completions"

	prompt := promptOff(text)

	payload := Payload{
		Messages: []Message{
			{
				Role:    "user",
				Content: prompt,
			},
		},
	}

	jsonData, err := json.Marshal(payload)
	if err != nil {
		fmt.Printf("Error marshaling payload: %v\n", err)
		return
	}

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Post(url, "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		fmt.Printf("Error making request: %v\n", err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		fmt.Printf("API returned error status %d: %s\n", resp.StatusCode, string(body))
		return
	}

	var responseData APIResponse
	if err := json.NewDecoder(resp.Body).Decode(&responseData); err != nil {
		fmt.Printf("Error decoding response: %v\n", err)
		return
	}

	var entities string
	if len(responseData.Choices) > 0 {
		entities = responseData.Choices[0].Message.Content
	}

	fmt.Println(entities)
}
