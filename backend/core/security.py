# AICTE Pre-Scrutiny & Deficiency Resolution Platform
# Security & Cryptography Utilities (backend/core/security.py)

import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Set
from passlib.context import CryptContext
from backend.core.config import settings

# Password Hashing via bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory Token Revocation / Blacklist Store (Thread-safe for single process MVP)
_revoked_tokens: Set[str] = set()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generates a secure bcrypt hash for the provided password."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a cryptographically signed JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    import uuid
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4())
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates signature, expiration, and claims of a JWT access token."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def revoke_token(token: str) -> None:
    """Revokes a JWT token on logout."""
    _revoked_tokens.add(token)


def is_token_revoked(token: str) -> bool:
    """Checks whether a token has been revoked."""
    return token in _revoked_tokens
