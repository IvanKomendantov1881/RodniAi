package service

import (
	"context"

	"learning-bot/internal/models"
	"learning-bot/internal/repository"
)

type UserService struct {
	repo *repository.UserRepository
}

func NewUserService(
	repo *repository.UserRepository,
) *UserService {

	return &UserService{
		repo: repo,
	}
}

func (s *UserService) CreateUser(
	ctx context.Context,
	user models.User,
) error {

	return s.repo.Create(ctx, user)
}
