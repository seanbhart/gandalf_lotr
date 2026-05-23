from __future__ import annotations

import numpy as np


def _rng(params, state_current, salt: int = 0):
    seed = int(params["random_seed"])
    run = int(state_current["run"])
    timestep = int(state_current["timestep"])
    subset = int(state_current["subset"])
    return np.random.default_rng(seed + (run * 100_000) + (subset * 1_000) + timestep + salt)


def p_target_price_change(params, _substep, _state_history, state_current, **_kwargs):
    rng = _rng(params, state_current)
    basis_points = rng.integers(
        int(params["price_change_min_bp"]),
        int(params["price_change_max_bp"]) + 1,
    )
    return {"target_price_change": float(basis_points) * 0.0001}


def p_sigma_change(params, _substep, _state_history, state_current, **_kwargs):
    rng = _rng(params, state_current, salt=17)
    basis_points = rng.integers(
        int(params["sigma_change_min_bp"]),
        int(params["sigma_change_max_bp"]) + 1,
    )
    return {"sigma_change": float(basis_points) * 0.0001}


def s_target_price(_params, _substep, _state_history, state_current, policy_input, **_kwargs):
    new_price = state_current["target_price"] * (1.0 + policy_input["target_price_change"])
    return "target_price", max(new_price, 0.0)


def s_sigma(params, _substep, _state_history, state_current, policy_input, **_kwargs):
    new_sigma = state_current["sigma"] * (1.0 + policy_input["sigma_change"])
    return "sigma", max(new_sigma, params["min_sigma"])


def s_limit_price(params, _substep, _state_history, _state_current, _policy_input, **_kwargs):
    return "limit_price", float(params["limit_price"])
