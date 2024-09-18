# ebbflow

`ebbflow` is a Python package designed for running mechanistic models.

## Features

- Compatible with SciPy's `solve_ivp` solver.
- Captures model intermediates at specified time points.
- Exports results to a pandas DataFrame for analysis.

## Installation

You can install `ebbflow` directly from PyPI:

```bash
pip install ebbflow
```

## Quickstart

To use ```ebbflow``` you start by defining a new class that inherits BaseMechanisticModel:

In the ```__init__``` of this class you pass all the constants as arguments. You can also provide a list of variables to include in the output. These are values that you can set each time you initalize a new model.

The ```model``` method is where you define the model calculations. This must take time (t) and state_vars as the arguments. Once you have defined all the calculation steps it is important to call ```self.save()```. This allows the class to capture all the intermediate values in your model during the integration. Finally, the ```model``` method should return a list of differentials. Make sure the order of the differentials matches the order of the state_vars. 

```python
from ebbflow import BaseMechanisticModel

class DemoModel(BaseMechanisticModel):
    def __init__(self, kAB, kBO, YBAB, vol, outputs):
        self.kAB = kAB        
        self.kBO = kBO
        self.YBAB = YBAB
        self.vol = vol        
        self.outputs = outputs
    
    def model(self, t, state_vars):
        kAB = self.kAB
        kBO = self.kBO
        YBAB = self.YBAB
        vol = self.vol

        # Variables with Differential Equation #
        A = state_vars[0]
        B = state_vars[1]

        # Model Equations # 
        concA = A/vol
        concB = B/vol
        UAAB = kAB*concA
        PBAB = UAAB*YBAB
        UBBO = kBO*concB

        # Differential Equations # 
        dAdt = -UAAB
        dBdt = PBAB - UBBO

        self.save()
        return [dAdt, dBdt]
```

With the model defined we can now set the parameters and run an integration. First, we create an instance of our class. In this example we call it `demo`. We set the value of our parameters using and specify the variable to include in the output. 

```python
demo = DemoModel(
    kAB=0.42, kBO=0.03, YBAB=1.0, vol=1.0, 
    outputs=['t', 'A', 'B', 'concA', 'concB', 'dAdt']
    )
```

We can now call the `run_model` method to perform an integration. We select the solver method to use (RK4), the time span to integrate (t_span), the initial state variables (y0), the evaluation times (t_eval) and the integration interval for RK4.

```python
demo.run_model(
    "RK4", t_span=(0, 120), y0=[3.811, 4.473], t_eval=np.arange(0,121,10),
    integ_interval=0.001
    )
```

After the model finishes running we can export the results to a dataframe for analysis.

```python
df = demo.to_dataframe()
print(df)
```

This will print the results at the times based on ```t_eval```.

```
          t             A         B         concA     concB          dAdt
0     0.000  3.809400e+00  4.474466  3.809400e+00  4.474466 -1.599948e+00
1     9.999  5.714814e-02  6.292568  5.714814e-02  6.292568 -2.400222e-02
2    19.999  8.569694e-04  4.706319  8.569694e-04  4.706319 -3.599271e-04
3    29.999  1.285075e-05  3.487197  1.285075e-05  3.487197 -5.397315e-06
4    39.999  1.927044e-07  2.583389  1.927044e-07  2.583389 -8.093585e-08
5    49.999  2.889714e-09  1.913822  2.889714e-09  1.913822 -1.213680e-09
6    59.999  4.333292e-11  1.417794  4.333292e-11  1.417794 -1.819983e-11
7    69.999  6.498022e-13  1.050328  6.498022e-13  1.050328 -2.729169e-13
8    79.999  9.744159e-15  0.778102  9.744159e-15  0.778102 -4.092547e-15
9    89.999  1.461193e-16  0.576432  1.461193e-16  0.576432 -6.137010e-17
10   99.999  2.191143e-18  0.427031  2.191143e-18  0.427031 -9.202800e-19
11  109.999  3.285745e-20  0.316353  3.285745e-20  0.316353 -1.380013e-20
12  119.999  4.927164e-22  0.234360  4.927164e-22  0.234360 -2.069409e-22
```

When using the "RK4" equation we can continue running our model from a previous time point. This allows us to start a model with a set of constants then moddify these constants at a chosen timepoint. 

```python
# This will create a list with our 2 state variables, A and B
new_stateVars =  df.iloc[-1, df.columns.isin(['A', 'B'])].tolist()

# We change the value of kAB
model.change_constants({"kAB": 0.5})

# Next we run the model with the new initial values and time span
model.run_model(
    "RK4", t_span=(120, 220), y0=new_stateVars, t_eval=np.arange(120,221,10), 
    integ_interval=0.01, prev_output=result
    )

new_result = model.to_dataframe()
display(new_result)
```

As you can see this model run starts at t=120 and goes to the new stop time of 220.

```
kAB updated to 0.5
Running Model...
t	A	B	concA	concB	dAdt
0	129.98	3.319897e-24	0.173618	3.319897e-24	0.173618	-1.659949e-24
1	139.98	2.236929e-26	0.128619	2.236929e-26	0.128619	-1.118465e-26
2	149.98	1.507231e-28	0.095284	1.507231e-28	0.095284	-7.536155e-29
3	159.98	1.015564e-30	0.070588	1.015564e-30	0.070588	-5.077821e-31
4	169.98	6.842818e-33	0.052293	6.842818e-33	0.052293	-3.421409e-33
5	179.98	4.610655e-35	0.038739	4.610655e-35	0.038739	-2.305327e-35
6	189.98	3.106635e-37	0.028699	3.106635e-37	0.028699	-1.553317e-37
7	199.98	2.093234e-39	0.021261	2.093234e-39	0.021261	-1.046617e-39
8	209.98	1.410410e-41	0.015750	1.410410e-41	0.015750	-7.052050e-42
9	219.98	9.503268e-44	0.011668	9.503268e-44	0.011668	-4.751634e-44
```