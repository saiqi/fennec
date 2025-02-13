import string
import random
import uuid
import base64
from passlib.hash import sha512_crypt as pwd_context


def random_string(min_length: int, max_length: int) -> str:
    choices = string.ascii_letters + string.punctuation + string.digits
    return "".join(
        random.choice(choices) for _ in range(random.randint(min_length, max_length))
    )


def random_password() -> str:
    return random_string(8, 12)


def random_client_id() -> str:
    return str(uuid.uuid4())


def random_client_secret() -> str:
    return base64.b64encode(random_string(24, 36).encode("utf-8")).decode("utf-8")


def verify_password(*, plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
