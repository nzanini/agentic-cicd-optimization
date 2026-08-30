"""Apply simulated repository changes to an isolated workspace."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from agentic_cicd.ranker.io_util import read_json, write_json


def materialize_workspace(repo_root: Path, dest: Path) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    shutil.copytree(repo_root / "fixtures", dest / "fixtures")
    shutil.copytree(repo_root / "configs", dest / "configs")
    return dest


def apply_changes(workspace: Path, ops: list[dict[str, Any]]) -> None:
    for op in ops:
        kind = op.get("op")
        if kind == "write":
            path = workspace / str(op["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(str(op["text"]), encoding="utf-8")
        elif kind == "set_movie_title":
            catalog_path = workspace / "fixtures" / "catalog.json"
            catalog = read_json(catalog_path)
            found = False
            for item in catalog["items"]:
                if item["id"] == op["movie_id"]:
                    item["title"] = op["title"]
                    found = True
                    break
            if not found:
                msg = f"movie {op['movie_id']} not in catalog"
                raise ValueError(msg)
            write_json(catalog_path, catalog)
        elif kind == "set_model_genre_weight":
            model_path = workspace / "fixtures" / "model" / "ranker.json"
            model = read_json(model_path)
            model["genre_weights"][op["genre"]] = float(op["value"])
            write_json(model_path, model)
        elif kind == "set_year_weight":
            overlay_path = workspace / "configs" / "scoring_weights.json"
            overlay = read_json(overlay_path)
            overlay["year_weight"] = float(op["value"])
            write_json(overlay_path, overlay)
        elif kind == "set_overlay_genre_weight":
            overlay_path = workspace / "configs" / "scoring_weights.json"
            overlay = read_json(overlay_path)
            weights = dict(overlay.get("genre_weights") or {})
            weights[op["genre"]] = float(op["value"])
            overlay["genre_weights"] = weights
            write_json(overlay_path, overlay)
        elif kind == "set_pipeline_description":
            pipeline_path = workspace / "configs" / "pipeline.json"
            pipeline = read_json(pipeline_path)
            pipeline["description"] = str(op["text"])
            write_json(pipeline_path, pipeline)
        else:
            msg = f"unknown apply op: {kind}"
            raise ValueError(msg)


def changed_paths_from_apply(ops: list[dict[str, Any]]) -> list[str]:
    """Physical paths touched by apply ops. Not a scenario-id lookup."""
    paths: list[str] = []
    for op in ops:
        kind = op.get("op")
        if kind == "write":
            paths.append(str(op["path"]))
        elif kind == "set_movie_title":
            paths.append("fixtures/catalog.json")
        elif kind == "set_model_genre_weight":
            paths.append("fixtures/model/ranker.json")
        elif kind == "set_year_weight":
            paths.append("configs/scoring_weights.json")
        elif kind == "set_overlay_genre_weight":
            paths.append("configs/scoring_weights.json")
        elif kind == "set_pipeline_description":
            paths.append("configs/pipeline.json")
    return paths


def change_set(files_changed: list[str], ops: list[dict[str, Any]]) -> list[str]:
    """Declared change class plus apply-touched paths. Conservative union."""
    seen: list[str] = []
    for path in [*files_changed, *changed_paths_from_apply(ops)]:
        if path not in seen:
            seen.append(path)
    return seen
