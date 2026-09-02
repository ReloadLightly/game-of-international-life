"""Command-line interface for reproducible demonstrations and experiments."""

from __future__ import annotations

import argparse
from pathlib import Path

from international_life.conway import PATTERNS, run_conway, seed_pattern
from international_life.experiments.jervis_four_worlds import run_four_worlds
from international_life.experiments.jervis_phase_diagram import run_phase_diagram
from international_life.experiments.territorial_ensemble import run_territorial_ensemble
from international_life.jervis import (
    JervisParameters,
    history_metrics,
    initialize_jervis_world,
    run_jervis,
)
from international_life.territorial import (
    TerritorialParameters,
    initialize_territorial_world,
    run_territorial,
    territorial_metrics,
)
from international_life.visualization import (
    save_binary_grid,
    save_jervis_arms,
    save_territorial_map,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="international-life",
        description="Cellular automata for international-relations theory experiments.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    conway = subparsers.add_parser("conway", help="run faithful Conway's Game of Life")
    conway.add_argument("--pattern", choices=sorted(PATTERNS), default="glider")
    conway.add_argument("--size", type=int, default=40)
    conway.add_argument("--steps", type=int, default=40)
    conway.add_argument("--boundary", choices=("wrap", "fixed"), default="wrap")
    conway.add_argument("--output", type=Path, default=Path("artifacts/conway_final.png"))

    jervis = subparsers.add_parser("jervis", help="run one Jervisian CA world")
    jervis.add_argument("--size", type=int, default=40)
    jervis.add_argument("--steps", type=int, default=80)
    jervis.add_argument("--seed", type=int, default=0)
    jervis.add_argument("--offense-advantage", type=float, default=0.75)
    jervis.add_argument("--distinguishability", type=float, default=0.25)
    jervis.add_argument("--output", type=Path, default=Path("artifacts/jervis_final.png"))

    four_worlds = subparsers.add_parser("four-worlds", help="run the matched Jervis 2x2")
    four_worlds.add_argument("--steps", type=int, default=80)
    four_worlds.add_argument("--seeds", type=int, default=12)
    four_worlds.add_argument("--size", type=int, default=40)
    four_worlds.add_argument("--output-dir", type=Path, default=Path("artifacts"))

    phase = subparsers.add_parser("phase-diagram", help="sweep the two Jervis dimensions")
    phase.add_argument("--steps", type=int, default=60)
    phase.add_argument("--seeds", type=int, default=6)
    phase.add_argument("--points", type=int, default=9)
    phase.add_argument("--size", type=int, default=32)
    phase.add_argument("--output-dir", type=Path, default=Path("artifacts"))

    territorial = subparsers.add_parser(
        "territorial",
        help="run one M2 hexagonal territorial world",
    )
    territorial.add_argument("--height", type=int, default=24)
    territorial.add_argument("--width", type=int, default=32)
    territorial.add_argument("--states", type=int, default=10)
    territorial.add_argument("--steps", type=int, default=60)
    territorial.add_argument("--seed", type=int, default=0)
    territorial.add_argument("--attack-threshold", type=float, default=0.98)
    territorial.add_argument("--battle-noise", type=float, default=0.06)
    territorial.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/territorial_final.png"),
    )

    territorial_ensemble = subparsers.add_parser(
        "territorial-ensemble",
        help="run a reproducible M2 ensemble and save trajectories",
    )
    territorial_ensemble.add_argument("--height", type=int, default=24)
    territorial_ensemble.add_argument("--width", type=int, default=32)
    territorial_ensemble.add_argument("--states", type=int, default=10)
    territorial_ensemble.add_argument("--steps", type=int, default=60)
    territorial_ensemble.add_argument("--seeds", type=int, default=6)
    territorial_ensemble.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "conway":
        initial = seed_pattern((args.size, args.size), args.pattern)
        history = run_conway(initial, steps=args.steps, boundary=args.boundary)
        save_binary_grid(
            history[-1],
            args.output,
            title=f"Conway: {args.pattern}, generation {args.steps}",
        )
        print(f"saved {args.output}")
        return 0

    if args.command == "jervis":
        params = JervisParameters(
            offense_advantage=args.offense_advantage,
            distinguishability=args.distinguishability,
        )
        initial = initialize_jervis_world((args.size, args.size), seed=args.seed)
        history = run_jervis(initial, params, steps=args.steps)
        metrics = history_metrics(history, params)
        save_jervis_arms(
            history[-1],
            params,
            args.output,
            title=f"Jervisian CA, generation {args.steps}",
        )
        for name, value in metrics.items():
            print(f"{name}: {value:.6f}")
        print(f"saved {args.output}")
        return 0

    if args.command == "four-worlds":
        paths = run_four_worlds(
            args.output_dir,
            steps=args.steps,
            seeds=args.seeds,
            shape=(args.size, args.size),
        )
        print("saved " + ", ".join(str(path) for path in paths))
        return 0

    if args.command == "phase-diagram":
        path = run_phase_diagram(
            args.output_dir,
            steps=args.steps,
            seeds=args.seeds,
            points=args.points,
            shape=(args.size, args.size),
        )
        print(f"saved {path}")
        return 0

    if args.command == "territorial":
        params = TerritorialParameters(
            attack_threshold=args.attack_threshold,
            battle_noise=args.battle_noise,
            battle_seed=args.seed,
        )
        initial = initialize_territorial_world(
            (args.height, args.width),
            num_polities=args.states,
            seed=args.seed,
        )
        history = run_territorial(initial, params, steps=args.steps)
        save_territorial_map(
            history[-1],
            args.output,
            title=f"M2 territorial world: generation {args.steps}",
        )
        for name, value in territorial_metrics(history[-1]).items():
            if isinstance(value, float):
                print(f"{name}: {value:.6f}")
            else:
                print(f"{name}: {value}")
        print(f"saved {args.output}")
        return 0

    if args.command == "territorial-ensemble":
        paths = run_territorial_ensemble(
            args.output_dir,
            steps=args.steps,
            seeds=args.seeds,
            shape=(args.height, args.width),
            num_polities=args.states,
        )
        print("saved " + ", ".join(str(path) for path in paths))
        return 0

    raise AssertionError(f"unhandled command: {args.command}")
