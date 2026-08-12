import io
from pathlib import Path

from flyin.adapters.cli.cli import Cli

_LINEAR_MAP = (
    "nb_drones: 1\n"
    "start_hub: start 0 0\n"
    "hub: a 1 0\n"
    "end_hub: goal 2 0\n"
    "connection: start-a\n"
    "connection: a-goal\n"
)


def _run(argv: list[str]) -> tuple[int, str, str]:
    """Run the CLI and return (exit_code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    code = Cli(out, err).run(argv)
    return code, out.getvalue(), err.getvalue()


def test_prints_movement_lines_and_exits_zero(tmp_path: Path) -> None:
    map_file = tmp_path / "m.txt"
    map_file.write_text(_LINEAR_MAP)

    code, out, err = _run([str(map_file)])

    assert code == 0
    assert out == "D1-a\nD1-goal\n"
    assert err == ""


def test_reports_parse_error_on_stderr(tmp_path: Path) -> None:
    map_file = tmp_path / "m.txt"
    # No nb_drones header: the parser rejects it.
    map_file.write_text("start_hub: s 0 0\nend_hub: goal 1 0\n")

    code, out, err = _run([str(map_file)])

    assert code == 1
    assert out == ""
    assert err != ""


def test_reports_unsolvable_map_on_stderr(tmp_path: Path) -> None:
    map_file = tmp_path / "m.txt"
    map_file.write_text(
        "nb_drones: 1\n"
        "start_hub: start 0 0\n"
        "hub: island 1 0\n"
        "end_hub: goal 2 0\n"
        "connection: start-island\n"
    )

    code, out, err = _run([str(map_file)])

    assert code == 1
    assert out == ""
    assert err != ""


def test_wrong_arguments_return_usage_error() -> None:
    code, out, err = _run([])

    assert code == 2
    assert out == ""
    assert "usage" in err
