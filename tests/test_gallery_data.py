import json
import tempfile
import unittest
from pathlib import Path

import app
import build_pages


class GalleryDataTests(unittest.TestCase):
    def test_main_case_uses_latest_uploaded_history(self):
        item = app._catalog()["cases"][0]

        self.assertEqual(item["caseId"], "inflak-main")
        self.assertEqual(item["run"]["runId"], "9c39a97ac6c44892a2f101d15714cd1b")
        self.assertEqual(item["features"]["eventCount"], 54)
        self.assertEqual(item["features"]["completedSteps"], 27)
        self.assertEqual(item["features"]["interactionCount"], 4)
        self.assertEqual(item["features"]["durationSeconds"], 389)
        self.assertEqual(
            item["historyFile"],
            "inflak-main/9c39a97ac6c44892a2f101d15714cd1b/skill-trace.jsonl",
        )

    def test_catalog_contains_complete_media_and_history(self):
        payload = app._catalog()
        cases = payload["cases"]

        self.assertEqual(len(cases), 15)
        self.assertEqual(payload["count"], 15)
        self.assertEqual(len({item["caseId"] for item in cases}), 15)
        for item in cases:
            self.assertTrue(app._confined_file(item["videoFile"]).is_file())
            self.assertTrue(app._confined_file(item["historyFile"]).is_file())
            self.assertTrue(item["description"])
            self.assertTrue(item["artifactSubstrates"])
            self.assertTrue(item["interactionRealizations"])
            self.assertEqual(set(item["layerFiles"]), {"L1", "L2", "L3", "L4"})
            plugin_prefix = f'plugins/{item["run"]["pluginId"]}/'
            for files in item["layerFiles"].values():
                for layer_file in files:
                    self.assertTrue(layer_file["name"])
                    self.assertRegex(layer_file["path"], r"^plugins/.+/SKILL\.md$")
                    self.assertTrue(layer_file["path"].startswith(plugin_prefix))
                    self.assertGreater(layer_file["invocations"], 0)

    def test_cover_times_are_frozen_to_reviewed_frames(self):
        expected = [10, 3, 7, 10, 22, 7, 17, 5, 16, 20, 13, 9, 3, 6, 33]
        self.assertEqual([item["coverTimeSeconds"] for item in app._catalog()["cases"]], expected)

    def test_paradigm_titles_and_taxonomy_use_reviewed_wording(self):
        payload = app._catalog()
        paradigm_cases = [item for item in payload["cases"] if item["kind"] == "paradigm"]
        expected_titles = [
            "P1 User-Driven Prompt Refinement",
            "P2 User-Driven Prompt Organization",
            "P3 Interaction as Part of Instruction",
            "P4 Referenced Artifact as Instruction",
            "P5 AI-Driven Prompt Suggestion",
            "P6 AI-Driven Prompt Decomposition",
            "P7 Generative Prompt Control Widgets",
            "P8 Generative Artifact Control Widgets",
            "P9 Artifact to Structured Instruction",
            "P10 Artifact to Multimodal Instruction",
            "P11 Artifact-Driven Prompt Enhancement",
            "P12 Interactive Artifact Refinement",
            "P13 AI-Proactively-Initiated Interaction",
        ]
        expected_slugs = [
            "pN1-user-driven-prompt-refinement",
            "pN2-user-driven-prompt-organization",
            "pN3-interaction-as-part-of-instruction",
            "pN4-referenced-artifact-as-instruction",
            "pN5-ai-driven-prompt-suggestion",
            "pN6-ai-driven-prompt-decomposition",
            "pN7-generative-prompt-control-widgets",
            "pN8-generative-artifact-control-widgets",
            "pN9-artifact-to-structured-instruction",
            "pN10-artifact-to-multimodal-instruction",
            "pN11-artifact-driven-prompt-enhancement",
            "pN12-interactive-artifact-refinement",
            "pN13-ai-proactively-initiated-interaction",
        ]
        expected_substrates = [
            "text",
            "sketches",
            "raster images",
            "structured data",
            "vector graphics",
        ]
        expected_realizations = [
            "selection",
            "dragging",
            "drawing",
            "annotation",
            "toggling",
            "direct manipulation",
        ]

        self.assertEqual([item["title"] for item in paradigm_cases], expected_titles)
        self.assertEqual(
            [item["videoFile"] for item in paradigm_cases],
            [f"clips/{slug}.mp4" for slug in expected_slugs],
        )
        self.assertEqual(
            [Path(item["historyFile"]).parts[0] for item in paradigm_cases],
            [f"inflak-{slug}" for slug in expected_slugs],
        )
        for item in paradigm_cases:
            run_path = app._confined_file(item["historyFile"]).with_name("run.json")
            run = json.loads(run_path.read_text(encoding="utf-8"))
            expected_storage_path = run_path.parent.relative_to(app.PROJECT_DIR).as_posix()
            self.assertEqual(run["storagePath"], expected_storage_path)
        self.assertEqual(payload["facets"]["artifactSubstrates"], expected_substrates)
        self.assertEqual(payload["facets"]["interactionRealizations"], expected_realizations)
        self.assertEqual(
            {value for item in payload["cases"] for value in item["artifactSubstrates"]},
            set(expected_substrates),
        )
        self.assertEqual(
            {value for item in payload["cases"] for value in item["interactionRealizations"]},
            set(expected_realizations),
        )


    def test_pages_build_uses_static_relative_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "site"
            build_pages.build(output_dir)

            html = (output_dir / "index.html").read_text(encoding="utf-8")
            javascript = (output_dir / "gallery.js").read_text(encoding="utf-8")
            catalog = json.loads((output_dir / "data" / "catalog.json").read_text(encoding="utf-8"))

            self.assertIn('href="./gallery.css?v=20260902"', html)
            self.assertIn('src="./assets/inflak-logo.png"', html)
            self.assertIn('fetch("./data/catalog.json")', javascript)
            self.assertNotIn("/api/gallery/cases", javascript)
            for item in catalog["cases"]:
                self.assertTrue(item["videoUrl"].startswith("./data/gallery_cases/"))
                self.assertTrue(item["historyUrl"].startswith("./data/gallery_cases/"))
                self.assertTrue((output_dir / item["videoUrl"]).is_file())
                self.assertTrue((output_dir / item["historyUrl"]).is_file())


if __name__ == "__main__":
    unittest.main()
