import unittest
from types import SimpleNamespace as NS

from migrate_existing import validate_plan


def plan(**changes):
    result = {
        name: NS(exists=True, resolution="up_to_date", ops=[])
        for name in ("creators", "videos", "video_scenes")
    }
    result.update(changes)
    return result


class MigrationPlanTest(unittest.TestCase):
    def test_allows_only_existing_computed_expression_updates(self):
        op = NS(target="column", op="alter", name="raw_attributes", destructive=False,
                details=NS(value="new expression", previous_value="old expression"))
        validate_plan(plan(videos=NS(exists=True, resolution="update_additive", ops=[op])))
        validate_plan(plan())

    def test_refuses_missing_tables_and_incompatible_types(self):
        for diff in (NS(exists=False, resolution="create", ops=[]),
                     NS(exists=True, resolution="unsupported", ops=[])):
            with self.assertRaises(RuntimeError):
                validate_plan(plan(videos=diff))
        with self.assertRaises(RuntimeError):
            validate_plan({})

    def test_refuses_index_replacement_and_column_addition(self):
        for target, operation in (("index", "drop"), ("index", "add"), ("column", "add")):
            op = NS(target=target, op=operation, name="raw_attributes", destructive=False)
            with self.assertRaises(RuntimeError):
                validate_plan(plan(videos=NS(exists=True, resolution="update_additive", ops=[op])))


if __name__ == "__main__":
    unittest.main()
