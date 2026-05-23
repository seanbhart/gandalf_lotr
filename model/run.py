from __future__ import annotations

import argparse

import pandas as pd

from model.config import make_simulation


def run(timesteps: int | None = None, runs: int | None = None) -> pd.DataFrame:
    kwargs = {}
    if timesteps is not None:
        kwargs["timesteps"] = timesteps
    if runs is not None:
        kwargs["runs"] = runs

    simulation = make_simulation(**kwargs)
    return pd.DataFrame(simulation.run())


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the LOTR radCAD model.")
    parser.add_argument("--timesteps", type=int, default=30)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--csv", help="Optional path to write simulation records.")
    args = parser.parse_args()

    df = run(timesteps=args.timesteps, runs=args.runs)
    if args.csv:
        df.to_csv(args.csv, index=False)
    print(df.tail(10).to_string(index=False))


if __name__ == "__main__":
    main()
