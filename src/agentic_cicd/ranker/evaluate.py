"""Workload evaluation metrics. These are not CI optimization metrics."""

from __future__ import annotations

from typing import Any

from agentic_cicd.ranker.identity import sha256_canonical


def evaluate_predictions(
    predictions: dict[str, Any],
    prepared: list[dict[str, Any]],
    personas: dict[str, Any],
) -> dict[str, Any]:
    rankings: dict[str, list[dict[str, Any]]] = predictions["rankings"]
    catalog_ids = {row["id"] for row in prepared}
    recommended = {entry["movie_id"] for rows in rankings.values() for entry in rows}
    scores = [entry["score"] for rows in rankings.values() for entry in rows]
    return {
        "catalog_size": len(prepared),
        "persona_count": len(personas["personas"]),
        "top_n": predictions["top_n"],
        "unique_titles_recommended": len(recommended),
        "coverage": round(len(recommended) / len(catalog_ids), 6) if catalog_ids else 0.0,
        "mean_top_score": round(sum(scores) / len(scores), 6) if scores else 0.0,
        "predictions_sha256": sha256_canonical(predictions),
    }
