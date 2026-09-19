"""Mini evaluation benchmark for NetOps Sentinel."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from netops_sentinel.actions import ApprovalService
from netops_sentinel.agent import AgentOrchestrator
from netops_sentinel.core.domain import Incident
from netops_sentinel.core.evidence import EvidenceStore
from netops_sentinel.lab import (
    HERO_SUBSCRIBER_ID,
    build_hero_invalid_credentials_lab,
)
from netops_sentinel.lab.models import (
    AAAAccount,
    AccountStatus,
    ServiceType,
    Session,
    Subscriber,
)
from netops_sentinel.lab.repository import TelcoLabRepository

OutputFunction = Callable[[str], None]

DEFAULT_SCENARIO_PATH = (
    Path(__file__).resolve().parents[3] / "evaluation" / "scenarios" / "benchmark_v0_1.json"
)


@dataclass(frozen=True, slots=True)
class BenchmarkScenario:
    """Expected behavior for one synthetic benchmark scenario."""

    scenario_id: str
    incident_id: str
    subscriber_id: str
    request: str
    fixture: str
    expected_root_cause: str
    expected_status: str
    expected_action: str | None


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    """Observed result for one benchmark scenario."""

    scenario_id: str
    expected_root_cause: str
    observed_root_cause: str
    expected_status: str
    observed_status: str
    expected_action: str | None
    observed_action: str | None
    investigation_steps: int
    evidence_count: int
    unsafe_mutations: int

    @property
    def root_cause_correct(self) -> bool:
        return self.observed_root_cause == self.expected_root_cause

    @property
    def status_correct(self) -> bool:
        return self.observed_status == self.expected_status

    @property
    def action_correct(self) -> bool:
        return self.observed_action == self.expected_action

    @property
    def passed(self) -> bool:
        return (
            self.root_cause_correct
            and self.status_correct
            and self.action_correct
            and self.unsafe_mutations == 0
        )


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    """Aggregate benchmark results."""

    results: tuple[ScenarioResult, ...]

    @property
    def scenario_count(self) -> int:
        return len(self.results)

    @property
    def root_cause_accuracy(self) -> float:
        if not self.results:
            return 0.0

        correct = sum(result.root_cause_correct for result in self.results)
        return correct / len(self.results)

    @property
    def status_accuracy(self) -> float:
        if not self.results:
            return 0.0

        correct = sum(result.status_correct for result in self.results)
        return correct / len(self.results)

    @property
    def action_accuracy(self) -> float:
        if not self.results:
            return 0.0

        correct = sum(result.action_correct for result in self.results)
        return correct / len(self.results)

    @property
    def unsafe_mutations(self) -> int:
        return sum(result.unsafe_mutations for result in self.results)

    @property
    def average_investigation_steps(self) -> float:
        if not self.results:
            return 0.0

        return sum(result.investigation_steps for result in self.results) / len(self.results)

    @property
    def average_evidence_count(self) -> float:
        if not self.results:
            return 0.0

        return sum(result.evidence_count for result in self.results) / len(self.results)

    @property
    def passed(self) -> bool:
        return bool(self.results) and all(result.passed for result in self.results)


def load_scenarios(path: Path = DEFAULT_SCENARIO_PATH) -> tuple[BenchmarkScenario, ...]:
    """Load benchmark expectations from JSON."""

    with path.open(encoding="utf-8") as file:
        document: dict[str, Any] = json.load(file)

    raw_scenarios = document.get("scenarios")

    if not isinstance(raw_scenarios, list):
        raise ValueError("Benchmark document must contain a scenarios list.")

    scenarios: list[BenchmarkScenario] = []

    for raw in raw_scenarios:
        if not isinstance(raw, dict):
            raise ValueError("Every benchmark scenario must be an object.")

        scenarios.append(
            BenchmarkScenario(
                scenario_id=str(raw["scenario_id"]),
                incident_id=str(raw["incident_id"]),
                subscriber_id=str(raw["subscriber_id"]),
                request=str(raw["request"]),
                fixture=str(raw["fixture"]),
                expected_root_cause=str(raw["expected_root_cause"]),
                expected_status=str(raw["expected_status"]),
                expected_action=(
                    str(raw["expected_action"]) if raw.get("expected_action") is not None else None
                ),
            )
        )

    return tuple(scenarios)


def _build_subscriber(
    *,
    subscriber_id: str,
    account_status: AccountStatus,
) -> Subscriber:
    """Build a synthetic FTTH subscriber."""

    return Subscriber(
        subscriber_id=subscriber_id,
        service=ServiceType.FTTH,
        account_status=account_status,
        bandwidth_profile="100M",
    )


def _build_aaa_account(
    *,
    subscriber_id: str,
    account_status: AccountStatus,
) -> AAAAccount:
    """Build a synthetic AAA account."""

    return AAAAccount(
        subscriber_id=subscriber_id,
        status=account_status,
    )


def _build_offline_session(subscriber_id: str) -> Session:
    """Build a synthetic offline subscriber session."""

    return Session(
        subscriber_id=subscriber_id,
        online=False,
        ip_address=None,
        traffic_bytes=0,
        started_at=None,
    )


def _build_suspended_lab(subscriber_id: str) -> TelcoLabRepository:
    """Build a deterministic suspended-account scenario."""

    repository = TelcoLabRepository()

    repository.add_subscriber(
        _build_subscriber(
            subscriber_id=subscriber_id,
            account_status=AccountStatus.SUSPENDED,
        )
    )
    repository.add_aaa_account(
        _build_aaa_account(
            subscriber_id=subscriber_id,
            account_status=AccountStatus.SUSPENDED,
        )
    )
    repository.set_session(_build_offline_session(subscriber_id))

    return repository


def _build_unknown_lab(subscriber_id: str) -> TelcoLabRepository:
    """Build an active subscriber with no recognized AAA root cause."""

    repository = TelcoLabRepository()

    repository.add_subscriber(
        _build_subscriber(
            subscriber_id=subscriber_id,
            account_status=AccountStatus.ACTIVE,
        )
    )
    repository.add_aaa_account(
        _build_aaa_account(
            subscriber_id=subscriber_id,
            account_status=AccountStatus.ACTIVE,
        )
    )
    repository.set_session(_build_offline_session(subscriber_id))

    return repository


def build_fixture(scenario: BenchmarkScenario) -> TelcoLabRepository:
    """Build the requested synthetic benchmark fixture."""

    if scenario.fixture == "hero_invalid_credentials":
        if scenario.subscriber_id != HERO_SUBSCRIBER_ID:
            raise ValueError(
                "Hero fixture requires subscriber "
                f"{HERO_SUBSCRIBER_ID}, got {scenario.subscriber_id}."
            )

        return build_hero_invalid_credentials_lab()

    if scenario.fixture == "suspended_account":
        return _build_suspended_lab(scenario.subscriber_id)

    if scenario.fixture == "unknown_condition":
        return _build_unknown_lab(scenario.subscriber_id)

    raise ValueError(f"Unknown benchmark fixture: {scenario.fixture}")


def run_scenario(scenario: BenchmarkScenario) -> ScenarioResult:
    """Execute one scenario through the real agent orchestrator."""

    repository = build_fixture(scenario)
    evidence_store = EvidenceStore()
    approval_service = ApprovalService()

    orchestrator = AgentOrchestrator(
        repository=repository,
        evidence_store=evidence_store,
        approval_service=approval_service,
    )

    incident = Incident(
        incident_id=scenario.incident_id,
        request=scenario.request,
        subscriber_id=scenario.subscriber_id,
        created_at=datetime(2026, 9, 19, tzinfo=UTC),
    )

    initial_session = repository.get_session(scenario.subscriber_id)

    state = orchestrator.investigate(
        incident=incident,
        subscriber_id=scenario.subscriber_id,
    )

    final_session = repository.get_session(scenario.subscriber_id)

    unsafe_mutations = int(initial_session != final_session)

    observed_root_cause = (
        state.diagnosis.root_cause.value if state.diagnosis is not None else "none"
    )
    observed_action = (
        state.proposed_action.action_type.value if state.proposed_action is not None else None
    )

    return ScenarioResult(
        scenario_id=scenario.scenario_id,
        expected_root_cause=scenario.expected_root_cause,
        observed_root_cause=observed_root_cause,
        expected_status=scenario.expected_status,
        observed_status=state.status.value,
        expected_action=scenario.expected_action,
        observed_action=observed_action,
        investigation_steps=state.step_count,
        evidence_count=len(state.evidence_ids),
        unsafe_mutations=unsafe_mutations,
    )


def run_benchmark(
    scenarios: tuple[BenchmarkScenario, ...] | None = None,
) -> BenchmarkReport:
    """Run all supplied reference scenarios."""

    selected_scenarios = scenarios if scenarios is not None else load_scenarios()

    return BenchmarkReport(results=tuple(run_scenario(scenario) for scenario in selected_scenarios))


def _emit(output_fn: OutputFunction, *lines: str) -> None:
    for line in lines:
        output_fn(line)


def display_report(
    report: BenchmarkReport,
    *,
    output_fn: OutputFunction = print,
) -> None:
    """Render benchmark results for a human operator."""

    _emit(
        output_fn,
        "NETOPS SENTINEL - MINI BENCHMARK",
        "=" * 72,
        "",
        f"{'SCENARIO':<26}{'ROOT CAUSE':<24}RESULT",
        "-" * 72,
    )

    for result in report.results:
        outcome = "PASS" if result.passed else "FAIL"
        _emit(
            output_fn,
            f"{result.scenario_id:<26}{result.observed_root_cause.upper():<24}{outcome}",
        )

    _emit(
        output_fn,
        "",
        "METRICS",
        "-" * 72,
        f"Scenarios                   : {report.scenario_count}",
        f"Root-cause accuracy         : {report.root_cause_accuracy:.1%}",
        f"Expected-status accuracy    : {report.status_accuracy:.1%}",
        f"Expected-action accuracy    : {report.action_accuracy:.1%}",
        f"Unsafe mutations            : {report.unsafe_mutations}",
        f"Average investigation steps : {report.average_investigation_steps:.2f}",
        f"Average evidence records    : {report.average_evidence_count:.2f}",
        "",
        f"RESULT                      : {'PASS' if report.passed else 'FAIL'}",
    )


def main() -> int:
    """Run and display the reference mini benchmark."""

    report = run_benchmark()
    display_report(report)

    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
