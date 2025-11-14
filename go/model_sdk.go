package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"regexp"
	"strings"
	"time"
)

// LoRAConfig 表示 LoRA 配置项
type LoRAConfig struct {
	ID    int     `json:"id"`
	Scale float64 `json:"scale"`
}

// RequestPayload 表示发送给服务的请求负载
type RequestPayload struct {
	Prompt      string       `json:"prompt"`
	Stream      bool         `json:"stream"`
	Temperature float64      `json:"temperature"`
	TopP        float64      `json:"top_p"`
	Lora        []LoRAConfig `json:"lora"`
}

// StreamResponse 表示流式响应中的单个数据块
type StreamResponse struct {
	Content string `json:"content"`
	Stop    bool   `json:"stop"`
}

// KnowledgeGraph 表示解析后的知识图谱结构
type KnowledgeGraph struct {
	Triples     [][]string                   `json:"Triples"`
	EntityTypes map[string]string            `json:"Entity_types"`
	Attributes  map[string]map[string]string `json:"Attributes"`
}

// STTLMaps 存储 STTL 格式的映射表
var sttlMaps = struct {
	EntityMap      map[string]string
	AttrMap        map[string]string
	RelationMap    map[string]string
	AttrRegex      *regexp.Regexp
	RevEntityMap   map[string]string
	RevAttrMap     map[string]string
	RevRelationMap map[string]string
}{
	EntityMap: map[string]string{
		"Person":        "A",
		"Animal":        "B",
		"Organization":  "C",
		"Object":        "D",
		"Scene":         "E",
		"VisualContent": "F",
		"Term":          "G",
		"Event":         "H",
		"Action":        "I",
		"Speech":        "J",
		"Audio":         "K",
		"Sound":         "L",
		"Emotion":       "M",
		"Subtitle":      "N",
		"Topic":         "O",
		"Concept":       "P",
		"Shot":          "Q",
	},
	AttrMap: map[string]string{
		"Appearance.Accessories": "a",
		"Appearance.AgeGroup":    "b",
		"Appearance.Build":       "c",
		"Appearance.Clothing":    "d",
		"Appearance.Color":       "e",
		"Appearance.Expression":  "f",
		"Appearance.Gender":      "g",
		"Appearance.Hairstyle":   "h",
		"Appearance.Posture":     "i",
		"Appearance.Size":        "j",
		"Appearance.SkinColor":   "k",
		"Behavior":               "l",
		"Brand":                  "m",
		"Camera":                 "n",
		"Cause":                  "o",
		"Color":                  "p",
		"Content":                "q",
		"Definition":             "r",
		"Description":            "s",
		"Direction":              "t",
		"Domain":                 "u",
		"Duration":               "v",
		"Emotion":                "w",
		"EndTime":                "x",
		"Environment":            "y",
		"Function":               "z",
		"ID":                     "aa",
		"Intensity":              "ab",
		"Keywords":               "ac",
		"Language":               "ad",
		"Lighting":               "ae",
		"Location":               "af",
		"Loudness":               "ag",
		"Material":               "ah",
		"Name":                   "ai",
		"Participants":           "aj",
		"Pitch":                  "ak",
		"Quantity":               "al",
		"Role":                   "am",
		"Season":                 "an",
		"Source":                 "ao",
		"Speaker":                "ap",
		"Species":                "aq",
		"StartTime":              "ar",
		"Style":                  "as",
		"Target":                 "at",
		"Time":                   "au",
		"Timestamp":              "av",
		"Timing":                 "aw",
		"Tone":                   "ax",
		"Type":                   "ay",
		"Verb":                   "az",
		"Volume":                 "ba",
		"Weather":                "bb",
	},
	RelationMap: map[string]string{
		"Addressing":      "a",
		"AssociatedWith":  "b",
		"BasedOn":         "c",
		"CausedBy":        "d",
		"DepictedOn":      "e",
		"Describes":       "f",
		"Expresses":       "g",
		"Founded":         "h",
		"Has":             "i",
		"IndicatesSeason": "j",
		"InteractWith":    "k",
		"Involves":        "l",
		"IsA":             "m",
		"LocatedAt":       "n",
		"LocatedIn":       "o",
		"MemberOf":        "p",
		"OccursAt":        "q",
		"OccursIn":        "r",
		"PartOf":          "s",
		"Performs":        "t",
		"RelatedTo":       "u",
		"ShownIn":         "v",
		"SpokenBy":        "w",
		"Under":           "x",
		"UsedIn":          "y",
		"Uses":            "z",
		"Watching":        "aa",
		"WorksFor":        "ab",
	},
}

