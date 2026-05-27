package handler

import (
	"context"
	"learning-bot/internal/models"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func (h *Handler) Start(message *tgbotapi.Message) error {
	msg := tgbotapi.NewMessage(
		message.Chat.ID,
		"Welcome to RAI Bot!",
	)
	// ОТПРАВЛЯЕМ СООБЩЕНИЕ (чтобы msg использовался):
	if _, err := h.bot.Send(msg); err != nil {
		return err
	}

	user := models.User{
		TelegramID: message.From.ID,
		Username:   message.From.UserName,
		FirstName:  message.From.FirstName,
	}

	err := h.userService.CreateUser(
		context.Background(),
		user,
	)

	if err != nil {
		return err
	}

	// ДОБАВЛЯЕМ В КОНЦЕ (если всё прошло без ошибок):
	return nil
}
