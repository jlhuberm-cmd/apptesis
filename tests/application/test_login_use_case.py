"""Tests del caso de uso de login (con mocks de los puertos)."""
import pytest

from application.dto.auth_dto import LoginRequest
from application.use_cases.auth.login_use_case import LoginUseCase
from domain.entities.user import AccountStatus, User, UserRole
from domain.exceptions.auth_exceptions import (
    AccountLockedError,
    AccountNotVerifiedError,
    InvalidCredentialsError,
)
from domain.ports.outbound.password_hasher import IPasswordHasher
from domain.ports.outbound.user_repository import IUserRepository


class FakeHasher(IPasswordHasher):
    def hash(self, password): return "H:" + password
    def verify(self, password, hashed): return hashed == "H:" + password
    def hash_code(self, code): return "C:" + code
    def verify_code(self, code, hashed): return hashed == "C:" + code


class InMemoryUserRepo(IUserRepository):
    def __init__(self): self._by_id = {}
    def save(self, user): self._by_id[user.id] = user; return user
    def find_by_id(self, user_id): return self._by_id.get(user_id)
    def find_by_email(self, email):
        return next((u for u in self._by_id.values() if u.email == email), None)
    def update(self, user): self._by_id[user.id] = user; return user
    def exists_by_email(self, email): return self.find_by_email(email) is not None


@pytest.fixture
def repo():
    return InMemoryUserRepo()


@pytest.fixture
def active_user(repo):
    user = User(
        email="ada@utpl.edu.ec",
        hashed_password="H:Abcdef1!",
        full_name="Ada",
        role=UserRole.RESEARCHER,
        status=AccountStatus.ACTIVE,
    )
    repo.save(user)
    return user


@pytest.fixture
def use_case(repo):
    return LoginUseCase(repo, FakeHasher())


def test_login_exitoso(use_case, active_user):
    res = use_case.execute(LoginRequest(email="ada@utpl.edu.ec", password="Abcdef1!"))
    assert res.email == "ada@utpl.edu.ec"
    assert res.role == "RESEARCHER"


def test_email_inexistente(use_case):
    with pytest.raises(InvalidCredentialsError):
        use_case.execute(LoginRequest(email="nadie@x.com", password="x"))


def test_password_incorrecta_incrementa_intentos(use_case, active_user, repo):
    with pytest.raises(InvalidCredentialsError) as exc:
        use_case.execute(LoginRequest(email="ada@utpl.edu.ec", password="WRONG1!x"))
    assert exc.value.remaining_attempts == 2
    assert repo.find_by_email("ada@utpl.edu.ec").failed_login_attempts == 1


def test_tercer_intento_bloquea(use_case, active_user, repo):
    for _ in range(2):
        with pytest.raises(InvalidCredentialsError):
            use_case.execute(LoginRequest(email="ada@utpl.edu.ec", password="bad1!Xyz"))
    # 3er intento -> bloqueo
    with pytest.raises(AccountLockedError):
        use_case.execute(LoginRequest(email="ada@utpl.edu.ec", password="bad1!Xyz"))
    assert repo.find_by_email("ada@utpl.edu.ec").is_locked()


def test_cuenta_no_verificada(repo):
    repo.save(User(email="p@x.com", hashed_password="H:Abcdef1!", full_name="P",
                   status=AccountStatus.PENDING_VERIFICATION))
    uc = LoginUseCase(repo, FakeHasher())
    with pytest.raises(AccountNotVerifiedError):
        uc.execute(LoginRequest(email="p@x.com", password="Abcdef1!"))


def test_cuenta_bloqueada_rechaza(repo):
    user = User(email="l@x.com", hashed_password="H:Abcdef1!", full_name="L",
                status=AccountStatus.LOCKED)
    repo.save(user)
    uc = LoginUseCase(repo, FakeHasher())
    with pytest.raises(AccountLockedError):
        uc.execute(LoginRequest(email="l@x.com", password="Abcdef1!"))


def test_login_exitoso_resetea_intentos(repo):
    user = User(email="r@x.com", hashed_password="H:Abcdef1!", full_name="R",
                status=AccountStatus.ACTIVE, failed_login_attempts=2)
    repo.save(user)
    uc = LoginUseCase(repo, FakeHasher())
    uc.execute(LoginRequest(email="r@x.com", password="Abcdef1!"))
    assert repo.find_by_email("r@x.com").failed_login_attempts == 0
