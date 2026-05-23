from __future__ import annotations

from radcad import Experiment, Model, Simulation

from model.partial_state_update_block import partial_state_update_blocks
from model.sim_params import MONTE_CARLO_RUNS, SIMULATION_TIMESTEPS
from model.state_variables import initial_state
from model.sys_params import system_params


def make_model(params=None, state=None) -> Model:
    return Model(
        initial_state=state or initial_state,
        state_update_blocks=partial_state_update_blocks,
        params=params or system_params,
    )


def make_simulation(
    params=None,
    state=None,
    timesteps: int = SIMULATION_TIMESTEPS,
    runs: int = MONTE_CARLO_RUNS,
) -> Simulation:
    return Simulation(
        model=make_model(params=params, state=state),
        timesteps=timesteps,
        runs=runs,
    )


def make_experiment(simulation=None) -> Experiment:
    return Experiment(simulations=[simulation or make_simulation()])
