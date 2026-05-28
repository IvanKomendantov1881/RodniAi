package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"

	"learning-bot/internal/config"
	"learning-bot/internal/dispatcher"
	"learning-bot/internal/handler"
	"learning-bot/internal/queue"
	"learning-bot/internal/repository"
	"learning-bot/internal/repository/postgres"
	"learning-bot/internal/service"
	"learning-bot/internal/telegram"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

func main() {
	cfg := config.GetConfig()

	bot, err := telegram.NewBot(cfg.BotToken)
	if err != nil {
		log.Fatal(err)
	}
	log.Printf("Authorized on account %s", bot.Self.UserName)

	db, err := postgres.New(
		cfg.DBHost,
		cfg.DBPort,
		cfg.DBUser,
		cfg.DBPassword,
		cfg.DBName,
	)
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close(context.Background())

	userRepo := repository.NewUserRepository(db)
	userService := service.NewUserService(userRepo)

	mq, err := queue.NewRabbitMQ(cfg.RabbitURL)
	if err != nil {
		log.Fatal(err)
	}
	defer mq.Close()

	// Слушаем ответы от Python воркера
	msgs, err := mq.Consume()
	if err != nil {
		log.Fatal(err)
	}

	go func() {
		for msg := range msgs {
			var result queue.ResultMessage
			if err := json.Unmarshal(msg.Body, &result); err != nil {
				log.Println("Error parsing result:", err)
				continue
			}

			text := formatResult(result)
			if text == "" {
				continue
			}

			response := tgbotapi.NewMessage(result.UserID, text)
			response.ParseMode = "Markdown"
			bot.Send(response)
		}
	}()

	disp := dispatcher.New(mq, bot)
	h := handler.New(bot, userService, mq, disp)
	u := tgbotapi.NewUpdate(0)
	u.Timeout = 60

	updates := bot.GetUpdatesChan(u)
	for update := range updates {
		h.Handle(update)
	}
}

func formatResult(r queue.ResultMessage) string {
	switch r.Status {
	case "success":
		// Для pdf/audio/teach — просто возвращаем text
		if data, ok := r.Data.(map[string]any); ok {
			if text, ok := data["text"].(string); ok && text != "" {
				return text
			}
		}
		switch r.Action {
		case "add_word":
			if data, ok := r.Data.(map[string]any); ok {
				return fmt.Sprintf("✅ Слово *%s* добавлено!\n\n📖 *Определение:* %s\n\n💬 *Пример:* _%s_",
					data["word"], data["definition"], data["example"])
			}
		case "delete_word":
			if data, ok := r.Data.(map[string]any); ok {
				return fmt.Sprintf("🗑 Слово *%s* удалено", data["deleted_word"])
			}
		case "delete_all":
			return "🗑 Словарь очищен"
		case "get_dictionary":
			if words, ok := r.Data.([]any); ok {
				if len(words) == 0 {
					return "📖 Ваш словарь пуст"
				}
				text := "📖 *Ваш словарь:*\n\n"
				for _, w := range words {
					if word, ok := w.(map[string]any); ok {
						text += fmt.Sprintf("*%v.* %v — %v\n",
							word["id"], word["word"], word["definition"])
					}
				}
				return text
			}
		}
	case "not_found":
		return "❌ Слово не найдено в словаре"
	case "error":
		return "⚠️ Произошла ошибка при обработке"
	}
	return ""
}
