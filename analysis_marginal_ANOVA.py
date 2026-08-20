import numpy as np
import pandas as pd
import pingouin as pg
from postprocess_results import post_process_simulation_results
import matplotlib.pyplot as plt

from statsmodels.stats.anova import anova_lm
from statsmodels.formula.api import ols
import numpy as np
import re

def convert_df_for_analysis(df = None):
    # csv_path = "MissingnessSim/python_missingness_extension/all_scenario_results.csv"

    # if df is None:
    #     df = pd.read_csv(csv_path)

    df['scenario_id'] = (df['mechanism'].astype(str) + '_' + 
                        df['missing_rate'].astype(str) + '_' + 
                        df['rho'].astype(str) + '_' + 
                        df['sample_size'].astype(str) + '_' + 
                        df['target_vars'].astype(str) + '_' + 
                        df['method'].astype(str))

    # convert to categorical for efficiency
    df['scenario_id'] = df['scenario_id'].astype('category')
    df['scenario_id'] = df['scenario_id'].str.replace(',', '', regex=False)
    
    return df

def convert_by_parameter(df):
    # parameter mappings
    param_mappings = {
        'sample_size': {
            'SMALL': 1000,
            'LARGE': 5000
        },
        'rho': {
            'LOW': -0.1,
            'MEDIUM': -0.4,
            'HIGH': -0.7
        },
        'mechanism': {
            "MCAR": "MCAR",
            "MAR(A)": "MAR(A)",
            "MNAR": "MNAR",
            "MAR(Y)": "MAR(Y)"
        },
        'missing_rate': {
            'LOW': 0.2,
            'HIGH': 0.5
        }
    }
    
    # dictionary to store results
    split_dataframes = {}
    
    # split by each parameter
    for param_name, level_mapping in param_mappings.items():
        split_dataframes[param_name] = []
        
        print(f"\n=== Splitting by {param_name.upper()} ===")
        
        for level_name, level_value in level_mapping.items():
            # filter dataframe for this parameter level
            if param_name in df.columns:
                subset_df = df[df[param_name] == level_value].copy()
                
                print(f"{level_name} ({level_value}): {len(subset_df)} rows")
                
                # store as level_name, dataframe
                split_dataframes[param_name].append((level_name, subset_df))
            else:
                print(f"Warning: Column '{param_name}' not found in dataframe")
    
    return split_dataframes

def run_ANOVA(df, dv, numInteractions=0, onlySignificant= False, ignoreColumnas=[]):
    print(f"\n{'='*60}")
    print(f"REPEATED MEASURES ANOVA ANALYSIS FOR: {dv.upper()}")
    print(f"{'='*60}")

    between = ['missing_rate', 'rho', 'sample_size', 'mechanism', 'method']
    if ignoreColumnas:
        between = [col for col in between if col not in ignoreColumnas]
    
    formula = f"{dv} ~ " + " + ".join([f"C({factor})" for factor in between])

    # first-order interactions between factors
    for i, factor1 in enumerate(between):
        for factor2 in between[i+1:]:  # Start from next factor to avoid duplicates
            formula += f" + C({factor1}):C({factor2})"

    print(f"Using formula with all first-order interactions: {formula}")
    
    model = ols(formula, data=df).fit()
    anova_result = anova_lm(model, typ=2)
    
    # calculate residual eta-squared (effect SS / total SS)
    ss_total = anova_result['sum_sq'].sum()
    anova_result['res_eta_sq'] = anova_result['sum_sq'] / ss_total
    
    highly_sig = anova_result[anova_result['PR(>F)'] < 0.001].copy()
    less_sig = anova_result[anova_result['PR(>F)'] >= 0.001].copy()
    highly_sig = highly_sig.sort_values(by='res_eta_sq', ascending=False)
    less_sig = less_sig.sort_values(by=['PR(>F)', 'res_eta_sq'], ascending=[True, False])

    residual_row = None
    if 'Residual' in anova_result.index:
        residual_row = anova_result.loc[['Residual']]
        highly_sig = highly_sig[~highly_sig.index.isin(['Residual'])]
        less_sig = less_sig[~less_sig.index.isin(['Residual'])]

    anova_result = pd.concat([highly_sig, less_sig])
    if residual_row is not None:
        anova_result = pd.concat([anova_result, residual_row])

    print(f"Total variance explained: {1 - anova_result.iloc[-1]['res_eta_sq']:.2%}")
    print(anova_result)
    
    print("\nANOVA Results:")
    print(anova_result.to_csv(index=False))

    print("\nSummary of Total Effects (Main + Interactions):")
    factor_total_effects = {}

    # total variacne explained by factor and interactions:
    # extract main factors from ANOVA
    main_factors = [col for col in between]
    interaction_pattern = r'C\((.*?)\):C\((.*?)\)'

    for factor in main_factors:
        factor_total_effects[factor] = 0.0

    # add main effects
    for idx in anova_result.index:
        idx_str = str(idx)
        for factor in main_factors:
            if idx_str == f"C({factor})":
                factor_total_effects[factor] += anova_result.loc[idx, 'res_eta_sq']
        
        # handle interaction effects
        match = re.search(interaction_pattern, idx_str)
        if match:
            factor1, factor2 = match.groups()
            # add interaction effect to toal variance explained by factor
            if factor1 in main_factors:
                factor_total_effects[factor1] += anova_result.loc[idx, 'res_eta_sq']
            if factor2 in main_factors:
                factor_total_effects[factor2] += anova_result.loc[idx, 'res_eta_sq']

    # sort by total effect size
    sorted_effects = sorted(factor_total_effects.items(), key=lambda x: x[1], reverse=True)

    effect_summary = pd.DataFrame(sorted_effects, columns=['Factor', 'Total η²'])
    effect_summary['Total η²'] = effect_summary['Total η²'].round(4)
    effect_summary['% of Variance'] = (effect_summary['Total η²'] * 100).round(2)

    print(effect_summary.to_string(index=False))



