import io
from pathlib import Path

from flyin.adapters.cli.cli import Cli
from flyin.adapters.map_catalog import MapCatalog

_LINEAR_MAP = (
    "nb_drones: 1\n"
    "start_hub: start 0 0\n"
    "hub: a 1 0\n"
    "end_hub: goal 2 0\n"
    "connection: start-a\n"
    "connection: a-goal\n"
)


def _run(
    argv: list[str],
    typed: str = "",
    maps_root: Path = Path("maps")
) -> tuple[int, str, str]:
    """Run the CLI and return (exit_code, stdout, stderr).

    Args:
        argv: Command-line arguments without the program name.
        typed: What a human types at the map prompt, if it is reached.
        maps_root: Directory the offered map catalog is built from.
    """
    out, err = io.StringIO(), io.StringIO()
    catalog = MapCatalog(maps_root)
    code = Cli(out, err, io.StringIO(typed), catalog).run(argv)
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


def test_too_many_arguments_return_usage_error() -> None:
    code, out, err = _run(["one.txt", "two.txt"])

    assert code == 2
    assert out == ""
    assert "usage" in err


def test_warning_goes_to_stderr_and_stdout_stays_clean(
    tmp_path: Path
) -> None:
    map_file = tmp_path / "m.txt"
    map_file.write_text(
        "nb_drones: 1\n"
        "start_hub: start 0 0 [zone=restricted]\n"
        "hub: a 1 0\n"
        "end_hub: goal 2 0\n"
        "connection: start-a\n"
        "connection: a-goal\n"
    )

    code, out, err = _run([str(map_file)])

    # The map solves (exit 0); the warning goes to stderr, never to stdout.
    assert code == 0
    assert out == "D1-a\nD1-goal\n"
    assert "warning" in err
    assert "start" in err


def test_no_argument_offers_the_map_catalog(tmp_path: Path) -> None:
    (tmp_path / "m.txt").write_text(_LINEAR_MAP)

    code, out, err = _run([], typed="1\n", maps_root=tmp_path)

    # The catalog is part of the dialogue a human asked for, so it goes to
    # stdout; the chosen map is then solved as usual.
    assert code == 0
    assert f"1. {tmp_path.name}/m.txt" in out
    assert out.endswith("D1-a\nD1-goal\n")
    assert err == ""


def test_selection_out_of_range_is_an_error(tmp_path: Path) -> None:
    (tmp_path / "m.txt").write_text(_LINEAR_MAP)

    code, out, err = _run([], typed="7\n", maps_root=tmp_path)

    assert code == 2
    assert "D1" not in out
    assert err != ""


def test_selection_must_be_a_number(tmp_path: Path) -> None:
    (tmp_path / "m.txt").write_text(_LINEAR_MAP)

    code, out, err = _run([], typed="abc\n", maps_root=tmp_path)

    assert code == 2
    assert err != ""


def test_empty_catalog_reports_an_error(tmp_path: Path) -> None:
    code, out, err = _run([], typed="1\n", maps_root=tmp_path)

    assert code == 2
    assert out == ""
    assert err != ""


class _FlushRecordingStream(io.StringIO):
    """Stdout stub that remembers how much was written on each flush."""

    def __init__(self) -> None:
        super().__init__()
        self.flushed_sizes: list[int] = []

    def flush(self) -> None:
        self.flushed_sizes.append(len(self.getvalue()))


def test_prompt_is_flushed_before_reading_the_answer(
    tmp_path: Path
) -> None:
    (tmp_path / "m.txt").write_text(_LINEAR_MAP)
    out = _FlushRecordingStream()
    err = io.StringIO()

    code = Cli(out, err, io.StringIO("1\n"), MapCatalog(tmp_path)).run([])

    # Without an explicit flush a line-buffered stdout holds the prompt back
    # (it has no trailing newline) and a human only sees it after answering.
    assert code == 0
    assert out.flushed_sizes
    written_when_flushed = out.getvalue()[:out.flushed_sizes[0]]
    assert written_when_flushed.endswith(
        "Type the number of the map to run: "
    )


def test_catalog_is_readable_and_separated(tmp_path: Path) -> None:
    (tmp_path / "m.txt").write_text(_LINEAR_MAP)

    _, out, _ = _run([], typed="1\n", maps_root=tmp_path)

    prompt = "Type the number of the map to run: "
    assert out.startswith("\nAvailable maps:\n\n")
    # A blank line keeps the simulation from starting glued to the answer.
    assert out.endswith(f"{prompt}\nD1-a\nD1-goal\n")
