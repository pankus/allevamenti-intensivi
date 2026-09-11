#!/usr/bin/env python3
"""Print a short-lived CLMS access token from a local service-key JSON file."""
import base64
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def b64url(value: bytes) -> bytes:
    return base64.urlsafe_b64encode(value).rstrip(b"=")


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit(f"uso: {Path(sys.argv[0]).name} SERVICE_KEY.json")
    key = json.loads(Path(sys.argv[1]).read_text())
    for field in ("client_id", "user_id", "token_uri", "private_key"):
        if not key.get(field):
            raise SystemExit(f"service key senza {field}")

    now = int(time.time())
    header = b64url(b'{"alg":"RS256","typ":"JWT"}')
    claims = b64url(json.dumps({
        "iss": key["client_id"], "sub": key["user_id"], "aud": key["token_uri"],
        "iat": now, "exp": now + 3000,
    }, separators=(",", ":")).encode())
    signed = header + b"." + claims

    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=True) as pem:
        pem.write(key["private_key"])
        pem.flush()
        signature = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", pem.name], input=signed,
            capture_output=True, check=True,
        ).stdout
    assertion = (signed + b"." + b64url(signature)).decode()
    response = subprocess.run(
        ["curl", "--fail", "--silent", "--show-error", "--request", "POST", key["token_uri"],
         "--header", "Accept: application/json", "--header", "Content-Type: application/x-www-form-urlencoded",
         "--data-urlencode", "grant_type=urn:ietf:params:oauth:grant-type:jwt-bearer",
         "--data-urlencode", f"assertion={assertion}"],
        capture_output=True, text=True, check=True,
    )
    print(json.loads(response.stdout)["access_token"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
