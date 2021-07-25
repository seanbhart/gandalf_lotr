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
