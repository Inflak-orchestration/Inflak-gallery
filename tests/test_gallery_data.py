import json
import tempfile
import unittest
from pathlib import Path

import app
import build_pages


class GalleryDataTests(unittest.TestCase):
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
