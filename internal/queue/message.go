package queue

type TaskMessage struct {
	TaskID  string      `json:"task_id"`
	Type    string      `json:"type"`
	UserID  int64       `json:"user_id"`
	Payload interface{} `json:"payload"`
}
type ResultMessage struct {
	Action string `json:"action"`
	UserID int64  `json:"user_id"`
	Status string `json:"status"`
	Data   any    `json:"data"`
}
