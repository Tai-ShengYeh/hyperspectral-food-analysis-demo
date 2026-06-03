from __future__ import annotations

import argparse
import hashlib
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


DATASET_URL = "https://zenodo.org/records/8362947/files/SpectroFood_dataset.csv?download=1"
DATASET_MD5 = "15327c7fb3d5fe10231735a286629715"
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUTPUT = RAW_DIR / "SpectroFood_dataset.csv"


def md5sum(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, output: Path, force: bool = False) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)

    if output.exists() and output.stat().st_size > 0 and not force:
        size_mb = output.stat().st_size / 1024 / 1024
        print(f"Already downloaded: {output} ({size_mb:.2f} MB)")
        return

    if output.exists() and force:
        output.unlink()

    print(f"Downloading:\n  {url}\nTo:\n  {output}")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "food-analysis-teaching-demo/1.0",
        },
    )

    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                total = response.headers.get("Content-Length")
                total_bytes = int(total) if total and total.isdigit() else None
                downloaded = 0

                with output.open("wb") as handle:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        handle.write(chunk)
                        downloaded += len(chunk)
                        if total_bytes:
                            pct = downloaded / total_bytes * 100
                            print(f"\r  {downloaded / 1024 / 1024:.2f} MB / {total_bytes / 1024 / 1024:.2f} MB ({pct:.1f}%)", end="")
                        else:
                            print(f"\r  {downloaded / 1024 / 1024:.2f} MB", end="")
                print()
            break
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            print(f"Attempt {attempt} failed: {exc}")
            time.sleep(2 * attempt)
    else:
        raise SystemExit(f"Download failed after 3 attempts: {last_error}")

    if output.stat().st_size == 0:
        raise SystemExit("Downloaded file is empty.")

    actual_md5 = md5sum(output)
    if actual_md5 != DATASET_MD5:
        raise SystemExit(
            "Downloaded file checksum did not match Zenodo metadata.\n"
            f"Expected: {DATASET_MD5}\n"
            f"Actual:   {actual_md5}"
        )

    print(f"Done: {output} ({output.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"MD5 verified: {actual_md5}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Download the open SpectroFood hyperspectral dataset.")
    parser.add_argument("--force", action="store_true", help="Re-download even if the file already exists.")
    args = parser.parse_args(argv)
    download(DATASET_URL, OUTPUT, force=args.force)


if __name__ == "__main__":
    main(sys.argv[1:])
