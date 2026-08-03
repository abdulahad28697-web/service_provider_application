from sqlalchemy.orm import Session
from repositories.admin.user_repository import UserRepository
from schemas.admin.request import UserCreate
from core.security import get_password_hash, verify_password
from core.exceptions import EntityAlreadyExistsException, CredentialsException
from models.user import User

class UserService:
    def __init__(self, db: Session):
        self.user_repo = UserRepository(db)

    def register_user(self, user_create: UserCreate) -> User:
        existing = self.user_repo.get_by_email(user_create.email)
        if existing:
            raise EntityAlreadyExistsException("User", "email", user_create.email)
        hashed_password = get_password_hash(user_create.password)
        return self.user_repo.create(user_create, hashed_password)

    def authenticate_user(self, email: str, password: str) -> User:
        user = self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise CredentialsException("Invalid email or password")
        if not user.is_active:
            raise CredentialsException("User account is inactive")
        return user

    def get_user_by_id(self, user_id: int) -> User | None:
        return self.user_repo.get_by_id(user_id)

    def get_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        return self.user_repo.get_all(skip, limit)
