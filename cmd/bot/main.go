package main

import (
	"context"
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

	disp := dispatcher.New(mq, bot)
	h := handler.New(bot, userService, mq, disp)
	u := tgbotapi.NewUpdate(0)
	u.Timeout = 60

	updates := bot.GetUpdatesChan(u)

	for update := range updates {
		h.Handle(update)
	}

}
