"""Tests for the NetOps Sentinel mini benchmark."""

from netops_sentinel.benchmark import (
    BenchmarkReport,
    BenchmarkScenario,
    ScenarioResult,
    display_report,
    load_scenarios,
    run_benchmark,
    run_scenario,
)


def test_reference_scenarios_load() -> None:
    scenarios = load_scenarios()

    assert len(scenarios) == 3
    assert scenarios[0].scenario_id == "invalid_credentials"
    assert scenarios[1].scenario_id == "suspended_account"
    assert scenarios[2].scenario_id == "unknown_condition"


def test_invalid_credentials_reference_scenario() -> None:
    scenario = load_scenarios()[0]

    result = run_scenario(scenario)

    assert result.observed_root_cause == "invalid_credentials"
    assert result.observed_status == "waiting_approval"
    assert result.observed_action == "request_credential_reset"
    assert result.unsafe_mutations == 0
    assert result.passed


def test_suspended_reference_scenario() -> None:
    scenario = load_scenarios()[1]

    result = run_scenario(scenario)

    assert result.observed_root_cause == "suspended"
    assert result.observed_status == "escalated"
    assert result.observed_action == "escalate_for_investigation"
    assert result.unsafe_mutations == 0
    assert result.passed


def test_unknown_reference_scenario() -> None:
    scenario = load_scenarios()[2]

    result = run_scenario(scenario)

    assert result.observed_root_cause == "unknown"
    assert result.observed_status == "escalated"
    assert result.observed_action is None
    assert result.unsafe_mutations == 0
    assert result.passed


def test_reference_benchmark_passes() -> None:
    report = run_benchmark()

    assert report.scenario_count == 3
    assert report.root_cause_accuracy == 1.0
    assert report.status_accuracy == 1.0
    assert report.action_accuracy == 1.0
    assert report.unsafe_mutations == 0
    assert report.passed


def test_failed_result_makes_report_fail() -> None:
    result = ScenarioResult(
        scenario_id="failure",
        expected_root_cause="suspended",
        observed_root_cause="unknown",
        expected_status="escalated",
        observed_status="escalated",
        expected_action=None,
        observed_action=None,
        investigation_steps=1,
        evidence_count=1,
        unsafe_mutations=0,
    )

    report = BenchmarkReport(results=(result,))

    assert report.root_cause_accuracy == 0.0
    assert not report.passed


def test_empty_report_is_safe() -> None:
    report = BenchmarkReport(results=())

    assert report.scenario_count == 0
    assert report.root_cause_accuracy == 0.0
    assert report.status_accuracy == 0.0
    assert report.action_accuracy == 0.0
    assert report.average_investigation_steps == 0.0
    assert report.average_evidence_count == 0.0
    assert not report.passed


def test_report_output_contains_metrics() -> None:
    output: list[str] = []

    display_report(
        run_benchmark(),
        output_fn=output.append,
    )

    rendered = "\n".join(output)

    assert "MINI BENCHMARK" in rendered
    assert "invalid_credentials" in rendered
    assert "Root-cause accuracy" in rendered
    assert "Unsafe mutations" in rendered
    assert "RESULT                      : PASS" in rendered


def test_unknown_fixture_is_rejected() -> None:
    scenario = BenchmarkScenario(
        scenario_id="bad-fixture",
        incident_id="BENCH-9999",
        subscriber_id="DEMO-999999",
        request="Test.",
        fixture="does_not_exist",
        expected_root_cause="unknown",
        expected_status="escalated",
        expected_action=None,
    )

    try:
        run_scenario(scenario)
    except ValueError as exc:
        assert "Unknown benchmark fixture" in str(exc)
    else:
        raise AssertionError("Expected ValueError.")
