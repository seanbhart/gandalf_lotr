from model.parts.lotr import (
    p_execution_check,
    s_executed,
    s_execution_failed,
    s_execution_value,
    s_failure_reason,
    s_limit_token_price,
    s_pair_value,
    s_previous_price_direction,
    s_redeemed,
    s_redemption_value,
    s_redeem_token_price,
)
from model.parts.market import (
    p_sigma_change,
    p_target_price_change,
    s_limit_price,
    s_sigma,
    s_target_price,
)


partial_state_update_blocks = [
    {
        "policies": {
            "target_price_change": p_target_price_change,
            "sigma_change": p_sigma_change,
        },
        "variables": {
            "target_price": s_target_price,
            "sigma": s_sigma,
            "limit_price": s_limit_price,
        },
    },
    {
        "policies": {
            "execution": p_execution_check,
        },
        "variables": {
            "limit_token_price": s_limit_token_price,
            "redeem_token_price": s_redeem_token_price,
            "pair_value": s_pair_value,
            "executed": s_executed,
            "execution_failed": s_execution_failed,
            "failure_reason": s_failure_reason,
            "execution_value": s_execution_value,
            "redeemed": s_redeemed,
            "redemption_value": s_redemption_value,
            "previous_price_direction": s_previous_price_direction,
        },
    },
]
