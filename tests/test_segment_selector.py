import unittest

from segment_selector import is_starred, select_segments


def segment(name, start, end, starred=False):
    return {
        "name": name,
        "start_index": start,
        "end_index": end,
        "starred": starred,
    }


class SegmentSelectorTest(unittest.TestCase):
    def test_is_starred_normalizes_boolean_strings(self):
        self.assertTrue(is_starred({"starred": "true"}))
        self.assertFalse(is_starred({"starred": "false"}))

    def test_regular_segment_overlapping_starred_segment_is_discarded(self):
        segments = [
            segment("普通短赛段", 20, 40),
            segment("收藏长赛段", 10, 50, starred=True),
            segment("后续赛段", 60, 80),
        ]

        selected = select_segments(segments)

        self.assertEqual(
            ["收藏长赛段", "后续赛段"],
            [item["name"] for item in selected],
        )

    def test_longer_regular_segment_wins_when_ranges_overlap(self):
        segments = [
            segment("路线型长赛段", 0, 100),
            segment("具体爬坡", 20, 40),
        ]

        selected = select_segments(segments)

        self.assertEqual(["路线型长赛段"], [item["name"] for item in selected])

    def test_all_overlapping_starred_segments_are_retained(self):
        segments = [
            segment("收藏长赛段", 0, 100, starred=True),
            segment("收藏短赛段", 20, 40, starred=True),
            segment("普通赛段", 50, 70),
        ]

        selected = select_segments(segments)

        self.assertEqual(
            ["收藏长赛段", "收藏短赛段"],
            [item["name"] for item in selected],
        )

    def test_regular_segment_inside_starred_segment_is_discarded(self):
        segments = [
            segment("收藏赛段", 0, 100, starred=True),
            segment("内部普通赛段", 20, 40),
        ]

        selected = select_segments(segments)

        self.assertEqual(["收藏赛段"], [item["name"] for item in selected])

    def test_regular_segment_touching_starred_boundary_is_retained(self):
        segments = [
            segment("收藏赛段", 0, 100, starred=True),
            segment("相邻普通赛段", 100, 140),
        ]

        selected = select_segments(segments)

        self.assertEqual(
            ["收藏赛段", "相邻普通赛段"],
            [item["name"] for item in selected],
        )

    def test_longest_non_overlapping_regular_segments_are_retained(self):
        segments = [
            segment("长赛段", 10, 50),
            segment("重叠短赛段", 20, 30),
            segment("不重叠赛段", 60, 90),
        ]

        selected = select_segments(segments)

        self.assertEqual(
            ["长赛段", "不重叠赛段"],
            [item["name"] for item in selected],
        )

    def test_invalid_segments_are_ignored_and_boundaries_may_touch(self):
        segments = [
            segment("第一段", 0, 20),
            segment("第二段", 20, 40),
            segment("", 50, 60),
            segment("索引倒置", 80, 70),
            {"name": "缺索引"},
        ]

        selected = select_segments(segments)

        self.assertEqual(["第一段", "第二段"], [item["name"] for item in selected])

    def test_string_true_is_treated_as_starred(self):
        selected = select_segments(
            [
                segment("普通赛段", 10, 20),
                {**segment("收藏赛段", 0, 30), "starred": "true"},
            ]
        )

        self.assertEqual(["收藏赛段"], [item["name"] for item in selected])


if __name__ == "__main__":
    unittest.main()
