"""Run one shell command in a throwaway Databricks Sandbox (Beta).

Sandboxes have ingress closed and their own filesystem and identity (`sandbox-agent`), but
egress is unrestricted, so this shows isolation from the laptop, not from the network.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any, Protocol


class SandboxAPI(Protocol):
    def create_sandbox(self, sandbox: Any, sandbox_id: str) -> Any: ...
    def execute_command_sync(
        self, name: str, cmd: str, *, args: list[str] | None = ..., execution_timeout: Any = ...
    ) -> Any: ...
    def delete_sandbox(self, name: str) -> Any: ...


@dataclass(frozen=True)
class Result:
    exit_code: int
    stdout: str
    stderr: str


def new_sandbox_id() -> str:
    return f"omnigent-talk-{secrets.token_hex(4)}"


def run(api: SandboxAPI, command: str, *, timeout_s: int = 60, keep: bool = False) -> Result:
    """Create a sandbox, run `command` under bash, and delete the sandbox even on failure."""
    from databricks.sdk.service.sandbox import Sandbox
    from google.protobuf.duration_pb2 import Duration

    sandbox_id = new_sandbox_id()
    name = f"sandboxes/{sandbox_id}"
    api.create_sandbox(sandbox=Sandbox(), sandbox_id=sandbox_id)
    try:
        resp = api.execute_command_sync(
            name,
            "/bin/bash",
            args=["-c", command],
            execution_timeout=Duration(seconds=timeout_s),
        )
        return Result(int(resp.exit_code or 0), resp.stdout or "", resp.stderr or "")
    finally:
        if not keep:
            api.delete_sandbox(name)
