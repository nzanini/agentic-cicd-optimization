"""Frozen weighted-genre ranker. No training, no randomness."""

from __future__ import annotations

from typing import Any

SCORE_DECIMALS = 6


def _movie_score(movie: dict[str, Any], prefs: dict[str, float], model: dict[str, Any]) -> float:
    weights: dict[str, float] = model["genre_weights"]
    genre_score = 0.0
    for genre, active in movie["genre_vector"].items():
        if not active:
            continue
        genre_score += float(prefs.get(genre, 0.0)) * float(weights.get(genre, 1.0))
    year_term = float(model.get("year_weight", 0.0)) * (
        int(movie["year"]) - int(model.get("reference_year", 0))
    )
    return round(genre_score + year_term, SCORE_DECIMALS)


def rank_catalog(
    prepared: list[dict[str, Any]],
    personas: dict[str, Any],
    model: dict[str, Any],
) -> dict[str, Any]:
    top_n = int(model["top_n"])
    rankings: dict[str, list[dict[str, Any]]] = {}
    for persona in sorted(personas["personas"], key=lambda p: p["id"]):
        scored: list[tuple[float, str, dict[str, Any]]] = []
        for movie in prepared:
            score = _movie_score(movie, persona["genre_prefs"], model)
            scored.append((score, movie["id"], movie))
        scored.sort(key=lambda row: (-row[0], row[1]))
        rankings[persona["id"]] = [
            {
                "rank": i + 1,
                "movie_id": movie["id"],
                "title": movie["title"],
                "score": score,
            }
            for i, (score, _mid, movie) in enumerate(scored[:top_n])
        ]
    return {"top_n": top_n, "rankings": rankings}
