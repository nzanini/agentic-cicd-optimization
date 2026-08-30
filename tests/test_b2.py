"""Unit tests for B2. Do not change B0/B1 behavior or S01–S14."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agentic_cicd.b0.graph import JOBS
from agentic_cicd.b1.cache import warm_cache
from agentic_cicd.b1.planner import DECISION_RUN, JobDecision, Plan, plan_jobs
from agentic_cicd.b2.agent import parse_proposal
from agentic_cicd.b2.policy import decide_invocation
from agentic_cicd.b2.prompts import SYSTEM_PROMPT, format_user_prompt
from agentic_cicd.b2.provider import FakeProvider, LLMResponse, ProviderError, completion_body
from agentic_cicd.b2.runner import record_from_result, run_b2
from agentic_cicd.b2.schema import (
    ProposalError,
    expand_copy_b1,
    proposal_template,
    validate_proposal,
)
from agentic_cicd.b2.settings import B2Settings, load_settings
from agentic_cicd.b2.tools import Toolbelt, ToolError, resolve_readable
from agentic_cicd.b2.verifier import verify_proposal

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "fixtures"
FEATURE_DEV = [
    "branch_guard",
    "validate",
    "test",
    "ingest",
    "prepare",
    "score",
    "evaluate",
    "package",
    "publish",
]


def _settings(**kwargs) -> B2Settings:
    return B2Settings(
        disabled=kwargs.get("disabled", False),
        api_key=kwargs.get("api_key", "test-key"),
        base_url="https://example.invalid/v1",
        model="fake-b2",
        min_confidence=kwargs.get("min_confidence", 0.7),
        min_save=kwargs.get("min_save", 5),
        timeout_s=1.0,
        max_tool_rounds=3,
        enable_tools=kwargs.get("enable_tools", True),
    )


def _offline() -> B2Settings:
    return _settings(api_key=None)


def _proposal(
    overrides: dict | None = None,
    *,
    uncertain: bool = False,
    edges: list | None = None,
    confidence: float = 0.9,
    evidence: bool = True,
) -> dict:
    jobs = []
    for name in JOBS:
        item = {
            "job": name,
            "decision": "RUN",
            "reason_code": "test",
            "reason": "unit test",
            "confidence": confidence,
            "dependencies_considered": [],
            "artifacts_required": [],
            "artifacts_reused": [],
            "evidence": [{"type": "test", "path": "x", "detail": "unit"}] if evidence else [],
        }
        spec = (overrides or {}).get(name)
        if isinstance(spec, str):
            item["decision"] = spec
        elif isinstance(spec, dict):
            item.update(spec)
        jobs.append(item)
    return {
        "schema_version": 1,
        "kind": "b2_proposal",
        "uncertain": uncertain,
        "notes": "",
        "discovered_edges": edges or [],
        "jobs": jobs,
    }


def _plan(tmp_path: Path, changed: list[str] | None, *, warm: bool = True) -> Plan:
    cache = tmp_path / "cache"
    if warm:
        warm_cache(FIXTURES, cache)
    return plan_jobs(
        source="feature",
        target="development",
        changed_paths=changed,
        fixtures_dir=FIXTURES,
        cache_dir=cache if warm else None,
        registry_dir=tmp_path / "registry",
    )


def _verify(tmp_path: Path, plan: Plan, proposal: dict, changed: list[str] | None, **kwargs):
    cache = tmp_path / "cache"
    if not cache.exists():
        warm_cache(FIXTURES, cache)
    return verify_proposal(
        b1=plan,
        proposal=proposal,
        fallback_reason=None,
        source="feature",
        target="development",
        changed_paths=changed,
        fixtures_dir=FIXTURES,
        cache_dir=kwargs.get("cache_dir", cache),
        registry_dir=tmp_path / "registry",
        workspace=kwargs.get("workspace"),
        repo=kwargs.get("repo", REPO),
        min_confidence=kwargs.get("min_confidence", 0.7),
    )


def _run(
    tmp_path: Path,
    changed: list[str] | None,
    *,
    source: str = "feature",
    target: str = "development",
    settings: B2Settings | None = None,
    provider: FakeProvider | None = None,
    workspace: Path | None = None,
    warm: bool = True,
    name: str = "b2",
):
    cache = tmp_path / "cache"
    if warm:
        warm_cache(FIXTURES, cache)
    return run_b2(
        source=source,
        target=target,
        fixtures_dir=FIXTURES,
        work_dir=tmp_path / name,
        registry_dir=tmp_path / "registry",
        changed_paths=changed,
        cache_dir=cache if warm else None,
        workspace_dir=workspace or tmp_path / "ws",
        repo_dir=REPO,
        settings=settings if settings is not None else _offline(),
        provider=provider,
    )


def _executed(result) -> list[str]:
    return [job.job_name for job in result.jobs if job.status == "executed"]


def test_valid_proposal_schema() -> None:
    payload = validate_proposal(_proposal({"branch_guard": "RUN", "score": "SKIP"}))
    assert payload["kind"] == "b2_proposal"
    assert {item["job"] for item in payload["jobs"]} == set(JOBS)


def test_malformed_proposal_rejected() -> None:
    with pytest.raises(ProposalError):
        validate_proposal("just run score")
    with pytest.raises(ProposalError):
        validate_proposal({"kind": "note", "schema_version": 1, "uncertain": False, "jobs": []})


def test_unknown_job_rejected() -> None:
    raw = _proposal()
    raw["jobs"].append(
        {
            "job": "deploy_prod",
            "decision": "SKIP",
            "confidence": 0.9,
            "evidence": [{"type": "x", "path": "", "detail": ""}],
        }
    )
    with pytest.raises(ProposalError, match="unknown"):
        validate_proposal(raw)


def test_missing_job_rejected() -> None:
    raw = _proposal()
    raw["jobs"] = [item for item in raw["jobs"] if item["job"] != "score"]
    with pytest.raises(ProposalError, match="missing"):
        validate_proposal(raw)


def test_unsupported_skip_inert_unknown(tmp_path: Path) -> None:
    plan = _plan(tmp_path, ["unknown/orphan.dat"])
    overrides = {name: "SKIP" for name in JOBS}
    overrides["branch_guard"] = "RUN"
    result = _verify(tmp_path, plan, _proposal(overrides), ["unknown/orphan.dat"])
    assert result.plan.run == plan.run
    assert any(event.job == "score" for event in result.rejected_novel)
    assert result.accepted_novel == []


def test_producer_consumer_forces_run(tmp_path: Path) -> None:
    plan = _plan(tmp_path, ["unknown/orphan.dat"])
    proposal = _proposal({"ingest": "SKIP", "prepare": "RUN", "score": "RUN"})
    result = _verify(tmp_path, plan, proposal, ["unknown/orphan.dat"])
    assert "ingest" in result.plan.run
    assert any(event.job == "ingest" for event in result.rejected_novel)


def test_valid_cache_reuse(tmp_path: Path) -> None:
    base = _plan(tmp_path, ["README.md"])
    forced = Plan(
        flow=base.flow,
        promote_mode=base.promote_mode,
        run=["branch_guard", "ingest"],
        decisions=[
            JobDecision(item.job_name, DECISION_RUN, "forced", "test")
            if item.job_name == "ingest"
            else item
            for item in base.decisions
        ],
        components=base.components,
        invalidated=(),
    )
    proposal = _proposal(
        {
            "ingest": {
                "decision": "SKIP",
                "artifacts_reused": ["raw_dataset"],
                "evidence": [{"type": "cache", "path": "", "detail": "identity"}],
            }
        }
    )
    result = _verify(tmp_path, forced, proposal, ["README.md"])
    assert "ingest" not in result.plan.run
    assert any(event.job == "ingest" for event in result.accepted_novel)


def test_stale_cache_rejected(tmp_path: Path) -> None:
    base = _plan(tmp_path, ["README.md"], warm=False)
    forced = Plan(
        flow=base.flow,
        promote_mode=base.promote_mode,
        run=["branch_guard", "ingest"],
        decisions=[
            JobDecision(item.job_name, DECISION_RUN, "forced", "test")
            if item.job_name == "ingest"
            else item
            for item in base.decisions
        ],
        components=base.components,
        invalidated=(),
    )
    proposal = _proposal(
        {
            "ingest": {
                "decision": "SKIP",
                "artifacts_reused": ["raw_dataset"],
                "evidence": [{"type": "cache", "path": "", "detail": "identity"}],
            }
        }
    )
    result = _verify(tmp_path, forced, proposal, ["README.md"], cache_dir=None)
    assert "ingest" in result.plan.run
    assert any(event.job == "ingest" for event in result.rejected_novel)


def test_low_confidence_rejected(tmp_path: Path) -> None:
    plan = _plan(tmp_path, ["unknown/orphan.dat"])
    result = _verify(
        tmp_path,
        plan,
        _proposal({"score": "SKIP"}, confidence=0.2),
        ["unknown/orphan.dat"],
    )
    assert "score" in result.plan.run
    assert any("confidence" in event.reason for event in result.rejected_novel)


def test_uncertain_proposal_keeps_b1(tmp_path: Path) -> None:
    plan = _plan(tmp_path, ["unknown/orphan.dat"])
    result = _verify(
        tmp_path,
        plan,
        _proposal({"score": "SKIP"}, uncertain=True),
        ["unknown/orphan.dat"],
    )
    assert result.plan.run == plan.run
    assert result.fallback_reason == "uncertain_proposal"


def test_branch_guard_cannot_be_skipped(tmp_path: Path) -> None:
    plan = _plan(tmp_path, ["unknown/orphan.dat"])
    result = _verify(
        tmp_path,
        plan,
        _proposal({"branch_guard": "SKIP"}),
        ["unknown/orphan.dat"],
    )
    assert "branch_guard" in result.plan.run


def test_illegal_flow_does_not_invoke(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        ["README.md"],
        source="feature",
        target="main",
        settings=_settings(),
        provider=FakeProvider(proposal=_proposal()),
    )
    record = record_from_result(result)
    assert record["agent_invoked"] is False
    assert record["invocation_reason_code"] == "illegal_flow"
    assert result.status == "failed"
    assert [job.job_name for job in result.jobs if job.status == "failed"] == ["branch_guard"]


def test_agent_not_invoked_when_b1_sufficient(tmp_path: Path) -> None:
    result = _run(
        tmp_path,
        ["README.md"],
        settings=_settings(),
        provider=FakeProvider(proposal=_proposal({name: "SKIP" for name in JOBS})),
    )
    record = record_from_result(result)
    assert record["agent_invoked"] is False
    assert record["invocation_reason_code"] == "b1_sufficient"
    assert _executed(result) == ["branch_guard"]


def test_api_failure_falls_back_to_b1(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    (workspace / "unknown").mkdir(parents=True)
    (workspace / "unknown" / "orphan.dat").write_text("x", encoding="utf-8")
    result = _run(
        tmp_path,
        ["unknown/orphan.dat"],
        settings=_settings(),
        provider=FakeProvider(error=ProviderError("unavailable", "api down")),
        workspace=workspace,
    )
    record = record_from_result(result)
    assert record["agent_invoked"] is True
    assert record["fallback_reason"] == "unavailable"
    assert _executed(result) == FEATURE_DEV


def test_timeout_falls_back_to_b1(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    (workspace / "unknown").mkdir(parents=True)
    (workspace / "unknown" / "orphan.dat").write_text("x", encoding="utf-8")
    result = _run(
        tmp_path,
        ["unknown/orphan.dat"],
        settings=_settings(),
        provider=FakeProvider(error=ProviderError("timeout", "deadline")),
        workspace=workspace,
        name="timeout",
    )
    assert record_from_result(result)["fallback_reason"] == "timeout"
    assert _executed(result) == FEATURE_DEV


def test_malformed_response_falls_back_to_b1(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    (workspace / "unknown").mkdir(parents=True)
    (workspace / "unknown" / "orphan.dat").write_text("x", encoding="utf-8")
    result = _run(
        tmp_path,
        ["unknown/orphan.dat"],
        settings=_settings(),
        provider=FakeProvider(content="I think you should skip score."),
        workspace=workspace,
        name="malformed",
    )
    record = record_from_result(result)
    assert record["fallback_reason"] == "malformed"
    assert _executed(result) == FEATURE_DEV


def test_offline_does_not_invoke(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    (workspace / "unknown").mkdir(parents=True)
    (workspace / "unknown" / "orphan.dat").write_text("x", encoding="utf-8")
    result = _run(tmp_path, ["unknown/orphan.dat"], workspace=workspace)
    record = record_from_result(result)
    assert record["agent_invoked"] is False
    assert record["invocation_reason_code"] == "offline"
    assert _executed(result) == FEATURE_DEV


def test_localized_import_edge_can_novel_accept(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    script = workspace / "scripts" / "tune_weights.py"
    script.parent.mkdir(parents=True)
    script.write_text("import agentic_cicd.ranker.score\n", encoding="utf-8")
    plan = _plan(tmp_path, ["scripts/tune_weights.py"])
    assert plan.run == FEATURE_DEV
    localized_skip = {name: "SKIP" for name in ("ingest", "prepare", "promote")}
    proposal = _proposal(
        localized_skip,
        edges=[
            {
                "from_path": "scripts/tune_weights.py",
                "to_component": "score_code",
                "via": "import",
                "evidence": [
                    {
                        "type": "import",
                        "path": "scripts/tune_weights.py",
                        "detail": "imports agentic_cicd.ranker.score",
                    }
                ],
            }
        ],
    )
    result = _verify(
        tmp_path,
        plan,
        proposal,
        ["scripts/tune_weights.py"],
        workspace=workspace,
        repo=REPO,
    )
    assert "ingest" not in result.plan.run
    assert "score" in result.plan.run
    assert any(event.job == "ingest" for event in result.accepted_novel)


def test_kill_switch_does_not_invoke(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    (workspace / "unknown").mkdir(parents=True)
    (workspace / "unknown" / "orphan.dat").write_text("x", encoding="utf-8")
    result = _run(
        tmp_path,
        ["unknown/orphan.dat"],
        settings=_settings(disabled=True),
        provider=FakeProvider(proposal=_proposal()),
        workspace=workspace,
    )
    assert record_from_result(result)["invocation_reason_code"] == "disabled"
    assert record_from_result(result)["agent_invoked"] is False


def test_policy_machine_readable(tmp_path: Path) -> None:
    plan = _plan(tmp_path, ["README.md"])
    decision = decide_invocation(
        plan,
        changed_paths=["README.md"],
        settings=_settings(),
        workspace=tmp_path,
        repo=REPO,
    )
    assert decision.invoke is False
    assert decision.reason_code == "b1_sufficient"


def test_tool_jail_blocks_secrets(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("B2_API_KEY=secret", encoding="utf-8")
    with pytest.raises(ToolError):
        resolve_readable(".env", [tmp_path])


def test_inspect_b1_plan_is_read_only(tmp_path: Path) -> None:
    plan = _plan(tmp_path, ["README.md"])
    tools = Toolbelt(
        plan=plan,
        fixtures_dir=FIXTURES,
        cache_dir=tmp_path / "cache",
        registry_dir=tmp_path / "registry",
        workspace=tmp_path,
        repo=REPO,
        diffs={},
    )
    payload = tools.inspect_b1_plan()
    assert payload["run"] == ["branch_guard"]
    classified = tools.dispatch("classify_path", {"path": "README.md"})
    assert classified["component"] == "documentation"


def test_local_settings_available_without_key() -> None:
    settings = load_settings({"B2_BASE_URL": "http://127.0.0.1:11434/v1", "B2_MODEL": "qwen2.5:3b"})
    assert settings.local is True
    assert settings.available is True
    assert settings.api_key is None
    assert settings.auth_token == "local"
    assert settings.model == "qwen2.5:3b"
    assert settings.enable_tools is False


def test_hosted_url_without_key_is_offline() -> None:
    settings = load_settings({})
    assert settings.local is False
    assert settings.available is False
    assert settings.model == "gpt-4o-mini"


def test_local_runtime_unavailable_falls_back_to_b1(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    (workspace / "unknown").mkdir(parents=True)
    (workspace / "unknown" / "orphan.dat").write_text("x", encoding="utf-8")
    settings = B2Settings(
        disabled=False,
        api_key=None,
        base_url="http://127.0.0.1:59999/v1",
        model="qwen2.5:3b",
        min_confidence=0.7,
        min_save=5,
        timeout_s=1.0,
        max_tool_rounds=2,
        enable_tools=False,
    )
    result = _run(
        tmp_path,
        ["unknown/orphan.dat"],
        settings=settings,
        workspace=workspace,
        name="local-down",
    )
    record = record_from_result(result)
    assert record["agent_invoked"] is False
    assert record["invocation_reason_code"] == "offline"
    assert record["local"] is True
    assert record["api_cost_usd"] == 0.0
    assert _executed(result) == FEATURE_DEV


def test_local_valid_proposal_can_novel_accept(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    script = workspace / "scripts" / "tune_weights.py"
    script.parent.mkdir(parents=True)
    script.write_text("import agentic_cicd.ranker.score\n", encoding="utf-8")
    settings = B2Settings(
        disabled=False,
        api_key="unused",
        base_url="https://example.invalid/v1",
        model="fake-b2",
        min_confidence=0.7,
        min_save=5,
        timeout_s=1.0,
        max_tool_rounds=2,
        enable_tools=True,
    )
    overrides = {name: "SKIP" for name in ("ingest", "prepare", "promote")}
    proposal = _proposal(
        overrides,
        edges=[
            {
                "from_path": "scripts/tune_weights.py",
                "to_component": "score_code",
                "via": "import",
                "evidence": [
                    {
                        "type": "import",
                        "path": "scripts/tune_weights.py",
                        "detail": "imports agentic_cicd.ranker.score",
                    }
                ],
            }
        ],
    )
    result = _run(
        tmp_path,
        ["scripts/tune_weights.py"],
        settings=settings,
        provider=FakeProvider(proposal=proposal),
        workspace=workspace,
        name="local-accept",
    )
    record = record_from_result(result)
    assert record["agent_invoked"] is True
    assert any(event["job"] == "ingest" for event in record["novel_accept"])
    assert "score" in record["final_executed_jobs"]
    assert "ingest" not in record["final_executed_jobs"]


def test_local_unsafe_proposal_is_novel_reject(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    (workspace / "unknown").mkdir(parents=True)
    (workspace / "unknown" / "orphan.dat").write_text("x", encoding="utf-8")
    overrides = {name: "SKIP" for name in JOBS}
    overrides["branch_guard"] = "RUN"
    result = _run(
        tmp_path,
        ["unknown/orphan.dat"],
        settings=_settings(),
        provider=FakeProvider(proposal=_proposal(overrides)),
        workspace=workspace,
        name="local-reject",
    )
    record = record_from_result(result)
    assert record["agent_invoked"] is True
    assert record["novel_reject"]
    assert _executed(result) == FEATURE_DEV


def test_copy_b1_expands_omitted_jobs() -> None:
    raw = {
        "schema_version": 1,
        "kind": "b2_proposal",
        "uncertain": False,
        "copy_b1": True,
        "jobs": [{"job": "score", "decision": "RUN"}],
    }
    payload = validate_proposal(expand_copy_b1(raw))
    assert {item["job"] for item in payload["jobs"]} == set(JOBS)
    assert all(item["decision"] in {"RUN", "SKIP"} for item in payload["jobs"])


def test_copy_b1_fills_missing_decision_as_run() -> None:
    raw = {
        "schema_version": 1,
        "kind": "b2_proposal",
        "uncertain": False,
        "copy_b1": True,
        "jobs": [{"job": "test"}],
    }
    payload = validate_proposal(raw)
    by_job = {item["job"]: item["decision"] for item in payload["jobs"]}
    assert by_job["test"] == "RUN"
    assert set(by_job) == set(JOBS)


def test_partial_jobs_without_copy_b1_remain_invalid() -> None:
    raw = {
        "schema_version": 1,
        "kind": "b2_proposal",
        "uncertain": False,
        "jobs": [{"job": "score", "decision": "RUN"}],
    }
    with pytest.raises(ProposalError, match="missing"):
        validate_proposal(raw)


def test_proposal_template_is_valid() -> None:
    payload = validate_proposal(proposal_template())
    assert payload["schema_version"] == 1
    assert payload["kind"] == "b2_proposal"


def test_parse_proposal_extracts_fenced_and_wrapped_json() -> None:
    text = json.dumps(_proposal())
    fenced = parse_proposal(f"```json\n{text}\n```")
    wrapped = parse_proposal(f"Here is the plan:\n{text}\nend")
    assert fenced["schema_version"] == 1
    assert wrapped["kind"] == "b2_proposal"


def test_parse_proposal_rejects_prose() -> None:
    with pytest.raises(ProposalError, match="non-JSON"):
        parse_proposal("I think you should skip score.")


def test_user_prompt_states_schema_contract() -> None:
    text = format_user_prompt(
        {
            "source": "feature",
            "target": "development",
            "changed_paths": ["scripts/tune_weights.py"],
            "b1_plan": {"run": FEATURE_DEV, "decisions": []},
            "unclassified_previews": [
                {"path": "scripts/tune_weights.py", "content": "import agentic_cicd.ranker.score"}
            ],
        }
    )
    assert '"schema_version":1' in text
    assert "b2_proposal" in text
    assert "unclassified_previews" in text
    assert "copy_b1" in SYSTEM_PROMPT
    assert "confidence" in SYSTEM_PROMPT
    assert "evidence" in SYSTEM_PROMPT


def test_json_object_request_body() -> None:
    with_json = completion_body("qwen2.5:3b", [], [], True)
    assert with_json["response_format"] == {"type": "json_object"}
    with_tools = completion_body("qwen2.5:3b", [], [{"type": "function"}], False)
    assert "response_format" not in with_tools


def test_schema_repair_recovers_valid_proposal(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    (workspace / "unknown").mkdir(parents=True)
    (workspace / "unknown" / "orphan.dat").write_text("x", encoding="utf-8")
    bad = _proposal()
    bad["schema_version"] = 2
    result = _run(
        tmp_path,
        ["unknown/orphan.dat"],
        settings=_settings(),
        provider=FakeProvider(
            tool_script=[
                LLMResponse(content=json.dumps(bad)),
                LLMResponse(content=json.dumps(_proposal())),
            ]
        ),
        workspace=workspace,
        name="repair",
    )
    record = record_from_result(result)
    assert record["proposal"] is not None
    assert record["repair_attempted"] is True
    assert record["fallback_reason"] is None
    assert _executed(result) == FEATURE_DEV


def test_copy_b1_empty_jobs_is_accepted_as_proposal(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    (workspace / "unknown").mkdir(parents=True)
    (workspace / "unknown" / "orphan.dat").write_text("x", encoding="utf-8")
    compact = {
        "schema_version": 1,
        "kind": "b2_proposal",
        "uncertain": False,
        "copy_b1": True,
        "jobs": [],
    }
    result = _run(
        tmp_path,
        ["unknown/orphan.dat"],
        settings=_settings(),
        provider=FakeProvider(content=json.dumps(compact)),
        workspace=workspace,
        name="copy-b1",
    )
    record = record_from_result(result)
    assert record["proposal"] is not None
    assert record["fallback_reason"] is None
    assert _executed(result) == FEATURE_DEV


def test_schema_repair_still_rejects_second_malformed(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    (workspace / "unknown").mkdir(parents=True)
    (workspace / "unknown" / "orphan.dat").write_text("x", encoding="utf-8")
    result = _run(
        tmp_path,
        ["unknown/orphan.dat"],
        settings=_settings(),
        provider=FakeProvider(content="still not json"),
        workspace=workspace,
        name="repair-fail",
    )
    record = record_from_result(result)
    assert record["fallback_reason"] == "malformed"
    assert record["repair_attempted"] is True
    assert record["proposal"] is None
    assert _executed(result) == FEATURE_DEV
