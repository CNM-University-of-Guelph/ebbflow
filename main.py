import time

import pandas as pd

from base_mechanistic_model import BaseMechanisticModel

class DemoModel(BaseMechanisticModel):
    def __init__(self, kAB, kBO, YBAB, vol, outputs):
        self.kAB = kAB        
        self.kBO = kBO
        self.YBAB = YBAB
        self.vol = vol        
        self.outputs = outputs
    
    def model(self, state_vars, t):
        kAB = self.kAB
        kBO = self.kBO
        YBAB = self.YBAB
        vol = self.vol

        # Variables w/ Differential Equation #
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


if __name__ == "__main__":
    def convert_list_to_dataframe(data: list):
        columns = ['t', 'A', 'B', 'concA', 'concB', 'dAdt']
        df = pd.DataFrame(data, columns=columns)
        return df

    print("Starting model run...")
    start_time = time.time()

    demo = DemoModel(
        kAB=0.42, kBO=0.03, YBAB=1.0, vol=1.0, 
        outputs=['t', 'A', 'B', 'concA', 'concB', 'dAdt']
    )
    result = demo.run_model(
        "RK4", t_span=(0, 120), y0=[3.811004739069482, 4.473254058347129],
        t_eval=10, integ_interval=0.001
        )
    
    elapsed_time = time.time() - start_time
    print(f"First model run completed in {elapsed_time:.4f} seconds.")

    df = convert_list_to_dataframe(result)
    print(df)

    # Test restarting from prev_output
    new_stateVars =  df.iloc[-1, df.columns.isin(['A', 'B'])].tolist()
    
    print("\nStarting second model run...")
    start_time = time.time()

    demo = DemoModel(
        kAB=0.5, kBO=0.03, YBAB=1.0, vol=1.0, 
        outputs=['t', 'A', 'B', 'concA', 'concB', 'dAdt']
    )
    result2 = demo.run_model(
        "RK4", t_span=(120, 220), y0=new_stateVars, t_eval=10, 
        integ_interval=0.01, prev_output=df
        )

    elapsed_time = time.time() - start_time
    print(f"Second model run completed in {elapsed_time:.4f} seconds.")

    df2 = convert_list_to_dataframe(result2)
    print(df2)
