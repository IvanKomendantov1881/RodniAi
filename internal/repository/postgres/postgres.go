package postgres

import (
	"context"
	"fmt"

	"github.com/jackc/pgx/v5"
)

func New(
	host,
	port,
	user,
	password,
	dbname string,
) (*pgx.Conn, error) {

	dsn := fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s",
		user,
		password,
		host,
		port,
		dbname,
	)

	conn, err := pgx.Connect(context.Background(), dsn)

	if err != nil {
		return nil, err
	}

	return conn, nil
}