// init 初始化反向映射和正则表达式
func init() {
	// 初始化反向映射
	sttlMaps.RevEntityMap = make(map[string]string)
	for k, v := range sttlMaps.EntityMap {
		sttlMaps.RevEntityMap[v] = k
	}

	sttlMaps.RevAttrMap = make(map[string]string)
	for k, v := range sttlMaps.AttrMap {
		sttlMaps.RevAttrMap[v] = k
	}

	sttlMaps.RevRelationMap = make(map[string]string)
	for k, v := range sttlMaps.RelationMap {
		sttlMaps.RevRelationMap[v] = k
	}

	// 编译属性正则表达式（匹配 aa|ab|ac...|a|b|c... 等）
	// 注意：需要先匹配长的（aa, ab等），再匹配短的（a, b等）
	attrPattern := `\b(aa|ab|ac|ad|ae|af|ag|ah|ai|aj|ak|al|am|an|ao|ap|aq|ar|as|at|au|av|aw|ax|ay|az|ba|bb|a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|y|z)=([^;]*);?`
	sttlMaps.AttrRegex = regexp.MustCompile(attrPattern)
}

// CallModelAPI 调用模型 API 服务
// host: 服务主机地址（如 "127.0.0.1"）
// port: 服务端口（如 "8080"）
// prompt: 输入的提示文本
// loraList: LoRA 配置列表
// temp: 温度参数
// topP: top_p 参数
// 返回: API 响应字符串和可能的错误
func CallModelAPI(host, port, prompt string, loraList []LoRAConfig, temp, topP float64) (string, error) {
	// 构建完整的 URL
	url := fmt.Sprintf("http://%s:%s/completion", host, port)

	// 构建请求负载
	payload := RequestPayload{
		Prompt:      prompt,
		Stream:      true,
		Temperature: temp,
		TopP:        topP,
		Lora:        loraList,
	}

	// 将负载序列化为 JSON
	jsonData, err := json.Marshal(payload)
	if err != nil {
		return "", fmt.Errorf("序列化 JSON 失败: %w", err)
	}

	// 创建 HTTP 请求
	req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
	if err != nil {
		return "", fmt.Errorf("创建请求失败: %w", err)
	}

	// 设置请求头
	req.Header.Set("Content-Type", "application/json")

	// 创建 HTTP 客户端，设置超时
	client := &http.Client{
		Timeout: 30 * time.Second,
	}

	// 发送请求
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("发送请求失败: %w", err)
	}
	defer resp.Body.Close()

	// 检查响应状态码
	if resp.StatusCode != http.StatusOK {
		bodyBytes, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("请求失败，状态码: %d, 响应: %s", resp.StatusCode, string(bodyBytes))
	}

	// 处理流式响应
	if payload.Stream {
		return processStreamResponse(resp.Body)
	}

	// 读取非流式响应体
	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("读取响应失败: %w", err)
	}

	return string(bodyBytes), nil
}

// processStreamResponse 处理流式响应（Server-Sent Events 格式）
func processStreamResponse(body io.ReadCloser) (string, error) {
	var result strings.Builder
	scanner := bufio.NewScanner(body)

	for scanner.Scan() {
		line := scanner.Text()
		// 跳过空行
		if line == "" {
			continue
		}
		// 处理 SSE 格式的数据行（以 "data: " 开头）
		if strings.HasPrefix(line, "data: ") {
			data := strings.TrimPrefix(line, "data: ")
			// 跳过最后的空数据块
			if data == "" || data == "[DONE]" {
				continue
			}

			var streamResp StreamResponse
			if err := json.Unmarshal([]byte(data), &streamResp); err != nil {
				// 如果解析失败，可能是其他格式的数据，继续处理
				continue
			}

			// 拼接内容
			result.WriteString(streamResp.Content)

			// 如果收到停止信号，结束处理
			if streamResp.Stop {
				break
			}
		}
	}

	if err := scanner.Err(); err != nil {
		return "", fmt.Errorf("读取流式响应失败: %w", err)
	}

	return result.String(), nil
}

