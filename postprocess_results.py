import pandas as pd
import numpy as np

def post_process_simulation_results(input_csv_path, conditioningDict={}, coefficients=["A1"]):
    df = pd.read_csv(input_csv_path)
    measures = [
        'bias', 
        'empirical_se',
        'model_se', 
        'coverage', 
        'mse', 
        'rel_error_se',  
        'model_se',
        'uw_bias', 
        'uw_empirical_se',
        'uw_coverage',
        'empirical_se_mcse',
        'coverage_mcse',
        'bias_mcse'
    ]
    
    if coefficients is None:
        avail_coeffs = set()
        for col in df.columns:
            for measure in measures:
                prefix = f"{measure}_"
                if col.startswith(prefix):
                    coeff = col[len(prefix):]
                    avail_coeffs.add(coeff)
        coefficients = list(avail_coeffs)
    
    results = []
    for idx, row in df.iterrows():
        result_row = {}
        
        param_cols = ['method', 'mechanism', 'missing_rate', 'rho', 'sample_size', 
                     'target_vars', 'predictors']
        
        for col in param_cols:
            if col in row:
                result_row[col] = row[col]
        
        for measure in measures:
            values = []
            coeff_cols = []
            for coeff in coefficients:
                col_name = f'{coeff}_{measure}'
                if col_name in df.columns:
                    coeff_cols.append(col_name)
                    if not pd.isna(row[col_name]):
                        values.append(row[col_name])
            
            if values:
                avg_val = np.mean(values)
                range_val = np.max(values) - np.min(values)
                
                result_row[f'{measure}_avg'] = avg_val
                result_row[f'{measure}_range'] = range_val
                result_row[f'{measure}_min'] = np.min(values)
                result_row[f'{measure}_max'] = np.max(values)
        
        # Monte Carlo SE - only average
        mc_se_measures = ['bias_mcse', 'empirical_se_mcse', 'coverage_mcse']
        
        for measure in mc_se_measures:
            values = []
            for coeff in coefficients:
                col_name = f'{coeff}_{measure}'
                if col_name in df.columns and not pd.isna(row[col_name]):
                    values.append(row[col_name])
            
            if values:
                avg_val = np.mean(values)
                result_row[f'{measure}_avg'] = avg_val
        
        results.append(result_row)
    
    result_df = pd.DataFrame(results)
    
    print(f"Number of rows: {len(result_df)}")
    print(f"Coefficients included: {coefficients}")

    if conditioningDict and isinstance(conditioningDict, dict):
       for key, value in conditioningDict.items():
           if key in result_df.columns:
               result_df = result_df[result_df[key] != value]

    #if 'bias_avg' in result_df.columns:
    result_df['bias_avg'] = result_df['bias_avg'].abs()
    result_df['mechanism'] = result_df['mechanism'].replace('MARY', 'MAR(Y)')
    result_df['mechanism'] = result_df['mechanism'].replace('MAR', 'MAR(A)')
    
    print(f"Number of rows after filtering: {len(result_df)}")

    return result_df


# input_csv_path = 'C:/Users/the_o/Desktop/Dissertation/MissingnessSimulation/MissingnessSim/python_missingness_extension/all_scenario_results.csv'  # Path to the input CSV file
# post_process_simulation_results(input_csv_path)
