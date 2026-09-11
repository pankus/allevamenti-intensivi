#!/usr/bin/env python3
"""Validate the source URLs declared by download scripts, then run them."""
import argparse
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def source_url(script: Path) -> str:
    match = re.search(r'^URL="([^"]+)"$', script.read_text(), re.MULTILINE)
    if not match:
        raise ValueError(f"{script.name}: URL= non trovato")
    return match.group(1)


def valid(url: str) -> bool:
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(url, method=method, headers={"Range": "bytes=0-0"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return 200 <= response.status < 400
        except urllib.error.HTTPError as error:
            if method == "HEAD" and error.code in (403, 405):
                continue
            print(f"{error.code} {url}", file=sys.stderr)
            return False
        except urllib.error.URLError as error:
            print(f"{error.reason} {url}", file=sys.stderr)
            return False
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="controlla i link senza scaricare")
    parser.add_argument("scripts", nargs="*", help="nomi degli script, senza percorso")
    args = parser.parse_args()
    names = args.scripts or ["download_istat_confini_2025.sh"]
    jobs = [SCRIPTS / name for name in names]

    for job in jobs:
        if job.parent != SCRIPTS or not job.name.startswith("download_") or not job.is_file():
            parser.error(f"script non consentito: {job.name}")
        url = source_url(job)
        if not valid(url):
            return 1
        print(f"OK  {job.name}: {url}")

    if not args.check:
        for job in jobs:
            subprocess.run([str(job)], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
