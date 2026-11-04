"""Sync portable Agent Skills bundles into Unity Catalog Skills (Beta)."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote

import httpx

from omnigent_talk import gateway

SKILLS_API = "/api/2.1/unity-catalog/skills"
FILES_API = "/api/2.0/fs/files/Skills"
UC_SCHEMA = "omnigent_talk"
COMMENT_PREFIX = "Managed by omnigent-talk; bundle-sha256="

AuthHeaders = Callable[[], dict[str, str]]
SyncStatus = Literal["created", "updated", "unchanged"]


class SkillsApiError(RuntimeError):
    """An error from the workspace Skills or Files REST API."""


@dataclass(frozen=True)
class BundleFile:
    path: str
    content: bytes


@dataclass(frozen=True)
class SkillBundle:
    bundle_name: str
    skill_id: str
    files: tuple[BundleFile, ...]
    digest: str

    @property
    def comment(self) -> str:
        return f"{COMMENT_PREFIX}{self.digest}"


@dataclass(frozen=True)
class SyncResult:
    bundle_name: str
    skill_id: str
    status: SyncStatus


def _skill_id(bundle_name: str) -> str:
    """Map the hyphenated Agent Skills name to a conservative UC identifier."""
    if not bundle_name or not bundle_name[0].isalpha():
        raise ValueError(f"Invalid skill directory name: {bundle_name!r}")
    if any(not (char.islower() or char.isdigit() or char == "-") for char in bundle_name):
        raise ValueError(f"Invalid skill directory name: {bundle_name!r}")
    return bundle_name.replace("-", "_")


def discover_bundles(skills_root: Path) -> list[SkillBundle]:
    """Read each immediate skill directory and hash every file in upload order."""
    bundles: list[SkillBundle] = []
    for directory in sorted(path for path in skills_root.iterdir() if path.is_dir()):
        if not (directory / "SKILL.md").is_file():
            raise ValueError(f"{directory} has no SKILL.md")
        files = tuple(
            BundleFile(path.relative_to(directory).as_posix(), path.read_bytes())
            for path in sorted(directory.rglob("*"))
            if path.is_file()
        )
        digest = hashlib.sha256()
        for file in files:
            path_bytes = file.path.encode()
            digest.update(len(path_bytes).to_bytes(8))
            digest.update(path_bytes)
            digest.update(len(file.content).to_bytes(8))
            digest.update(file.content)
        bundles.append(
            SkillBundle(directory.name, _skill_id(directory.name), files, digest.hexdigest())
        )
    return bundles


def _response_object(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as error:
        raise SkillsApiError("Skills API returned a non-JSON response") from error
    if not isinstance(payload, dict):
        raise SkillsApiError("Skills API returned a non-object response")
    return payload


def _error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text.strip()[:500]
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict) and error.get("message"):
            return str(error["message"])[:500]
        if payload.get("message"):
            return str(payload["message"])[:500]
    return response.text.strip()[:500]


@dataclass
class SkillsApi:
    """Thin pure-HTTP seam over the UC Skills and Files APIs."""

    host: str
    catalog: str
    auth: AuthHeaders
    client: httpx.Client
    schema: str = UC_SCHEMA

    @property
    def parent(self) -> str:
        return f"schemas/{self.catalog}.{self.schema}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        content: bytes | None = None,
        content_type: str | None = None,
    ) -> httpx.Response:
        headers = self.auth()
        if json_body is not None:
            headers["Content-Type"] = "application/json"
        elif content_type:
            headers["Content-Type"] = content_type
        response = self.client.request(
            method,
            f"{self.host.rstrip('/')}{path}",
            params=params,
            json=json_body,
            content=content,
            headers=headers,
        )
        if not response.is_success:
            detail = _error_detail(response)
            suffix = f": {detail}" if detail else ""
            raise SkillsApiError(f"{method} {path} returned HTTP {response.status_code}{suffix}")
        return response

    def list_skills(self) -> list[dict[str, Any]]:
        skills: list[dict[str, Any]] = []
        page_token = ""
        while True:
            params = {"parent": self.parent, "page_size": "200"}
            if page_token:
                params["page_token"] = page_token
            payload = _response_object(self._request("GET", SKILLS_API, params=params))
            page = payload.get("skills", [])
            if not isinstance(page, list) or not all(isinstance(item, dict) for item in page):
                raise SkillsApiError("Skills API returned an invalid skills list")
            skills.extend(page)
            token = payload.get("next_page_token")
            if not isinstance(token, str) or not token:
                return skills
            page_token = token

    def _resource_path(self, skill_id: str, suffix: str = "") -> str:
        full_name = quote(f"{self.catalog}.{self.schema}.{skill_id}", safe="._-")
        return f"{SKILLS_API}/{full_name}{suffix}"

    def _create(self, bundle: SkillBundle) -> dict[str, Any]:
        response = self._request(
            "POST",
            SKILLS_API,
            params={"parent": self.parent, "skill_id": bundle.skill_id},
            json_body={"comment": bundle.comment},
        )
        return _response_object(response)

    def _upload(self, bundle: SkillBundle, file: BundleFile) -> None:
        namespace = "/".join(
            quote(part, safe="._-") for part in (self.catalog, self.schema, bundle.skill_id)
        )
        relative_path = "/".join(quote(part, safe="._-") for part in file.path.split("/"))
        self._request(
            "PUT",
            f"{FILES_API}/{namespace}/{relative_path}",
            params={"overwrite": "true"},
            content=file.content,
            content_type="application/octet-stream",
        )

    def _finalize(self, bundle: SkillBundle) -> dict[str, Any]:
        return _response_object(
            self._request("POST", self._resource_path(bundle.skill_id, "/finalize"))
        )

    def _record_digest(self, bundle: SkillBundle, finalized: dict[str, Any]) -> None:
        etag = finalized.get("etag")
        if not isinstance(etag, str) or not etag:
            raise SkillsApiError("Finalize response did not contain an etag")
        self._request(
            "PATCH",
            self._resource_path(bundle.skill_id),
            params={"update_mask": "comment", "etag": etag},
            json_body={"comment": bundle.comment},
        )

    @staticmethod
    def _remote_skill_id(skill: dict[str, Any]) -> str:
        name = skill.get("name", "")
        if not isinstance(name, str):
            return ""
        return name.removeprefix("skills/").rsplit(".", 1)[-1]

    @staticmethod
    def _is_unchanged(bundle: SkillBundle, skill: dict[str, Any]) -> bool:
        return (
            skill.get("comment") == bundle.comment
            and skill.get("bundle_name") == bundle.bundle_name
            and bool(skill.get("finalize_time"))
        )

    def sync(self, skills_root: Path, *, dry_run: bool = False) -> list[SyncResult]:
        """Create or update every local bundle, without writing unchanged bundles."""
        remote = {self._remote_skill_id(skill): skill for skill in self.list_skills()}
        results: list[SyncResult] = []
        for bundle in discover_bundles(skills_root):
            existing = remote.get(bundle.skill_id)
            if existing is not None and self._is_unchanged(bundle, existing):
                results.append(SyncResult(bundle.bundle_name, bundle.skill_id, "unchanged"))
                continue

            status: SyncStatus = "created" if existing is None else "updated"
            if not dry_run:
                if existing is None:
                    self._create(bundle)
                for file in bundle.files:
                    self._upload(bundle, file)
                finalized = self._finalize(bundle)
                if existing is not None:
                    self._record_digest(bundle, finalized)
            results.append(SyncResult(bundle.bundle_name, bundle.skill_id, status))
        return results


def connect() -> SkillsApi:
    """Connect using only the profile and catalog selected in .env.local."""
    profile = gateway.require_env("DBX_PROFILE")
    catalog = gateway.require_env("CATALOG")
    host, auth = gateway.workspace_auth(profile)
    return SkillsApi(host, catalog, auth, httpx.Client(timeout=60))
