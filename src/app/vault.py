"""Šifrování tajných dat kampaně PJ heslem kampaně (poznámky, mapy).

Jen standardní knihovna (běží i na webu a v Androidu, kde chybí OpenSSL):
klíč PBKDF2-HMAC-SHA256 z hesla a vlastní soli, šifra HMAC-SHA256 v režimu čítače (proud klíčů),
autentizace HMAC-SHA256 (šifrovaný text nejde nepozorovaně změnit, špatné heslo se pozná).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os

VERSION = 1


def pbkdf2(password: bytes, salt: bytes, rounds: int) -> bytes:
    """PBKDF2-HMAC-SHA256. Webová verze a Android (Python bez OpenSSL) nemají hashlib.pbkdf2_hmac,
    proto náhradní výpočet v čistém Pythonu (stejný výsledek)."""
    fast = getattr(hashlib, "pbkdf2_hmac", None)
    if fast is not None:
        try:
            return fast("sha256", password, salt, rounds)
        except (ValueError, AttributeError):  # pragma: no cover - sha256 bez OpenSSL
            pass
    if len(password) > 64:
        password = hashlib.sha256(password).digest()
    key = password.ljust(64, b"\0")
    inner = hashlib.sha256(bytes(b ^ 0x36 for b in key))
    outer = hashlib.sha256(bytes(b ^ 0x5C for b in key))

    def prf(msg: bytes) -> bytes:
        i = inner.copy()
        i.update(msg)
        o = outer.copy()
        o.update(i.digest())
        return o.digest()

    u = prf(salt + b"\x00\x00\x00\x01")
    acc = int.from_bytes(u, "big")
    for _ in range(rounds - 1):
        u = prf(u)
        acc ^= int.from_bytes(u, "big")
    return acc.to_bytes(32, "big")


def derive(password: str, salt_hex: str, rounds: int) -> bytes:
    """32 bajtů klíče z hesla kampaně (sůl šifrování je jiná než sůl ověření hesla)."""
    return pbkdf2(password.encode("utf-8"), bytes.fromhex(salt_hex), rounds)


def _keys(key: bytes) -> tuple[bytes, bytes]:
    return hashlib.sha256(key + b"enc").digest(), hashlib.sha256(key + b"mac").digest()


def _stream(k: bytes, nonce: bytes, n: int) -> bytes:
    out = bytearray()
    i = 0
    while len(out) < n:
        out += hmac.new(k, nonce + i.to_bytes(8, "big"), hashlib.sha256).digest()
        i += 1
    return bytes(out[:n])


def _xor(a: bytes, b: bytes) -> bytes:
    return (int.from_bytes(a, "big") ^ int.from_bytes(b, "big")).to_bytes(len(a), "big") if a else b""


def seal(key: bytes, obj) -> dict:
    ek, mk = _keys(key)
    nonce = os.urandom(16)
    plain = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ct = _xor(plain, _stream(ek, nonce, len(plain)))
    tag = hmac.new(mk, nonce + ct, hashlib.sha256).hexdigest()
    return {"v": VERSION, "n": nonce.hex(), "ct": base64.b64encode(ct).decode("ascii"), "tag": tag}


def open_box(key: bytes, box: dict):
    """Rozšifruje; při špatném klíči nebo poškozených datech ValueError."""
    ek, mk = _keys(key)
    nonce = bytes.fromhex(box["n"])
    ct = base64.b64decode(box["ct"])
    tag = hmac.new(mk, nonce + ct, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(tag, box.get("tag", "")):
        raise ValueError("Tajná data kampaně nejde otevřít (jiné heslo nebo poškozená data).")
    return json.loads(_xor(ct, _stream(ek, nonce, len(ct))).decode("utf-8"))
