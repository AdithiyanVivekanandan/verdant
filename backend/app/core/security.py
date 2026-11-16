from datetime import datetime, timedelta, timezone
from typing import Optional
import base64
import httpx
from jose import jwt
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey, SECP256R1
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicNumbers
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.hazmat.backends import default_backend

from app.core.config import settings

_jwks_cache: Optional[dict] = None
_jwks_cache_time: Optional[datetime] = None


def _b64url_decode_bytes(data: str) -> bytes:
    data += "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data)


def _b64url_decode_uint(data: str) -> int:
    return int.from_bytes(_b64url_decode_bytes(data), "big")


async def fetch_jwks() -> dict:
    global _jwks_cache, _jwks_cache_time
    now = datetime.now(timezone.utc)
    if _jwks_cache is not None and _jwks_cache_time is not None:
        if (now - _jwks_cache_time).total_seconds() < 3600:
            return _jwks_cache
    if not settings.SUPABASE_URL:
        raise ValueError("SUPABASE_URL is not configured")
    jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(jwks_url)
        resp.raise_for_status()
        _jwks_cache = resp.json()
        _jwks_cache_time = now
        return _jwks_cache


def _public_key_pem(jwks: dict, kid: str) -> Optional[tuple]:
    """Return (pem, algorithm) for the JWK matching kid, supporting RSA and EC keys."""
    keys = jwks.get("keys", []) if isinstance(jwks, dict) else []
    key = next((k for k in keys if k.get("kid") == kid), None)
    if not key:
        return None
    kty = key.get("kty")
    if kty == "RSA":
        n = _b64url_decode_uint(key["n"])
        e = _b64url_decode_uint(key["e"])
        numbers = RSAPublicNumbers(e, n)
        public_key = numbers.public_key(default_backend())
        pem = public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode("ascii")
        return (pem, "RS256")
    if kty == "EC":
        crv = key.get("crv")
        x = _b64url_decode_bytes(key["x"])
        y = _b64url_decode_bytes(key["y"])
        if crv == "P-256":
            curve = SECP256R1()
            alg = "ES256"
        else:
            return None
        encoded = b"\x04" + x + y
        public_key = EllipticCurvePublicKey.from_encoded_point(curve, encoded)
        pem = public_key.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode("ascii")
        return (pem, alg)
    return None


async def verify_supabase_jwt(token: str) -> Optional[dict]:
    """Verify a Supabase access token using the project's JWKS.

    Supabase may sign access tokens with RS256 (RSA) or ES256 (Elliptic Curve);
    the public keys are published at /auth/v1/.well-known/jwks.json. This fetches
    the current JWKS and verifies the signature with the key matching the token's
    `kid`, using the algorithm declared by that key.
    """
    try:
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        if not kid:
            return None
        jwks = await fetch_jwks()
        result = _public_key_pem(jwks, kid)
        if result is None:
            return None
        pem, algorithm = result
        issuer = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1"
        data = jwt.decode(
            token,
            pem,
            algorithms=[algorithm],
            audience="authenticated",
            issuer=issuer,
            options={"verify_signature": True, "verify_aud": True, "verify_iss": True},
        )
        return data
    except Exception:
        return None


async def extract_user_id(token: str) -> Optional[str]:
    """Extract the Supabase user ID (sub) from a verified JWT."""
    payload = await verify_supabase_jwt(token)
    if payload is None:
        return None
    return payload.get("sub")
