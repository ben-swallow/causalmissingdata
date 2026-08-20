import pandas as pd
import pingouin as pg
from pyparsing import col
from postprocess_results import post_process_simulation_results
from analysis_marginal_ANOVA import convert_df_for_analysis
import matplotlib.pyplot as plt
import numpy as np

def getSERatio(df):
    se_ratios = []
    
    for method, group in df.groupby('method'):
        mean_estimated_se = group['model_se_avg'].mean()
        empirical_se = group['empirical_se_avg'].mean()
        
        se_ratio = mean_estimated_se / empirical_se
        
        se_ratios.append({
            'method': method,
            'mean_estimated_se': round(mean_estimated_se, 4),
            'empirical_se': round(empirical_se, 4),
            'se_ratio': round(se_ratio, 3),
            'n_simulations': len(group)
        })
    
    se_ratio_df = pd.DataFrame(se_ratios)
    
    print("SE Ratio by Method for A1 (Mean Estimated SE / Empirical SE)")
    print("=" * 50)
    print("Ideal SE ratio ≈ 1.0")
    print(se_ratio_df.to_string(index=False))
    
    return se_ratio_df
    
    

input_csv_path = 'C:/Users/the_o/Desktop/Dissertation/MissingnessSimulation/MissingnessSim/python_missingness_extension/all_scenario_results.csv'
df = post_process_simulation_results(input_csv_path, conditioningDict={"sample_size": 1000})
df = convert_df_for_analysis(df)
getSERatio(df)

df = post_process_simulation_results(input_csv_path, conditioningDict={"sample_size": 5000})
df = convert_df_for_analysis(df)
getSERatio(df)