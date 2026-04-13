"""RSS feed adapter."""

from __future__ import annotations

from xml.etree import ElementTree

import httpx


class RssAdapter:
    def __init__(self, *, client: httpx.Client) -> None:
        self._client = client

    def fetch(self, url: str) -> list[dict[str, str]]:
        response = self._client.get(url, timeout=10.0)
        response.raise_for_status()

        root = ElementTree.fromstring(response.text)
        items: list[dict[str, str]] = []
        for item in root.findall(".//item"):
            items.append(
                {
                    "title": item.findtext("title", default=""),
                    "link": item.findtext("link", default=""),
                    "description": item.findtext("description", default=""),
                    "pubDate": item.findtext("pubDate", default=""),
                }
            )
        return items
