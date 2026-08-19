from pathlib import Path

from flyin.adapters.map_catalog import MapCatalog


def _make_maps(root: Path) -> None:
    """Create a small nested map tree to catalog."""
    (root / "easy").mkdir()
    (root / "easy" / "02_second.txt").write_text("")
    (root / "easy" / "01_first.txt").write_text("")
    (root / "hard" / "sub").mkdir(parents=True)
    (root / "hard" / "sub" / "03_deep.txt").write_text("")
    (root / "notes.md").write_text("not a map")


def test_lists_txt_files_sorted_and_one_based(tmp_path: Path) -> None:
    _make_maps(tmp_path)

    options = MapCatalog(tmp_path).available_maps()

    assert [option.index for option in options] == [1, 2, 3]
    assert [option.display_path for option in options] == [
        f"{tmp_path.name}/easy/01_first.txt",
        f"{tmp_path.name}/easy/02_second.txt",
        f"{tmp_path.name}/hard/sub/03_deep.txt"
    ]


def test_option_for_index_returns_the_selected_map(tmp_path: Path) -> None:
    _make_maps(tmp_path)
    catalog = MapCatalog(tmp_path)

    selected = catalog.option_for_index(2)

    assert selected is not None
    assert selected.path == tmp_path / "easy" / "02_second.txt"


def test_option_for_index_rejects_out_of_range(tmp_path: Path) -> None:
    _make_maps(tmp_path)
    catalog = MapCatalog(tmp_path)

    assert catalog.option_for_index(0) is None
    assert catalog.option_for_index(4) is None


def test_missing_root_yields_no_options(tmp_path: Path) -> None:
    assert MapCatalog(tmp_path / "nope").available_maps() == ()


def test_official_catalog_finds_the_repository_maps() -> None:
    options = MapCatalog.official().available_maps()

    assert len(options) == 10
    assert options[0].display_path.startswith("maps/")