def analyze_by_method(df, dv_list=['bias_avg', 'coverage_avg', 'empirical_se_avg']):
    methods = df['method'].unique()
    results = {}
    
    for method in methods:
        print(f"\n\n{'='*80}")
        print(f"ANALYZING METHOD: {method}")
        print(f"{'='*80}")
        
        # filter by method
        method_df = df[df['method'] == method].copy()
        
        hyperparams = ['missing_rate', 'rho', 'sample_size', 'mechanism']
        
        for dv in dv_list:
            print(f"\n{'-'*60}")
            print(f"ANALYZING {dv.upper()} FOR {method}")
            print(f"{'-'*60}")
            
            formula = f"{dv} ~ " + " + ".join([f"C({param})" for param in hyperparams])
            
            for i, param1 in enumerate(hyperparams):
                for param2 in hyperparams[i+1:]:
                    formula += f" + C({param1}):C({param2})"
            
            # stats
            model = ols(formula, data=method_df).fit()
            anova_result = anova_lm(model, typ=2)
            ss_total = anova_result['sum_sq'].sum()
            anova_result['res_eta_sq'] = anova_result['sum_sq'] / ss_total
            
            highly_sig = anova_result[anova_result['PR(>F)'] < 0.001].copy()
            less_sig = anova_result[anova_result['PR(>F)'] >= 0.001].copy()
            
            highly_sig = highly_sig.sort_values(by='res_eta_sq', ascending=False)
            less_sig = less_sig.sort_values(by=['PR(>F)', 'res_eta_sq'], ascending=[True, False])
            
            residual_row = None
            if 'Residual' in anova_result.index:
                residual_row = anova_result.loc[['Residual']]
                highly_sig = highly_sig[~highly_sig.index.isin(['Residual'])]
                less_sig = less_sig[~less_sig.index.isin(['Residual'])]
            
            anova_result = pd.concat([highly_sig, less_sig])
            if residual_row is not None:
                anova_result = pd.concat([anova_result, residual_row])
            
            if method not in results:
                results[method] = {}
            results[method][dv] = anova_result
            
            print(f"Total variance explained: {1 - anova_result.iloc[-1]['res_eta_sq']:.2%}")
            print(anova_result)
    
    return results


if __name__ == "__main__":
    input_csv_path = 'C:/Users/the_o/Desktop/Dissertation/MissingnessSimulation/MissingnessSim/python_missingness_extension/all_scenario_results.csv'
    df = post_process_simulation_results(input_csv_path, conditioningDict={})
    
    #print(f"Length before filtering: {len(df)}")
    #df = df[(df['method'] != 'full_')].copy()
    #print(f"Length after filtering: {len(df)}")
    df = convert_df_for_analysis(df)

    run_ANOVA(df, 'bias_avg', numInteractions=1, onlySignificant=False, ignoreColumnas=[""])
    run_ANOVA(df, 'coverage_avg', numInteractions=1, onlySignificant=False, ignoreColumnas=[""])
    run_ANOVA(df, 'empirical_se_avg', numInteractions=1, onlySignificant=False, ignoreColumnas=[""])

    #print("\nANALYZING HYPERPARAMETERS WITHIN EACH METHOD")
    method_results = analyze_by_method(df) 