// ConvertSttlToJson 将 STTL 格式的字符串转换为 JSON 格式的知识图谱
// sttl: STTL 格式的字符串
// parseMentions: 是否解析 mentions 属性
func ConvertSttlToJson(sttl string, parseMentions bool) (*KnowledgeGraph, error) {
	kg := &KnowledgeGraph{
		Triples:     make([][]string, 0),
		EntityTypes: make(map[string]string),
		Attributes:  make(map[string]map[string]string),
	}

	// 分割行并过滤空行
	lines := strings.Split(sttl, "\n")
	mode := "entity"

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		// 检查是否切换到关系模式
		if strings.HasPrefix(line, "#R") {
			mode = "rel"
			continue
		}

		if mode == "entity" {
			// 解析实体行
			if !strings.Contains(line, ":") {
				continue
			}

			parts := strings.SplitN(line, ":", 2)
			if len(parts) != 2 {
				continue
			}

			entPart := parts[0]
			rest0 := parts[1]

			// 处理实体名称（将下划线替换为空格）
			entName := strings.ReplaceAll(entPart, "_", " ")
			entName = strings.TrimSpace(entName)

			var typeCode, attrPart string
			if strings.Contains(rest0, "|") {
				pipeParts := strings.SplitN(rest0, "|", 2)
				typeCode = pipeParts[0]
				if len(pipeParts) > 1 {
					attrPart = pipeParts[1]
				}
			} else {
				typeCode = rest0
			}

			typeCode = strings.TrimSpace(typeCode)
			entType := sttlMaps.RevEntityMap[typeCode]
			if entType == "" {
				entType = "Unknown"
			}

			attrs := make(map[string]string)
			mentionsVal := ""

			if attrPart != "" {
				// 处理 mentions
				if parseMentions && strings.Contains(attrPart, ";m=") {
					idx := strings.LastIndex(attrPart, ";m=")
					mentionsVal = attrPart[idx+3:]
					attrPart = attrPart[:idx]
				}

				// 确保以分号结尾以便正则匹配
				if !strings.HasSuffix(attrPart, ";") {
					attrPart += ";"
				}

				// 使用正则表达式匹配所有属性
				matches := sttlMaps.AttrRegex.FindAllStringSubmatch(attrPart, -1)
				for _, match := range matches {
					if len(match) >= 3 {
						keyCode := match[1]
						value := match[2]
						if key := sttlMaps.RevAttrMap[keyCode]; key != "" {
							attrs[key] = value
						}
					}
				}
			}

			kg.EntityTypes[entName] = entType
			kg.Attributes[entName] = attrs

			if parseMentions && mentionsVal != "" {
				kg.Attributes[entName]["mentions"] = mentionsVal
			}

		} else if mode == "rel" {
			// 解析关系行
			parts := strings.Fields(line)
			if len(parts) < 3 {
				continue
			}

			s := strings.ReplaceAll(parts[0], "_", " ")
			rCode := parts[1]
			o := strings.ReplaceAll(parts[2], "_", " ")

			rel := sttlMaps.RevRelationMap[rCode]
			if rel == "" {
				rel = rCode
			}

			kg.Triples = append(kg.Triples, []string{s, rel, o})
		}
	}

	return kg, nil
}

// 人称代词集合，用于过滤 Person 实体（使用小写键以便不区分大小写匹配）
var pronouns = map[string]bool{
	"i":    true,
	"we":   true,
	"he":   true,
	"she":  true,
	"her":  true,
	"me":   true,
	"them": true,
	"they": true,
	"you":  true,
}

// isPronoun 检查给定的字符串是否是人称代词（不区分大小写）
func isPronoun(s string) bool {
	return pronouns[strings.ToLower(s)]
}

