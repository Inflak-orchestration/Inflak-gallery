from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_DIR / "frontend"
CATALOG_PATH = PROJECT_DIR / "data" / "catalog.json"
GALLERY_CASES_DIR = PROJECT_DIR / "data" / "gallery_cases"


def _pages_catalog() -> dict[str, Any]:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    cases = []
    for source in payload["cases"]:
        item = {key: value for key, value in source.items() if key not in {"videoFile", "historyFile"}}
        item["videoUrl"] = f'./data/gallery_cases/{source["videoFile"]}'
        item["historyUrl"] = f'./data/gallery_cases/{source["historyFile"]}'
        cases.append(item)
    return {**payload, "cases": cases}


def build(output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    html = (FRONTEND_DIR / "gallery.html").read_text(encoding="utf-8")
    replacements = {
        'href="/gallery/gallery.css?v=20260902"': 'href="./gallery.css?v=20260902"',
        'href="/gallery/"': 'href="./"',
        'src="/assets/inflak-logo.png"': 'src="./assets/inflak-logo.png"',
        'src="/gallery/gallery.js?v=20260902"': 'src="./gallery.js?v=20260902"',
    }
    for source, target in replacements.items():
        html = html.replace(source, target)
    (output_dir / "index.html").write_text(html, encoding="utf-8")

    shutil.copy2(FRONTEND_DIR / "gallery.css", output_dir / "gallery.css")
    gallery_js = (FRONTEND_DIR / "gallery.js").read_text(encoding="utf-8")
    gallery_js = gallery_js.replace('fetch("/api/gallery/cases")', 'fetch("./data/catalog.json")')
    (output_dir / "gallery.js").write_text(gallery_js, encoding="utf-8")
    shutil.copytree(FRONTEND_DIR / "assets", output_dir / "assets")
    shutil.copytree(GALLERY_CASES_DIR, output_dir / "data" / "gallery_cases")
    (output_dir / "data" / "catalog.json").write_text(
        json.dumps(_pages_catalog(), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / ".nojekyll").touch()


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the static GitHub Pages site.")
    parser.add_argument("--output", type=Path, default=PROJECT_DIR / "dist")
    args = parser.parse_args()
    build(args.output.resolve())


if __name__ == "__main__":
    main()