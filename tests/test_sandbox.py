from types import SimpleNamespace

import pytest

from omnigent_talk import sandbox


class FakeAPI:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, object]] = []

    def create_sandbox(self, sandbox, sandbox_id):
        self.calls.append(("create", sandbox_id))

    def execute_command_sync(self, name, cmd, *, args=None, execution_timeout=None):
        self.calls.append(("exec", (name, cmd, args)))
        if self.fail:
            raise RuntimeError("boom")
        return SimpleNamespace(exit_code=0, stdout="45\n", stderr="")

    def delete_sandbox(self, name):
        self.calls.append(("delete", name))


def test_runs_command_under_bash_and_cleans_up():
    api = FakeAPI()
    result = sandbox.run(api, "echo 45")
    assert result == sandbox.Result(0, "45\n", "")
    sid = api.calls[0][1]
    assert api.calls[1:] == [
        ("exec", (f"sandboxes/{sid}", "/bin/bash", ["-c", "echo 45"])),
        ("delete", f"sandboxes/{sid}"),
    ]


def test_sandbox_is_deleted_when_the_command_fails():
    api = FakeAPI(fail=True)
    with pytest.raises(RuntimeError):
        sandbox.run(api, "false")
    assert api.calls[-1][0] == "delete"
