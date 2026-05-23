from __future__ import annotations

import math


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def price_direction(target_price: float, limit_price: float) -> str:
    if target_price > limit_price:
        return "above"
    if target_price < limit_price:
        return "below"
    return "at"


def crossed_limit(previous_direction: str, target_price: float, limit_price: float) -> bool:
    current_direction = price_direction(target_price, limit_price)
    return current_direction == "at" or (
        previous_direction in {"above", "below"}
        and current_direction in {"above", "below"}
        and current_direction != previous_direction
    )


def limit_token_value(
    target_price: float,
    limit_price: float,
    sigma: float,
    transfer_fee_rate: float = 0.0,
) -> float:
    if limit_price <= 0:
        raise ValueError("limit_price must be positive")
    if sigma < 0:
        raise ValueError("sigma must be non-negative")

    if target_price > limit_price:
        spread = limit_price - target_price
    else:
        spread = target_price - limit_price

    value = limit_price * math.exp(sigma * spread)
    collateral_after_fees = limit_price * (1.0 - transfer_fee_rate)
    return clamp(value, 0.0, collateral_after_fees)


def redeem_token_value(
    target_price: float,
    limit_price: float,
    sigma: float,
    transfer_fee_rate: float = 0.0,
) -> float:
    collateral_after_fees = limit_price * (1.0 - transfer_fee_rate)
    return collateral_after_fees - limit_token_value(
        target_price,
        limit_price,
        sigma,
        transfer_fee_rate,
    )


def token_pair_values(
    target_price: float,
    limit_price: float,
    sigma: float,
    transfer_fee_rate: float = 0.0,
) -> tuple[float, float, float]:
    limit_value = limit_token_value(target_price, limit_price, sigma, transfer_fee_rate)
    redeem_value = redeem_token_value(target_price, limit_price, sigma, transfer_fee_rate)
    return limit_value, redeem_value, limit_value + redeem_value
