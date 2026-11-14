"""Vytvoří podpisový klíč pro Android (jednou, na tvém počítači).

Použití:
    pip install cryptography
    python scripts/create_signing_key.py

Vznikne soubor upload-keystore.p12 a textový soubor s jeho obsahem v base64.
Obsah base64 vlož na GitHubu do Settings → Secrets and variables → Actions jako
ANDROID_KEYSTORE_BASE64 a zvolené heslo jako ANDROID_KEYSTORE_PASSWORD.

Klíč i heslo si bezpečně ulož mimo repozitář. Bez nich nepůjde vydat aktualizaci,
kterou si hráči nainstalují přes starou verzi (bez ztráty dat).
"""
from __future__ import annotations

import base64
import datetime
import getpass
import sys

try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import pkcs12
    from cryptography.x509.oid import NameOID
except ImportError:
    sys.exit("Nejdřív nainstaluj knihovnu: pip install cryptography")

ALIAS = "upload"


def main() -> None:
    pwd = getpass.getpass("Zvol heslo ke klíči (min. 8 znaků): ")
    if len(pwd) < 8 or pwd != getpass.getpass("Zopakuj heslo: "):
        sys.exit("Heslo je kratší než 8 znaků, nebo se neshoduje.")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Denik dobrodruha")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=365 * 30)).sign(key, hashes.SHA256()))
    data = pkcs12.serialize_key_and_certificates(
        ALIAS.encode(), key, cert, None, serialization.BestAvailableEncryption(pwd.encode()))
    with open("upload-keystore.p12", "wb") as f:
        f.write(data)
    with open("upload-keystore.base64.txt", "w") as f:
        f.write(base64.b64encode(data).decode())
    print("Hotovo: upload-keystore.p12 a upload-keystore.base64.txt")
    print("Obsah .base64.txt vlož do secretu ANDROID_KEYSTORE_BASE64, heslo do ANDROID_KEYSTORE_PASSWORD.")
    print("Oba soubory pak přesuň na bezpečné místo a do repozitáře je nenahrávej.")


if __name__ == "__main__":
    main()
