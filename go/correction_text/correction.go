package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

func promptCorrection(inputText string) string {
	return fmt.Sprintf(`
You are a precise text proofreader. Correct ONLY the following clear errors:

1. Grammar: Fix verb tense agreement (e.g., "he go" → "he goes")
2. Spelling: Correct misspelled words (e.g., "bananaes" → "bananas")
3. Punctuation: Basic punctuation only (e.g., missing periods, unnecessary apostrophes)
4. Capitalization: Sentence beginnings and proper nouns only when clearly indicated

CRITICAL CONSTRAINTS:
- NEVER change correctly spelled words (e.g., "Your" → "your" is WRONG)
- NEVER add honorifics not in original (e.g., don't add "Dr." if not present)
- NEVER modify quoted speech or personal pronouns
- PRESERVE all names, titles, and phrasing exactly as written unless clearly misspelled

Examples:
Input: he go to the store
Output: He goes to the store

Input: elon musk says i like your show
Output: Elon Musk says I like your show

Input: dr smith will arrive tomorrow
Output: Dr. Smith will arrive tomorrow

Input: Elon Musk says I've been a longtime admirer of your show.
Output: Elon Musk says I've been a longtime admirer of your show.

Now correct this text:
%s
output:
`, inputText)
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
	usrNerAPI := "http://127.0.0.1:8080/v1/chat/completions"
	inputText := "Elon musk say I've been a longtime admirer of your show."

	prompt := promptCorrection(inputText)

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
	resp, err := client.Post(usrNerAPI, "application/json", bytes.NewBuffer(jsonData))
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
