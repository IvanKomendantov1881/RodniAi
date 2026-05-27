package repository

import (
	"context"

	"learning-bot/internal/models"

	"github.com/jackc/pgx/v5"
)

type UserRepository struct {
	db *pgx.Conn
}

func NewUserRepository(db *pgx.Conn) *UserRepository {
	return &UserRepository{
		db: db,
	}
}

func (r *UserRepository) Create(
	ctx context.Context,
	user models.User,
) error {

	query := `
	INSERT INTO users (
		telegram_id,
		username,
		first_name
	)
	VALUES ($1, $2, $3)
	ON CONFLICT (telegram_id) DO NOTHING
	`

	_, err := r.db.Exec(
		ctx,
		query,
		user.TelegramID,
		user.Username,
		user.FirstName,
	)

	return err
}
