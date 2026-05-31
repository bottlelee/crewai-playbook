from __future__ import annotations

from pathlib import Path
from typing import Any, Type

from langchain.tools import BaseTool


class FileReadTool(BaseTool):
    name: str = "read_file"
    description: str = "Read the content of a file from the local filesystem. Input: absolute or relative file path."

    def _run(self, file_path: str) -> str:
        p = Path(file_path)
        if not p.exists():
            return f"File not found: {file_path}"
        return p.read_text(encoding="utf-8")

    async def _arun(self, file_path: str) -> str:
        return self._run(file_path)


class FileWriteTool(BaseTool):
    name: str = "write_file"
    description: str = (
        "Write content to a file. Input should be a JSON object with keys "
        'file_path (str), content (str), and optionally directory (str). '
        "If the file_path has a suffix it is treated as a file path; "
        "otherwise it is treated as a directory and a file named output.txt is created inside."
    )

    def _run(self, file_path: str, content: str, directory: str | None = None) -> str:
        if directory:
            dest = Path(directory) / file_path
        else:
            dest = Path(file_path)
        if dest.suffix:
            dest.parent.mkdir(parents=True, exist_ok=True)
        else:
            dest.mkdir(parents=True, exist_ok=True)
            dest = dest / "output.txt"
        dest.write_text(content, encoding="utf-8")
        return f"Content written to {dest}"

    async def _arun(self, file_path: str, content: str, directory: str | None = None) -> str:
        return self._run(file_path, content, directory)


class DirectoryReadTool(BaseTool):
    name: str = "list_directory"
    description: str = "List files and directories in a given path. Input: absolute or relative directory path."

    def _run(self, directory_path: str) -> str:
        p = Path(directory_path)
        if not p.exists() or not p.is_dir():
            return f"Directory not found: {directory_path}"
        items = [str(item) for item in p.iterdir()]
        return "\n".join(items) if items else "(empty directory)"

    async def _arun(self, directory_path: str) -> str:
        return self._run(directory_path)


class WebSearchTool(BaseTool):
    name: str = "web_search"
    description: str = (
        "Search the web for current information using Bing. "
        "Input: a search query string. "
        "Returns top search results with titles, URLs, and snippets."
    )

    def _run(self, query: str) -> str:
        try:
            import re
            import requests

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            }
            resp = requests.get(
                "https://www.bing.com/search",
                params={"q": query, "setlang": "en"},
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            html = resp.text

            results: list[str] = []

            # Split into <li class="b_algo"> blocks
            blocks = re.findall(
                r'<li[^>]*class="b_algo"[^>]*>(.*?)</li>', html, re.DOTALL
            )

            for block in blocks[:5]:
                # Title from <h2><a href="...">title</a></h2>
                h2_match = re.search(
                    r'<h2[^>]*>\s*<a[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>',
                    block, re.DOTALL,
                )
                if not h2_match:
                    continue
                url = h2_match.group(1)
                title = re.sub(r"<[^>]+>", "", h2_match.group(2)).strip()

                # Snippet from <p> tag
                snippet_match = re.search(
                    r'<p[^>]*>(.*?)</p>', block, re.DOTALL
                )
                snippet = ""
                if snippet_match:
                    snippet = re.sub(
                        r"<[^>]+>", "", snippet_match.group(1)
                    ).strip()

                entry = f"**{title}**\n  URL: {url}"
                if snippet:
                    entry += f"\n  {snippet}"
                results.append(entry)

            if results:
                return "\n\n".join(results)
            return f"No results found for: {query}"

        except Exception as exc:
            return f"Search failed: {exc}"

    async def _arun(self, query: str) -> str:
        return self._run(query)


TOOL_REGISTRY: dict[str, BaseTool] = {
    "read_file": FileReadTool(),
    "write_file": FileWriteTool(),
    "list_directory": DirectoryReadTool(),
    "web_search": WebSearchTool(),
}


def resolve_tools(tool_names: list[str] | None) -> list[BaseTool] | None:
    if not tool_names:
        return None
    resolved: list[BaseTool] = []
    for name in tool_names:
        if name in TOOL_REGISTRY:
            resolved.append(TOOL_REGISTRY[name])
    return resolved if resolved else None
