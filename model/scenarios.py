from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from model.config import make_simulation
from model.state_variables import initial_state


@dataclass(frozen=True)
class Scenario:
    name: str
    description: str
    params: dict[str, list[Any]]
    state: dict[str, Any] = field(default_factory=dict)
    timesteps: int = 30
    runs: int = 1


BASE_PARAMS = {
    "limit_price": [10.0],
    "price_change_min_bp": [0],
    "price_change_max_bp": [0],
    "sigma_change_min_bp": [0],
    "sigma_change_max_bp": [0],
    "min_sigma": [0.10],
    "transfer_fee_rate": [0.0],
    "execution_reward_rate": [0.0],
    "dex_slippage_rate": [0.0],
    "dex_liquidity": [1_000_000.0],
    "oracle_available": [True],
    "dex_available": [True],
    "redeemer_has_pair": [False],
    "redemption_timestep": [None],
    "random_seed": [11],
}


def _params(**overrides) -> dict[str, list[Any]]:
    params = {key: list(value) for key, value in BASE_PARAMS.items()}
    for key, value in overrides.items():
        params[key] = value if isinstance(value, list) else [value]
    return params


def _state(**overrides) -> dict[str, Any]:
    state = {**initial_state}
    state.update(overrides)
    return state


SCENARIOS = [
    Scenario(
        name="downside_execution",
        description="Market starts above a lower limit and drifts down until the Limit Token executes.",
        params=_params(price_change_min_bp=-350, price_change_max_bp=-350),
        state=_state(target_price=12.0, limit_price=10.0, previous_price_direction="above"),
        timesteps=24,
    ),
    Scenario(
        name="upside_execution",
        description="Market starts below a higher limit and rallies into execution.",
        params=_params(limit_price=15.0, price_change_min_bp=350, price_change_max_bp=350),
        state=_state(target_price=12.0, limit_price=15.0, previous_price_direction="below"),
        timesteps=24,
    ),
    Scenario(
        name="redemption_before_execution",
        description="A holder reunites both token halves and redeems collateral before the limit is crossed.",
        params=_params(
            price_change_min_bp=-50,
            price_change_max_bp=-50,
            redeemer_has_pair=True,
            redemption_timestep=8,
            transfer_fee_rate=0.01,
        ),
        state=_state(target_price=12.0, limit_price=10.0, previous_price_direction="above"),
        timesteps=16,
    ),
    Scenario(
        name="oracle_failure",
        description="The market crosses the limit but execution fails because the price oracle is unavailable.",
        params=_params(oracle_available=False),
        state=_state(target_price=9.5, limit_price=10.0, previous_price_direction="above"),
        timesteps=1,
    ),
    Scenario(
        name="dex_liquidity_shortfall",
        description="Execution is triggered, but available DEX liquidity is below the embedded collateral size.",
        params=_params(dex_liquidity=5.0),
        state=_state(target_price=9.5, limit_price=10.0, previous_price_direction="above"),
        timesteps=1,
    ),
    Scenario(
        name="fees_and_slippage",
        description="Execution succeeds after reward fees and swap slippage reduce realized value.",
        params=_params(execution_reward_rate=0.01, dex_slippage_rate=0.03, transfer_fee_rate=0.02),
        state=_state(target_price=9.5, limit_price=10.0, previous_price_direction="above"),
        timesteps=1,
    ),
]


def terminal_records(df: pd.DataFrame) -> pd.DataFrame:
    max_substep = df.groupby(["simulation", "subset", "run", "timestep"])["substep"].transform("max")
    return df[df["substep"] == max_substep].copy()


def run_scenario(scenario: Scenario) -> pd.DataFrame:
    simulation = make_simulation(
        params=scenario.params,
        state=scenario.state,
        timesteps=scenario.timesteps,
        runs=scenario.runs,
    )
    df = terminal_records(pd.DataFrame(simulation.run()))
    df.insert(0, "scenario", scenario.name)
    df.insert(1, "description", scenario.description)
    return df


def run_all_scenarios() -> pd.DataFrame:
    return pd.concat([run_scenario(scenario) for scenario in SCENARIOS], ignore_index=True)


def summarize_scenarios(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scenario, group in df.groupby("scenario", sort=False):
        final = group.sort_values(["run", "timestep"]).groupby("run").tail(1)
        rows.append(
            {
                "scenario": scenario,
                "runs": int(final["run"].nunique()),
                "executed_runs": int(final["executed"].sum()),
                "redeemed_runs": int(final["redeemed"].sum()),
                "failed_runs": int(final["execution_failed"].sum()),
                "failure_reasons": ", ".join(sorted(reason for reason in final["failure_reason"].unique() if reason)),
                "avg_final_target_price": round(float(final["target_price"].mean()), 4),
                "avg_limit_token_price": round(float(final["limit_token_price"].mean()), 4),
                "avg_redeem_token_price": round(float(final["redeem_token_price"].mean()), 4),
                "avg_pair_value": round(float(final["pair_value"].mean()), 4),
                "avg_execution_value": round(float(final["execution_value"].mean()), 4),
                "avg_redemption_value": round(float(final["redemption_value"].mean()), 4),
            }
        )
    return pd.DataFrame(rows)


def write_scenario_outputs(output_dir: str | Path = "reports") -> tuple[Path, Path]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records = run_all_scenarios()
    summary = summarize_scenarios(records)
    records_path = output_dir / "lotr_scenario_records.csv"
    summary_path = output_dir / "lotr_scenario_summary.csv"
    records.to_csv(records_path, index=False)
    summary.to_csv(summary_path, index=False)
    return records_path, summary_path
