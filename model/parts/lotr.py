from __future__ import annotations

from model.valuation import crossed_limit, price_direction, token_pair_values


def _effective_execution_value(params, state_current) -> float:
    gross_value = state_current["limit_price"]
    value_after_reward = gross_value * (1.0 - params["execution_reward_rate"])
    value_after_slippage = value_after_reward * (1.0 - params["dex_slippage_rate"])
    return max(value_after_slippage, 0.0)


def p_execution_check(params, _substep, _state_history, state_current, **_kwargs):
    if state_current["executed"] or state_current["redeemed"]:
        return {
            "should_execute": False,
            "execution_failed": state_current["execution_failed"],
            "failure_reason": state_current["failure_reason"],
            "should_redeem": False,
        }

    redemption_timestep = params["redemption_timestep"]
    should_redeem = bool(
        params["redeemer_has_pair"]
        and redemption_timestep is not None
        and state_current["timestep"] >= redemption_timestep
    )

    if should_redeem:
        return {
            "should_execute": False,
            "execution_failed": False,
            "failure_reason": "",
            "should_redeem": True,
        }

    should_execute = crossed_limit(
        state_current["previous_price_direction"],
        state_current["target_price"],
        state_current["limit_price"],
    )
    failure_reason = ""
    execution_failed = False

    if should_execute and not params["oracle_available"]:
        execution_failed = True
        failure_reason = "oracle_unavailable"
    elif should_execute and not params["dex_available"]:
        execution_failed = True
        failure_reason = "dex_unavailable"
    elif should_execute and params["dex_liquidity"] < state_current["limit_price"]:
        execution_failed = True
        failure_reason = "insufficient_dex_liquidity"

    return {
        "should_execute": should_execute,
        "execution_failed": execution_failed,
        "failure_reason": failure_reason,
        "should_redeem": False,
    }


def s_limit_token_price(params, _substep, _state_history, state_current, _policy_input, **_kwargs):
    value, _redeem, _pair = token_pair_values(
        state_current["target_price"],
        state_current["limit_price"],
        state_current["sigma"],
        params["transfer_fee_rate"],
    )
    return "limit_token_price", value


def s_redeem_token_price(params, _substep, _state_history, state_current, _policy_input, **_kwargs):
    _limit, redeem, _pair = token_pair_values(
        state_current["target_price"],
        state_current["limit_price"],
        state_current["sigma"],
        params["transfer_fee_rate"],
    )
    return "redeem_token_price", redeem


def s_pair_value(params, _substep, _state_history, state_current, _policy_input, **_kwargs):
    _limit, _redeem, pair = token_pair_values(
        state_current["target_price"],
        state_current["limit_price"],
        state_current["sigma"],
        params["transfer_fee_rate"],
    )
    return "pair_value", pair


def s_executed(_params, _substep, _state_history, state_current, policy_input, **_kwargs):
    if state_current["executed"]:
        return "executed", True
    return "executed", bool(policy_input["should_execute"] and not policy_input["execution_failed"])


def s_execution_failed(_params, _substep, _state_history, state_current, policy_input, **_kwargs):
    return "execution_failed", bool(state_current["execution_failed"] or policy_input["execution_failed"])


def s_failure_reason(_params, _substep, _state_history, state_current, policy_input, **_kwargs):
    if state_current["failure_reason"]:
        return "failure_reason", state_current["failure_reason"]
    return "failure_reason", policy_input["failure_reason"]


def s_execution_value(params, _substep, _state_history, state_current, policy_input, **_kwargs):
    if state_current["execution_value"]:
        return "execution_value", state_current["execution_value"]
    if policy_input["should_execute"] and not policy_input["execution_failed"]:
        return "execution_value", _effective_execution_value(params, state_current)
    return "execution_value", 0.0


def s_redeemed(_params, _substep, _state_history, state_current, policy_input, **_kwargs):
    if state_current["redeemed"]:
        return "redeemed", True
    return "redeemed", bool(policy_input["should_redeem"])


def s_redemption_value(params, _substep, _state_history, state_current, policy_input, **_kwargs):
    if state_current["redemption_value"]:
        return "redemption_value", state_current["redemption_value"]
    if policy_input["should_redeem"]:
        return "redemption_value", state_current["limit_price"] * (1.0 - params["transfer_fee_rate"])
    return "redemption_value", 0.0


def s_previous_price_direction(_params, _substep, _state_history, state_current, _policy_input, **_kwargs):
    return "previous_price_direction", price_direction(
        state_current["target_price"],
        state_current["limit_price"],
    )
