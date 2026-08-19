from flyin.adapters.cli.visual import (
    RESET,
    AnsiPalette,
    VisualRenderer
)
from flyin.parsing.map_parser import MapParser

_FORK_MAP = (
    "nb_drones: 2\n"
    "start_hub: start 0 0 [color=green]\n"
    "hub: junction 1 0 [color=yellow max_drones=2]\n"
    "hub: vault 2 0 [zone=restricted color=nosuchcolor]\n"
    "end_hub: goal 3 0 [color=red]\n"
    "connection: start-junction\n"
    "connection: junction-vault\n"
    "connection: vault-goal\n"
)


def _render(lines: list[str]) -> list[str]:
    """Render movement lines against the fork map above."""
    return VisualRenderer(MapParser(_FORK_MAP).parse()).render(lines)


def test_palette_paints_a_known_color() -> None:
    assert AnsiPalette().paint("start", "green") == "\033[32mstart\033[0m"


def test_palette_leaves_unknown_and_missing_colors_alone() -> None:
    palette = AnsiPalette()

    # The subject allows any single word as a color and fixes no list, so an
    # unknown one must degrade to plain text instead of failing.
    assert palette.paint("vault", "nosuchcolor") == "vault"
    assert palette.paint("vault", None) == "vault"


def test_view_reports_every_zone_state() -> None:
    rendered = "\n".join(_render([]))

    assert "Drones: 2" in rendered
    assert "type=normal" in rendered
    assert "type=restricted" in rendered
    # Terminals ignore max_drones, and a plain zone defaults to 1.
    assert "capacity=unlimited" in rendered
    assert "capacity=2" in rendered
    assert "capacity=1" in rendered
    assert "color=nosuchcolor" in rendered
    assert "xy=(1,0)" in rendered


def test_view_paints_zone_names_with_their_color() -> None:
    lines = _render([])

    # Names are padded before being painted, so the escape code opens on the
    # name and closes after the padding that keeps the columns aligned.
    assert any(line.startswith("  \033[32m■") for line in lines)
    assert any("\033[32mstart   \033[0m" in line for line in lines)
    assert any("\033[33mjunction\033[0m" in line for line in lines)
    assert any("\033[31mgoal    \033[0m" in line for line in lines)


def test_unknown_color_is_reported_but_never_painted() -> None:
    vault = next(line for line in _render([]) if "vault" in line)

    assert "color=nosuchcolor" in vault
    assert "\033[" not in vault


def test_turns_are_numbered_and_painted() -> None:
    rendered = "\n".join(_render(["D1-junction", "D1-goal D2-junction"]))

    assert "Turn 1: D1-\033[33mjunction\033[0m" in rendered
    assert "Turn 2: D1-\033[31mgoal\033[0m D2-\033[33mjunction\033[0m" in (
        rendered
    )


def test_view_appends_the_run_metrics() -> None:
    rendered = "\n".join(
        _render(["D1-junction", "D1-goal D2-junction", "D2-goal"])
    )

    assert "Metrics:" in rendered
    assert "Turns:" in rendered and "3" in rendered
    # Four tokens across the three turns.
    assert "Total moves:" in rendered and "4" in rendered
    assert "Drones/turn (avg):" in rendered and "1.3" in rendered


def test_in_flight_token_paints_both_ends() -> None:
    # A drone in transit toward a restricted zone is D<id>-<from>-<to>; zone
    # names cannot contain dashes, so the split is unambiguous.
    rendered = "\n".join(_render(["D1-junction-vault"]))

    assert "D1-\033[33mjunction\033[0m-vault" in rendered


def test_palette_covers_every_color_the_official_maps_declare() -> None:
    # Taken from `grep -o 'color=[a-z]*' maps/*/*.txt`: if one of these is
    # missing the official maps render half-plain, which defeats the point.
    declared = (
        "orange", "blue", "red", "green", "purple", "darkred", "cyan",
        "gold", "brown", "yellow", "maroon", "crimson", "black", "lime",
        "violet", "magenta"
    )
    palette = AnsiPalette()

    unpainted = [
        color for color in declared
        if palette.paint("zone", color) == "zone"
    ]

    assert unpainted == []


def test_palette_spreads_rainbow_across_the_letters() -> None:
    painted = AnsiPalette().paint("ab", "rainbow")

    # One official map declares color=rainbow, which is not a single hue.
    assert painted.count(RESET) == 2
    assert painted.startswith("\033[31ma\033[0m")
    assert painted != "ab"
