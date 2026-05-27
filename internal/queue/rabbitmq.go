package queue

import (
	"context"

	amqp "github.com/rabbitmq/amqp091-go"
)

type RabbitMQ struct {
	conn    *amqp.Connection
	channel *amqp.Channel
}

func NewRabbitMQ(url string) (*RabbitMQ, error) {
	conn, err := amqp.Dial(url)
	if err != nil {
		return nil, err
	}

	ch, err := conn.Channel()
	if err != nil {
		return nil, err
	}

	mq := &RabbitMQ{
		conn:    conn,
		channel: ch,
	}

	_, err = mq.channel.QueueDeclare("tasks", true, false, false, false, nil)
	if err != nil {
		return nil, err
	}

	_, err = mq.channel.QueueDeclare("go_results", true, false, false, false, nil)
	if err != nil {
		return nil, err
	}

	return mq, nil
}

func (r *RabbitMQ) Close() {
	r.channel.Close()
	r.conn.Close()
}

func (r *RabbitMQ) Publish(body []byte) error {
	return r.channel.PublishWithContext(
		context.Background(),
		"",
		"tasks",
		false,
		false,
		amqp.Publishing{
			ContentType: "application/json",
			Body:        body,
		},
	)
}

func (r *RabbitMQ) Consume() (<-chan amqp.Delivery, error) {
	return r.channel.Consume(
		"go_results",
		"",
		true,
		false,
		false,
		false,
		nil,
	)
}