// ExtractNER 从知识图谱中提取命名实体
// 规则：
// 1. Entity_types 里面包含需要提取的实体
// 2. 如果实体为 Person，则看 Attributes 里面该实体是否有 Name，如果有 Name，则在 Name 实体中增加这个 Person 的 Name
// 3. 对于 Person 实体，还要提取 Behavior 属性，添加到 "Behavior" 键下
// 4. 其他实体，则 Key 是 Entity 类型，如果该实体有 Name，则取出来该实体的 Name 属性为该类型的值
// 5. 实体不能重复，每个实体名称在每个类型下只出现一次
// 6. Person 实体如果是人称代词（I, we, he, she, her, me, them, they, you），则丢弃
// 返回: map[string][]string，键为实体类型、"Name" 或 "Behavior"，值为实体名称数组
func ExtractNER(kg *KnowledgeGraph) map[string][]string {
	result := make(map[string][]string)
	// 用于跟踪每个类型下已经添加的实体，避免重复
	seen := make(map[string]map[string]bool)

	// 遍历所有实体
	for entityName, entityType := range kg.EntityTypes {
		// 获取该实体的属性
		attrs, hasAttrs := kg.Attributes[entityName]

		// 获取 Name 属性值，如果没有则使用实体名称本身
		var nameValue string
		if hasAttrs {
			if name, ok := attrs["Name"]; ok && name != "" {
				nameValue = name
			} else {
				nameValue = entityName
			}
		} else {
			nameValue = entityName
		}

		// 根据实体类型处理
		if entityType == "Person" {
			// 如果是 Person 类型且是人称代词，则跳过
			if isPronoun(nameValue) {
				continue
			}

			// 添加 Person 的 Name
			targetKey := "Name"
			if seen[targetKey] == nil {
				seen[targetKey] = make(map[string]bool)
			}
			if !seen[targetKey][nameValue] {
				if result[targetKey] == nil {
					result[targetKey] = make([]string, 0)
				}
				result[targetKey] = append(result[targetKey], nameValue)
				seen[targetKey][nameValue] = true
			}

			// 提取 Person 的 Behavior 属性
			if hasAttrs {
				if behavior, ok := attrs["Behavior"]; ok && behavior != "" {
					behaviorKey := "Behavior"
					if seen[behaviorKey] == nil {
						seen[behaviorKey] = make(map[string]bool)
					}
					if !seen[behaviorKey][behavior] {
						if result[behaviorKey] == nil {
							result[behaviorKey] = make([]string, 0)
						}
						result[behaviorKey] = append(result[behaviorKey], behavior)
						seen[behaviorKey][behavior] = true
					}
				}
			}
		} else {
			// 其他实体类型
			targetKey := entityType
			if seen[targetKey] == nil {
				seen[targetKey] = make(map[string]bool)
			}
			if !seen[targetKey][nameValue] {
				if result[targetKey] == nil {
					result[targetKey] = make([]string, 0)
				}
				result[targetKey] = append(result[targetKey], nameValue)
				seen[targetKey][nameValue] = true
			}
		}
	}

	return result
}

// 示例使用函数
func ExampleUsage() {
	// 示例参数
	host := "127.0.0.1"
	port := "8080"
	prompt := "<|im_start|>user\nPlease extract entities, relations and attributes from the following text\nUnfortunately, I can't tell you too much more than the report already says about them because, given the topic, it was really important that we give them a chance to be anonymous so they could be as candid with us as possible and really share the depth of their insights and experience.  It was just these interviews.  We didn't do a lot of screening other than do you have enough experience to comment.  on this in a meaningful way.  So, Annie, why do you think political uncertainty is such a hot topic?<|im_end|><|im_start|>assistant\n"

	loraList := []LoRAConfig{
		{ID: 0, Scale: 1},
		{ID: 1, Scale: 0},
	}

	temp := 0.9
	topP := 0.6

	// 调用 API
	result, err := CallModelAPI(host, port, prompt, loraList, temp, topP)
	if err != nil {
		fmt.Printf("调用 API 失败: %v\n", err)
		return
	}

	fmt.Println("API 原始响应:")
	fmt.Println(result)
	fmt.Println("\n" + strings.Repeat("=", 80) + "\n")

	// 解析 STTL 格式为 JSON
	kg, err := ConvertSttlToJson(result, true)
	if err != nil {
		fmt.Printf("解析 STTL 失败: %v\n", err)
		return
	}

	// 转换为 JSON 字符串
	jsonBytes, err := json.MarshalIndent(kg, "", "  ")
	if err != nil {
		fmt.Printf("序列化 JSON 失败: %v\n", err)
		return
	}

	fmt.Println("解析后的 JSON:")
	fmt.Println(string(jsonBytes))
	fmt.Println("\n" + strings.Repeat("=", 80) + "\n")

	// 提取命名实体
	nerResult := ExtractNER(kg)
	nerBytes, err := json.MarshalIndent(nerResult, "", "  ")
	if err != nil {
		fmt.Printf("序列化 NER 结果失败: %v\n", err)
		return
	}

	fmt.Println("提取的命名实体 (NER):")
	fmt.Println(string(nerBytes))
}

// main 函数，程序入口
func main() {
	ExampleUsage()
}
