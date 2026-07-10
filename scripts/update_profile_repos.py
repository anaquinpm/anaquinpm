#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
README_PATH = ROOT / "README.md"
START_MARKER = "<!-- START_SECTION:repositories -->"
END_MARKER = "<!-- END_SECTION:repositories -->"


def fetch_repositories(username: str, count: int) -> list[dict]:
    url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
    req = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-readme-updater",
        },
    )
    with urlopen(req, timeout=20) as response:
        data = json.load(response)

    repos = []
    for repo in data:
        if repo.get("private") or repo.get("fork"):
            continue
        repos.append(repo)

    return repos[:count]


def build_table(repositories: list[dict]) -> str:
    lines = [
        "| Repository | Description | Topics |",
        "|:---|:---|:---|",
    ]

    for repo in repositories:
        name = repo["name"]
        full_name = repo["full_name"]
        description = (repo.get("description") or "No description provided").replace("|", "\\|")
        topics = ", ".join(repo.get("topics", [])) if repo.get("topics") else "—"
        lines.append(f"| **[{name}]({repo['html_url']})** | {description} | {topics} |")

    return "\n".join(lines)


def update_readme(readme_path: Path, repositories: list[dict]) -> None:
    content = readme_path.read_text(encoding="utf-8")

    if START_MARKER not in content or END_MARKER not in content:
        raise SystemExit("README markers not found")

    block = f"{START_MARKER}\n{build_table(repositories)}\n{END_MARKER}"
    updated = re.sub(
        rf"{re.escape(START_MARKER)}.*?{re.escape(END_MARKER)}",
        block,
        content,
        flags=re.S,
    )
    readme_path.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    username = os.environ.get("GITHUB_USERNAME", "anaquinpm")
    count = int(os.environ.get("REPO_COUNT", "6"))

    try:
        repositories = fetch_repositories(username, count)
    except Exception as exc:
        print(f"Unable to fetch repositories: {exc}", file=sys.stderr)
        repositories = []

    update_readme(README_PATH, repositories)
