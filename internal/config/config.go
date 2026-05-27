package config

import (
	"os"

	"github.com/joho/godotenv"
)

type Config struct {
	BotToken   string
	DBHost     string
	DBPort     string
	DBUser     string
	DBPassword string
	DBName     string
	RabbitURL  string
}

func GetConfig() *Config {
	godotenv.Load() // просто пробуем загрузить, не падаем если нет

	return &Config{
		BotToken:   os.Getenv("BOT_TOKEN"),
		DBHost:     os.Getenv("DB_HOST"),
		DBPort:     os.Getenv("DB_PORT"),
		DBUser:     os.Getenv("DB_USER"),
		DBPassword: os.Getenv("DB_PASSWORD"),
		DBName:     os.Getenv("DB_NAME"),
		RabbitURL:  os.Getenv("RABBIT_URL"),
	}
}
