# InFlak Case Gallery

Standalone website for the recorded InFlak interaction corpus. It includes 15 videos, trace histories, taxonomy filters, case descriptions, trace-derived features, and the Layer skill files used in each recording.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./start
```

Open <http://127.0.0.1:8012/gallery/>.

Open a specific recording with `?case=<caseId>`, using the stable `caseId`
from the catalog, for example
<http://127.0.0.1:8012/gallery/?case=inflak-pN7-image-prompt-control>.
The same query parameter works on GitHub Pages. Selecting a case updates the
URL; closing it removes the parameter, and browser Back/Forward restores the
matching view. Unknown IDs leave the gallery list visible.

Set `INFLAK_GALLERY_PORT` to use another port. The website is self-contained and does not import or read files from another repository at runtime.

## GitHub Pages

Pushes to `main` automatically test, build, and deploy the static gallery through GitHub Actions. The published site is available at:

<https://inflak-orchestration.github.io/Inflak-gallery/>

The repository must use **Settings > Pages > Build and deployment > Source: GitHub Actions**. To build the same static output locally:

```bash
python3 build_pages.py
python3 -m http.server 8000 --directory dist
```

Open <http://127.0.0.1:8000/>. The generated `dist/` directory is ignored by Git; the deployment workflow rebuilds it from source.

## Data

- `data/catalog.json`: frozen public case metadata and trace-derived summaries
- `data/gallery_cases/clips/`: MP4 recordings
- `data/gallery_cases/<case>/<run>/`: `run.json` and `skill-trace.jsonl`

Layer names, paths, and invocation counts shown in the UI are frozen provenance metadata in `data/catalog.json`. The referenced plugin source files are intentionally not included, and the standalone site does not execute those skills.
