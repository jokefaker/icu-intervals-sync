import unittest
from pathlib import Path


class DockerfileTest(unittest.TestCase):
    def test_runtime_files_include_segment_selector(self):
        dockerfile = Path(__file__).parents[1].joinpath("Dockerfile").read_text(
            encoding="utf-8"
        )

        self.assertIn("segment_selector.py", dockerfile)
        self.assertIn("strava_segments.py", dockerfile)
        self.assertIn("strava_segments_chart.js", dockerfile)
        self.assertIn("INTERVALS_ICU_ATHLETE_IDS", dockerfile)
        self.assertIn("INTERVALS_ICU_DISCOVER_ATHLETES", dockerfile)


if __name__ == "__main__":
    unittest.main()
