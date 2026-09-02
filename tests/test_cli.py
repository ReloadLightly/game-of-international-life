from pathlib import Path

from international_life.cli import main


def test_cli_commands_run_end_to_end(tmp_path: Path) -> None:
    conway_path = tmp_path / "conway.png"
    assert (
        main(
            [
                "conway",
                "--pattern",
                "glider",
                "--size",
                "10",
                "--steps",
                "4",
                "--boundary",
                "fixed",
                "--output",
                str(conway_path),
            ]
        )
        == 0
    )
    assert conway_path.is_file()

    jervis_path = tmp_path / "jervis.png"
    assert (
        main(
            [
                "jervis",
                "--size",
                "8",
                "--steps",
                "2",
                "--seed",
                "3",
                "--offense-advantage",
                "0.5",
                "--distinguishability",
                "0.4",
                "--output",
                str(jervis_path),
            ]
        )
        == 0
    )
    assert jervis_path.is_file()

    four_worlds_dir = tmp_path / "four-worlds"
    assert (
        main(
            [
                "four-worlds",
                "--size",
                "8",
                "--steps",
                "2",
                "--seeds",
                "1",
                "--output-dir",
                str(four_worlds_dir),
            ]
        )
        == 0
    )
    assert (four_worlds_dir / "jervis_four_worlds_summary.csv").is_file()

    phase_dir = tmp_path / "phase"
    assert (
        main(
            [
                "phase-diagram",
                "--size",
                "8",
                "--steps",
                "2",
                "--seeds",
                "1",
                "--points",
                "2",
                "--output-dir",
                str(phase_dir),
            ]
        )
        == 0
    )
    assert (phase_dir / "jervis_phase_diagram.csv").is_file()


def test_m2_and_m3_cli_commands_run_end_to_end(tmp_path: Path) -> None:
    territorial_path = tmp_path / "territorial.png"
    assert (
        main(
            [
                "territorial",
                "--height",
                "6",
                "--width",
                "8",
                "--states",
                "4",
                "--steps",
                "2",
                "--seed",
                "3",
                "--output",
                str(territorial_path),
            ]
        )
        == 0
    )
    assert territorial_path.is_file()

    ensemble_dir = tmp_path / "territorial-ensemble"
    assert (
        main(
            [
                "territorial-ensemble",
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
                str(ensemble_dir),
            ]
        )
        == 0
    )
    assert (ensemble_dir / "territorial_ensemble_summary.csv").is_file()

    m3_dir = tmp_path / "m3"
    assert (
        main(
            [
                "m3",
                "--height",
                "6",
                "--width",
                "8",
                "--states",
                "4",
                "--steps",
                "1",
                "--seeds",
                "1",
                "--dominant-share",
                "0.40",
                "--output-dir",
                str(m3_dir),
            ]
        )
        == 0
    )
    assert (m3_dir / "m3_ensemble_summary.csv").is_file()
