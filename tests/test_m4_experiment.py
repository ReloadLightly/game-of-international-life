import csv
import json
from pathlib import Path

from international_life.cli import main
from international_life.experiments.alliance_comparison import run_alliance_comparison


def test_m4_experiment_writes_matched_tables_and_figures(tmp_path: Path) -> None:
    paths = run_alliance_comparison(
        tmp_path,
        steps=3,
        seeds=1,
        shape=(6, 8),
        num_polities=4,
    )
    assert all(path.is_file() for path in paths)
    for filename in (
        "m4_abandonment.png",
        "m4_entrapment.png",
        "m4_chain_ganging.png",
        "m4_conflict_cost.png",
        "m4_matched_networks.png",
    ):
        assert (tmp_path / filename).is_file()

    manifest = json.loads((tmp_path / "m4_manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "0.4.0"
    assert manifest["matching_contract"]["difference_definition"] == "binding minus flexible"

    with (tmp_path / "m4_paired_differences.csv").open(encoding="utf-8") as handle:
        paired = list(csv.DictReader(handle))
    assert len(paired) == 4
    assert all(row["initial_fingerprint"] for row in paired)


def test_m4_cli_runs_end_to_end(tmp_path: Path) -> None:
    output_dir = tmp_path / "m4"
    assert (
        main(
            [
                "m4",
                "--height",
                "6",
                "--width",
                "8",
                "--states",
                "4",
                "--steps",
                "2",
                "--seeds",
                "1",
                "--output-dir",
                str(output_dir),
            ]
        )
        == 0
    )
    assert (output_dir / "m4_ensemble_summary.csv").is_file()
    assert (output_dir / "m4_matched_networks.png").is_file()
