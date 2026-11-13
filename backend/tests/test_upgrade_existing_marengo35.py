import unittest
from types import SimpleNamespace as NS

from upgrade_existing_marengo35 import validate_plan


def up_to_date():
    return NS(exists=True, resolution="up_to_date", ops=[])


def rebuild(index, drop=True):
    ops = [NS(target="index", op="add", name=index)]
    if drop:
        ops.insert(0, NS(target="index", op="drop", name=index))
    return NS(exists=True, resolution="update_destructive" if drop else "update_additive", ops=ops)


def plan(**changes):
    result = {name: up_to_date() for name in ("creators", "videos", "video_scenes")}
    result.update(changes)
    return result


class UpgradePlanTest(unittest.TestCase):
    def test_allows_rebuilding_the_two_named_indexes(self):
        self.assertTrue(validate_plan(plan(videos=rebuild("title_marengo"), video_scenes=rebuild("scene_marengo"))))

    def test_allows_a_rerun_after_a_stopped_build(self):
        self.assertTrue(validate_plan(plan(video_scenes=rebuild("scene_marengo", drop=False))))

    def test_reports_nothing_to_do_when_up_to_date(self):
        self.assertFalse(validate_plan(plan()))

    def test_refuses_missing_tables_and_other_changes(self):
        with self.assertRaises(RuntimeError):
            validate_plan({})
        with self.assertRaises(RuntimeError):
            validate_plan(plan(videos=NS(exists=False, resolution="create", ops=[])))
        with self.assertRaises(RuntimeError):
            validate_plan(plan(videos=NS(exists=True, resolution="unsupported", ops=[])))
        with self.assertRaises(RuntimeError):
            validate_plan(plan(creators=rebuild("title_marengo")))

    def test_refuses_wrong_index_and_column_changes(self):
        with self.assertRaises(RuntimeError):
            validate_plan(plan(video_scenes=rebuild("title_marengo")))
        column_op = NS(target="column", op="alter", name="scenes")
        with self.assertRaises(RuntimeError):
            validate_plan(plan(videos=NS(exists=True, resolution="update_destructive",
                                         ops=rebuild("title_marengo").ops + [column_op])))


if __name__ == "__main__":
    unittest.main()
