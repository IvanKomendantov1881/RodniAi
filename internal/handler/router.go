package handler

import tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"

func (h *Handler) Handle(update tgbotapi.Update) {
	h.dispatcher.Handle(update)
}
