import pandas as pd
import numpy as np

def simulate_MAR(df, target_var, predictor, missing_percent, seed=None, max_miss_rate=0.95):
    df = df.copy()
    # remove rows where predictor has NaN values
    df = df.dropna(subset=[predictor])
    if seed is not None:
        np.random.seed(seed)
    
    # create different probabilities for each category
    unique_cats = np.sort(df[predictor].unique())
    prob_dict = {}
    
    if len(unique_cats) == 2:
        freq_low = (df[predictor] == unique_cats[0]).mean()
        freq_high = (df[predictor] == unique_cats[1]).mean()
        
        mar_ratio = 5.0  # high category 5x more likely to be missing than low

        prob_low = missing_percent / (freq_low + freq_high * mar_ratio)
        prob_high = mar_ratio * prob_low

        # apply caps
        prob_low = min(max_miss_rate, prob_low)
        prob_high = min(max_miss_rate, prob_high)
        
        if prob_high == max_miss_rate:
            prob_low = max(0.01, prob_high / mar_ratio)
        
        prob_dict[unique_cats[0]] = prob_low
        prob_dict[unique_cats[1]] = prob_high
    else:
        frequencies = []
        for cat in unique_cats:
            freq = (df[predictor] == cat).mean()
            frequencies.append(freq)
        
        multipliers = []
        for i in range(len(unique_cats)):
            multiplier = 0.2 + (5 * i / (len(unique_cats) - 1))
            multipliers.append(multiplier)
        
        weighted_multipliers = sum(freq * mult for freq, mult in zip(frequencies, multipliers))
        base_prob = missing_percent / weighted_multipliers
        
        for i, cat in enumerate(unique_cats):
            prob_dict[cat] = min(max_miss_rate, base_prob * multipliers[i])
    
    # map probabilities to each row
    missing_probs = df[predictor].map(prob_dict)
    missing_probs = missing_probs.clip(upper=max_miss_rate)

    # generate missingness based on probabilities
    for cat in unique_cats:
        cat_mask = df[predictor] == cat
        cat_indices = df[cat_mask].index
        cat_prob = prob_dict[cat]
        n_missing = int(len(cat_indices) * cat_prob)
        
        # randomly select indices to make missing
        if n_missing > 0:
            missing_indices = np.random.choice(cat_indices, n_missing, replace=False)
            df.loc[missing_indices, target_var] = np.nan

    return df