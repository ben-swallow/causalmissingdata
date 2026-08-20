import pandas as pd

def apply_method_complete_case(dataframe, missingVariables):
    if missingVariables is None:
        missingVariables = []
    
    exclude_rows = pd.Series(False, index=dataframe.index)
    
    for var in missingVariables:
    # check if variable is A1 or A2 which need special handling for structural missingness
        if var in ['A1', 'A2']:
            censoring_var = f'censoring{var}'
            var_missing = dataframe[var].isna()
            var_structural = dataframe[censoring_var] == 1
            var_nonstructural_missing = var_missing & ~var_structural
            exclude_rows |= var_nonstructural_missing
        else:
            var_missing = dataframe[var].isna()
            exclude_rows |= var_missing
    
    #print(f"Excluding {exclude_rows.sum()} rows due to missing values in specified variables.")
    # keep rows that are NOT excluded
    complete_cases = dataframe[~exclude_rows].copy()
    #print(f"Total excluded: {exclude_rows.sum()}")
    #print(f"Final sample size: {len(dataframe) - exclude_rows.sum()}")
    
    #print(f"Number of complete cases after exclusion: {len(complete_cases)}")
    return complete_cases