import numpy as np
import pandas as pd

def simulate_MCAR(df, target_var, missing_fraction, seed):
    df = df.copy()

    if seed is not None:
        np.random.seed(seed)

    # only consider rows where the variable is currently observed
    observed_indices = df[df[target_var].notnull()].index
    n_to_mask = max(1, int(np.floor(missing_fraction * len(observed_indices))))

    if n_to_mask == 0:
        return df, df[target_var].notnull().values

    missing_indices = np.random.choice(observed_indices, size=n_to_mask, replace=False)
    df.loc[missing_indices, target_var] = np.nan

    return df