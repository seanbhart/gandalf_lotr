import math

from model.config import make_simulation
from model.report import generate_reports
from model.scenarios import run_all_scenarios, summarize_scenarios
from model.state_variables import initial_state
from model.valuation import crossed_limit, token_pair_values


def test_token_pair_values_sum_to_collateral_after_fees():
    limit_token, redeem_token, pair_value = token_pair_values(
        target_price=12.0,
        limit_price=10.0,
        sigma=0.5,
        transfer_fee_rate=0.02,
    )

    assert limit_token > 0
    assert redeem_token > 0
    assert math.isclose(pair_value, 9.8)


def test_crossing_limit_detects_direction_change():
    assert crossed_limit("above", target_price=9.5, limit_price=10.0)
    assert crossed_limit("below", target_price=10.5, limit_price=10.0)
    assert not crossed_limit("above", target_price=12.0, limit_price=10.0)


def test_simulation_runs_with_parameter_sweep():
    simulation = make_simulation(timesteps=4, runs=1)
    records = simulation.run()

    limit_prices = {record["limit_price"] for record in records if record["timestep"] > 0}
    assert limit_prices == {5.0, 10.0, 15.0, 19.0}


def test_oracle_failure_blocks_execution_and_records_reason():
    params = {
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
        "oracle_available": [False],
        "dex_available": [True],
        "redeemer_has_pair": [False],
        "redemption_timestep": [None],
        "random_seed": [1],
    }
    state = {
        **initial_state,
        "target_price": 9.0,
        "limit_price": 10.0,
        "previous_price_direction": "above",
    }

    records = make_simulation(params=params, state=state, timesteps=1, runs=1).run()
    last = records[-1]

    assert last["executed"] is False
    assert last["execution_failed"] is True
    assert last["failure_reason"] == "oracle_unavailable"


def test_redemption_prevents_later_execution():
    params = {
        "limit_price": [10.0],
        "price_change_min_bp": [-1000],
        "price_change_max_bp": [-1000],
        "sigma_change_min_bp": [0],
        "sigma_change_max_bp": [0],
        "min_sigma": [0.10],
        "transfer_fee_rate": [0.01],
        "execution_reward_rate": [0.0],
        "dex_slippage_rate": [0.0],
        "dex_liquidity": [1_000_000.0],
        "oracle_available": [True],
        "dex_available": [True],
        "redeemer_has_pair": [True],
        "redemption_timestep": [1],
        "random_seed": [1],
    }
    state = {
        **initial_state,
        "target_price": 12.0,
        "limit_price": 10.0,
        "previous_price_direction": "above",
    }

    records = make_simulation(params=params, state=state, timesteps=4, runs=1).run()
    last = records[-1]

    assert last["redeemed"] is True
    assert last["redemption_value"] == 9.9
    assert last["executed"] is False


def test_scenarios_generate_summary_and_outputs(tmp_path):
    records = run_all_scenarios()
    summary = summarize_scenarios(records)

    assert set(summary["scenario"]) >= {
        "downside_execution",
        "redemption_before_execution",
        "oracle_failure",
        "fees_and_slippage",
    }
    assert summary.loc[summary["scenario"] == "oracle_failure", "failed_runs"].iloc[0] == 1

    paths = generate_reports(tmp_path)
    assert paths["dashboard"].exists()
    assert paths["notebook"].exists()
