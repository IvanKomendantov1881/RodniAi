package handler

import (
	"learning-bot/internal/dispatcher"
	"learning-bot/internal/queue"
	"learning-bot/internal/service"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

type Handler struct {
	bot         *tgbotapi.BotAPI
	userService *service.UserService
	queue       *queue.RabbitMQ
	dispatcher  *dispatcher.Dispatcher
}

func New(
	bot *tgbotapi.BotAPI,
	userService *service.UserService,
	queue *queue.RabbitMQ,
	dispatcher *dispatcher.Dispatcher,
) *Handler {

	return &Handler{
		bot:         bot,
		userService: userService,
		queue:       queue,
		dispatcher:  dispatcher,
	}
}
