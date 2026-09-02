from pathlib import Path

from international_life.experiments.jervis_four_worlds import run_four_worlds
from international_life.experiments.jervis_phase_diagram import run_phase_diagram


def test_four_worlds_writes_reproducible_outputs(tmp_path: Path) -> None:
    run_path, summary_path = run_four_worlds(
        tmp_path,
        steps=2,
        seeds=1,
        shape=(8, 8),
    )
    assert run_path.is_file()
    assert summary_path.is_file()
    assert (tmp_path / "jervis_final_mean_arms.png").is_file()
    assert (tmp_path / "jervis_mean_conflict_rate.png").is_file()
    assert len(run_path.read_text(encoding="utf-8").splitlines()) == 5
    assert len(summary_path.read_text(encoding="utf-8").splitlines()) == 5


def test_phase_diagram_writes_data_and_separate_plots(tmp_path: Path) -> None:
    csv_path = run_phase_diagram(
        tmp_path,
        steps=2,
        seeds=1,
        points=2,
        shape=(8, 8),
    )
    assert csv_path.is_file()
    assert (tmp_path / "jervis_phase_final_arms.png").is_file()
    assert (tmp_path / "jervis_phase_conflict.png").is_file()
    assert len(csv_path.read_text(encoding="utf-8").splitlines()) == 5


def test_territorial_ensemble_writes_trajectories_maps_and_plots(tmp_path: Path) -> None:
    from international_life.experiments.territorial_ensemble import run_territorial_ensemble

    timeseries_path, summary_path = run_territorial_ensemble(
        tmp_path,
        steps=2,
        seeds=1,
        shape=(6, 8),
        num_polities=4,
    )
    assert timeseries_path.is_file()
    assert summary_path.is_file()
    assert (tmp_path / "territorial_initial_seed0.png").is_file()
    assert (tmp_path / "territorial_final_seed0.png").is_file()
    assert (tmp_path / "territorial_state_count.png").is_file()
    assert (tmp_path / "territorial_effective_powers.png").is_file()
    assert (tmp_path / "territorial_conquests.png").is_file()
    assert len(timeseries_path.read_text(encoding="utf-8").splitlines()) == 4
    assert len(summary_path.read_text(encoding="utf-8").splitlines()) == 4
