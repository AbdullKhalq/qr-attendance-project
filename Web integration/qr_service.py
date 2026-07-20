"""Signed QR token creation, validation, URL building, and PNG generation."""

from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlencode

import qrcode

from models import Lecture, parse_iso


class InvalidQRToken(ValueError):
    pass


@dataclass(frozen=True)
class QRTokenPayload:
    lecture_id: str
    expires_at: str
    nonce: str


class QRService:
    def __init__(self, secret_key: str, public_base_url: str) -> None:
        if not secret_key:
            raise ValueError("secret_key cannot be empty")
        self._secret = secret_key.encode("utf-8")
        self.public_base_url = public_base_url.rstrip("/")

    @staticmethod
    def _b64encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")

    @staticmethod
    def _b64decode(value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(value + padding)

    def create_token(self, lecture: Lecture) -> str:
        payload = {
            "lecture_id": lecture.lecture_id,
            "expires_at": lecture.expires_at,
            "nonce": secrets.token_urlsafe(12),
        }
        body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        signature = hmac.new(self._secret, body, hashlib.sha256).digest()
        return f"{self._b64encode(body)}.{self._b64encode(signature)}"

    def validate_token(self, token: str, check_expiry: bool = True) -> QRTokenPayload:
        try:
            encoded_body, encoded_signature = token.split(".", 1)
            body = self._b64decode(encoded_body)
            supplied_signature = self._b64decode(encoded_signature)
        except (ValueError, TypeError, base64.binascii.Error) as exc:
            raise InvalidQRToken("The QR token format is invalid.") from exc

        expected_signature = hmac.new(self._secret, body, hashlib.sha256).digest()
        if not hmac.compare_digest(supplied_signature, expected_signature):
            raise InvalidQRToken("The QR token signature is invalid.")

        try:
            payload = json.loads(body.decode("utf-8"))
            result = QRTokenPayload(**payload)
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError) as exc:
            raise InvalidQRToken("The QR token payload is invalid.") from exc

        if check_expiry and datetime.now(timezone.utc) > parse_iso(result.expires_at):
            raise InvalidQRToken("This lecture QR code has expired.")
        return result

    @staticmethod
    def token_hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def build_scan_url(self, token: str) -> str:
        return f"{self.public_base_url}/student/scan?{urlencode({'token': token})}"

    def create_qr_png(self, token: str) -> bytes:
        image = qrcode.make(self.build_scan_url(token))
        stream = io.BytesIO()
        image.save(stream, format="PNG")
        return stream.getvalue()
