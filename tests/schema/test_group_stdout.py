from muscles.core.schema.group import Group


class _DummyColumn:
    def __init__(self, default=None):
        self.default = default
        self.value = None


class DemoGroup(Group):
    columns = {
        "name": _DummyColumn(default="fallback"),
    }


def test_group_init_does_not_write_to_stdout(capsys):
    DemoGroup(name="Denis")
    captured = capsys.readouterr()
    assert captured.out == ""
