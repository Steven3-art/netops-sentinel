"""Tests for the NetOps Sentinel CLI hero demonstration."""

from collections.abc import Iterator

from netops_sentinel.demo import main


def _run_demo(answer: str) -> tuple[int, str]:
    """Run the demo with deterministic input and capture its output."""

    output: list[str] = []
    answers: Iterator[str] = iter((answer,))

    exit_code = main(
        input_fn=lambda _: next(answers),
        output_fn=output.append,
    )

    return exit_code, "\n".join(output)


def test_demo_refusal_executes_no_mutation() -> None:
    exit_code, output = _run_demo("n")

    assert exit_code == 0
    assert "INVALID_CREDENTIALS" in output
    assert "REQUEST_CREDENTIAL_RESET" in output
    assert "HUMAN APPROVAL REQUIRED" in output
    assert "ACTION NOT APPROVED" in output
    assert "No mutation was executed." in output
    assert "RECOVERED" not in output


def test_demo_approval_reaches_recovered_state() -> None:
    exit_code, output = _run_demo("y")

    assert exit_code == 0

    assert "NETOPS SENTINEL" in output
    assert "DEMO-100042" in output

    assert "subscriber.get_status" in output
    assert "session.get_online_session" in output
    assert "radius.get_failures" in output

    assert "EV-0001" in output
    assert "EV-0002" in output
    assert "EV-0003" in output
    assert "EV-0004" in output

    assert "INVALID_CREDENTIALS" in output
    assert "Confidence  : 100%" in output
    assert "REQUEST_CREDENTIAL_RESET" in output
    assert "LEVEL_2_MUTATE" in output

    assert "Approved by : demo-operator" in output

    assert "EV-0005" in output
    assert "EV-0006" in output
    assert "EV-0007" in output

    assert "Session: ONLINE" in output
    assert "Authentication: SUCCESS" in output

    assert "RECOVERED" in output
    assert "Incident lifecycle completed successfully." in output


def test_demo_yes_word_is_accepted() -> None:
    exit_code, output = _run_demo("YES")

    assert exit_code == 0
    assert "RECOVERED" in output


def test_demo_ambiguous_answer_is_fail_safe() -> None:
    exit_code, output = _run_demo("maybe")

    assert exit_code == 0
    assert "ACTION NOT APPROVED" in output
    assert "No mutation was executed." in output
    assert "CONTROLLED EXECUTION" not in output
    assert "RECOVERED" not in output


def test_demo_empty_answer_is_fail_safe() -> None:
    exit_code, output = _run_demo("")

    assert exit_code == 0
    assert "ACTION NOT APPROVED" in output
    assert "No mutation was executed." in output
    assert "RECOVERED" not in output
