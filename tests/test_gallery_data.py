import unittest

import app


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


if __name__ == "__main__":
    unittest.main()
