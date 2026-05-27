package dispatcher

import (
	"encoding/json"
	"fmt"
	"log"
	"strings"

	"learning-bot/internal/queue"
	"learning-bot/internal/storage"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api/v5"
)

type Dispatcher struct {
	queue *queue.RabbitMQ
	bot   *tgbotapi.BotAPI
}

func New(
	queue *queue.RabbitMQ,
	bot *tgbotapi.BotAPI,
) *Dispatcher {

	return &Dispatcher{
		queue: queue,
		bot:   bot,
	}
}

func (d *Dispatcher) Handle(update tgbotapi.Update) {

	if update.Message == nil {
		return
	}

	msg := update.Message

	// /teach
	if strings.HasPrefix(msg.Text, "/teach") {

		task := queue.TaskMessage{
			Type:   "teach",
			UserID: msg.From.ID,
			Payload: map[string]any{
				"text": msg.Text,
			},
		}

		body, _ := json.Marshal(task)

		err := d.queue.Publish(body)

		response := tgbotapi.NewMessage(
			msg.Chat.ID,
			"📚 Запрос на обучение отправлен в обработку",
		)

		d.bot.Send(response)
		if err != nil {
			log.Println(err)
		}

		return
	}

	// /english
	if strings.HasPrefix(msg.Text, "/english") {

		task := queue.TaskMessage{
			Type:   "english",
			UserID: msg.From.ID,
			Payload: map[string]any{
				"text": msg.Text,
			},
		}

		body, _ := json.Marshal(task)

		d.queue.Publish(body)
		response := tgbotapi.NewMessage(
			msg.Chat.ID,
			"🇬🇧 Английское слово отправлено в обработку",
		)

		d.bot.Send(response)
		return
	}

	// AUDIO
	if msg.Voice != nil {

		file, err := d.bot.GetFile(
			tgbotapi.FileConfig{
				FileID: msg.Voice.FileID,
			},
		)

		if err != nil {
			log.Println(err)
			return
		}

		fileURL := file.Link(d.bot.Token)

		filepath := "storage/" + msg.Voice.FileUniqueID + ".ogg"

		err = storage.DownloadFile(filepath, fileURL)

		if err != nil {
			log.Println(err)
			return
		}

		task := queue.TaskMessage{
			Type:   "audio",
			UserID: msg.From.ID,
			Payload: map[string]any{
				"filepath": filepath,
			},
		}

		body, _ := json.Marshal(task)

		d.queue.Publish(body)

		response := tgbotapi.NewMessage(
			msg.Chat.ID,
			"🎤 Аудио загружено и отправлено в обработку",
		)

		d.bot.Send(response)

		return
	}

	// 🎤 VOICE

	if msg.Voice != nil {

		processAudio(d, msg.Voice.FileID, msg.From.ID, "ogg", msg.Chat.ID)
		return
	}

	// 🎵 AUDIO (mp3, wav, m4a)
	if msg.Audio != nil {

		processAudio(d, msg.Audio.FileID, msg.From.ID, "audio", msg.Chat.ID)
		return
	}

	// 📎 AUDIO AS DOCUMENT (mp3/m4a sent as file)
	if msg.Document != nil &&
		(strings.HasSuffix(strings.ToLower(msg.Document.FileName), ".mp3") ||
			strings.HasSuffix(strings.ToLower(msg.Document.FileName), ".m4a") ||
			strings.HasSuffix(strings.ToLower(msg.Document.FileName), ".wav")) {

		processAudio(d, msg.Document.FileID, msg.From.ID, "audio", msg.Chat.ID)
		return
	}

	// PDF

	if msg.Document != nil &&
		(msg.Document.MimeType == "application/pdf" ||
			strings.HasSuffix(strings.ToLower(msg.Document.FileName), ".pdf")) {

		file, err := d.bot.GetFile(
			tgbotapi.FileConfig{
				FileID: msg.Document.FileID,
			},
		)

		if err != nil {
			log.Println(err)
			return
		}

		fileURL := file.Link(d.bot.Token)

		filepath := fmt.Sprintf(
			"storage/%s.pdf",
			msg.Document.FileUniqueID,
		)

		err = storage.DownloadFile(filepath, fileURL)
		if err != nil {
			log.Println(err)
			return
		}
		log.Println("PDF DOWNLOADED:", filepath)

		task := queue.TaskMessage{
			Type:   "pdf",
			UserID: msg.From.ID,
			Payload: map[string]any{
				"filepath": filepath,
			},
		}

		body, _ := json.Marshal(task)

		log.Println("PUBLISHING TO QUEUE...")
		err = d.queue.Publish(body)
		if err != nil {
			log.Println("QUEUE ERROR:", err)
		} else {
			log.Println("QUEUE OK")
		}

		response := tgbotapi.NewMessage(
			msg.Chat.ID,
			"📄 PDF загружен и отправлен в обработку",
		)

		d.bot.Send(response)

		return
	}
}

func processAudio(d *Dispatcher, fileID string, userID int64, ext string, chatID int64) {

	file, err := d.bot.GetFile(
		tgbotapi.FileConfig{FileID: fileID},
	)

	if err != nil {
		log.Println(err)
		return
	}

	fileURL := file.Link(d.bot.Token)

	filepath := fmt.Sprintf("storage/%s.%s", file.FileUniqueID, ext)

	err = storage.DownloadFile(filepath, fileURL)
	if err != nil {
		log.Println(err)
		return
	}

	task := queue.TaskMessage{
		Type:   "audio",
		UserID: userID,
		Payload: map[string]any{
			"filepath": filepath,
		},
	}

	body, _ := json.Marshal(task)
	d.queue.Publish(body)

	d.bot.Send(tgbotapi.NewMessage(
		chatID,
		"🎧 Аудио отправлено в обработку",
	))
}
