import sys
import gael.testing


def test__add_appsever_import_paths__multiple_calls__only_adds_once():
    components_before_add = len(sys.path)
    gael.testing.add_appsever_import_paths()
    components_after_first_add = len(sys.path)
    gael.testing.add_appsever_import_paths()
    components_after_second_add = len(sys.path)
    assert components_before_add <= components_after_first_add == components_after_second_add
