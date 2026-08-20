import pandas as pd
import numpy as np

def apply_method_hot_deck_imputation(df, missingVariables): # random hot deck
    df_imputed = df.copy()
    
    # select strata variables from the dataframe
    potential_strata = [col for col in df.columns if col not in missingVariables]
    
    # if there are no potential strata, use all columns except the current missing one
    if not potential_strata:
        strata_vars = [col for col in df.columns if col != missingVariables[0]][:6]
    else:
        # use first 6 (or fewer if not available) non-missing columns as strata
        strata_vars = potential_strata[:min(6, len(potential_strata))]
    
    for col in missingVariables:
        missing_mask = df_imputed[col].isnull()
        
        for idx in df_imputed[missing_mask].index:
            # relax if no donors
            for num_strata in range(len(strata_vars), 0, -1):
                donor_mask = pd.Series(True, index=df.index)
                
                # match on first num_strata variables
                for var in strata_vars[:num_strata]:
                    donor_mask &= (df[var] == df_imputed.loc[idx, var])
                
                potential_donors = df[donor_mask & df[col].notna()]
                
                if len(potential_donors) >= 3:
                    donor_value = np.random.choice(potential_donors[col].values)
                    df_imputed.loc[idx, col] = donor_value
                    break
            else:
                # Final fallback
                available_values = df[col].dropna().values
                df_imputed.loc[idx, col] = np.random.choice(available_values)
    
    return df_imputed