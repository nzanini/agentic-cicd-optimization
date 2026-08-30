"""Deterministic feature preparation from the raw catalog."""

from __future__ import annotations

from typing import Any

GENRES = ("action", "comedy", "drama", "romance", "scifi", "thriller")


def prepare_catalog(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for item in catalog["items"]:
        genres = list(item["genres"])
        unknown = [g for g in genres if g not in GENRES]
        if unknown:
            msg = f"unknown genres on {item['id']}: {unknown}"
            raise ValueError(msg)
        prepared.append(
            {
                "id": item["id"],
                "title": item["title"],
                "year": int(item["year"]),
                "genres": sorted(genres),
                "genre_vector": {g: 1.0 if g in genres else 0.0 for g in GENRES},
            }
        )
    return sorted(prepared, key=lambda row: row["id"])
