"""QR kód pozvánky jako obrázek PNG (knihovna qrcode jen spočítá body, PNG se poskládá bez Pillow)."""
from __future__ import annotations

import struct
import zlib


def matrix(text: str) -> list[list[bool]] | None:
    try:
        import qrcode  # type: ignore
    except Exception:  # pragma: no cover - knihovna chybí
        return None
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=2)
    q.add_data(text)
    q.make(fit=True)
    return q.get_matrix()


def png(text: str, scale: int = 8) -> bytes | None:
    """Černobílý PNG (bílý okraj), vhodný pro ft.Image(src=bytes)."""
    m = matrix(text)
    if not m:
        return None
    n = len(m)
    size = n * scale
    rows = bytearray()
    for y in range(n):
        line = bytearray([0])  # filtr 0
        for x in range(n):
            line += (b"\x00" if m[y][x] else b"\xff") * scale
        rows += bytes(line) * scale

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 0, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(rows), 9)) + chunk(b"IEND", b""))
