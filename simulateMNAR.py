from simulateMAR import simulate_MAR
import pandas as pd
import numpy as np

def simulate_MNAR(df, target_var, missing_percent, seed=None, max_miss_rate=0.95):
    df = df.copy()
    if seed is not None:
        np.random.seed(seed)
    
    # create direct value-dependent missingness
    if df[target_var].nunique() <= 2:
        values = sorted(df[target_var].unique())
        low_val, high_val = values[0], values[1]

        # calculate frequencies
        freq_low = (df[target_var] == low_val).mean()
        freq_high = (df[target_var] == high_val).mean()
        
        mnar_ratio = 10.0  # high values 10x more likely to be missing

        prob_low = missing_percent / (freq_low + freq_high * mnar_ratio)
        prob_high = mnar_ratio * prob_low
        
        # apply caps
        prob_low = min(max_miss_rate, prob_low)
        prob_high = min(max_miss_rate, prob_high)

        # create probability map
        missing_probs = df[target_var].map({low_val: prob_low, high_val: prob_high})
        
        # generate missingness
        random_draws = np.random.uniform(0, 1, len(df))
        missing_mask = random_draws < missing_probs
        
        df.loc[missing_mask, target_var] = np.nan
        
    else:
        # for categorical variables, use existing MAR function
        df = simulate_MAR(df, target_var, target_var, missing_percent, seed, max_miss_rate)
    
    return df