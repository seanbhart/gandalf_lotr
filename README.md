# LIMIT ORDER TOKEN RESERVE MODEL

## ENV SETUP

```
virtualenv .lotr
source .lotr/bin/activate
git init
pip install jupyterlab cadCAD cadCAD_diagram matplotlib pandas plotly ipywidgets numpy networkx scipy seaborn
jupyter labextension install jupyterlab-plotly
python -m ipykernel install --user --name=.lotr
```

```
mkdir model && cd model
touch __init__.py
touch  config.py
touch  partial_state_update_block.py
touch  run.py
touch  sim_params.py
touch  state_variables.py
touch  sys_params.py
mkdir parts && cd parts
touch __init__.py
```

## RUN

```
jupyter-lab
jupyter notebook [OLD]
```

## radCAD model

The importable model in `model/` ports the LOTR valuation logic from the
notebooks to radCAD and adds first-pass execution edge cases.

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m model.run --timesteps 30 --runs 1
python -m model.report --output-dir reports
pytest
```

Core invariant: the Limit Token and Redeem Token values sum to the limit price
minus configured transfer fees. Execution is triggered when the target price
crosses the limit price, with parameters for oracle availability, DEX
availability, DEX liquidity, slippage, and execution reward fees.

Generated scenario outputs:

- `reports/lotr_scenario_records.csv`
- `reports/lotr_scenario_summary.csv`
- `reports/lotr_dashboard.html`
- `reports/lotr_scenario_report.ipynb`
