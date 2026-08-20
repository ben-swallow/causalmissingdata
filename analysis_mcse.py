import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from analysis_marginal_ANOVA import convert_df_for_analysis, convert_by_parameter
from postprocess_results import post_process_simulation_results

input_csv_path = 'C:/Users/the_o/Desktop/Dissertation/MissingnessSimulation/MissingnessSim/python_missingness_extension/all_scenario_results.csv'
df = post_process_simulation_results(input_csv_path, conditioningDict={})

df = convert_df_for_analysis(df)

print("=== BIAS MCSE SUMMARY ===")
mcse_summary = df['bias_mcse_avg'].describe().round(4)
print(mcse_summary)

print("=== COVERAGE MCSE SUMMARY ===")
mcse_summary = df['coverage_mcse_avg'].describe().round(4)
print(mcse_summary)

print("=== EMPIRICAL MCSE SUMMARY ===")
mcse_summary = df['empirical_se_mcse_avg'].describe().round(4)
print(mcse_summary)


mcse_columns = ['bias_mcse_avg', 'empirical_se_mcse_avg', 'coverage_mcse_avg']
threshold = 0.05


# find rows where MCSE exceeds threshold
mcse_mask = df[mcse_columns] > threshold
high_mcse_rows = mcse_mask.any(axis=1)
high_mcse = df[high_mcse_rows].copy()

newDf = high_mcse[['scenario_id'] + mcse_columns]
newDf = newDf.sort_values(by='bias_mcse_avg', ascending=False)
print(f"Scenarios with any MCSE > {threshold}: {len(newDf)}")
newDf = newDf.round(4)
print(newDf.to_csv(index=False))

