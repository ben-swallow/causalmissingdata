import pandas as pd
import numpy as np

def apply_method_single_imputation(df, missingVariables):
    df_imputed = df.copy()
    
    for col in missingVariables:
        missing_mask = df_imputed[col].isnull()
        
        # mode imputation
        fill_value = df[col].mode()[0]
            
        df_imputed.loc[missing_mask, col] = fill_value
    
    return df_imputed


