import pandas as pd
import numpy as np
import re

def create_propensity_score_df(df):
    method_names = ["CCA_", "SMI_", "HD_", "MI_", "full_"]
    exclusion_values = df.iloc[:-1, 1:].values
    scenario_descriptions = df.iloc[-1, 1:].tolist()
    
    method_mapping = {
        "CCA_": "Complete Case Analysis",
        "SMI_": "Single Mode Imputation",
        "HD_": "Hot Deck Imputation",
        "MI_": "Multiple Imputation",
        "full_": "Full Data (Reference)"
    }
    
    sample_sizes = []
    rhos = []
    mechanisms = []
    missing_rates = []
    
    for desc in scenario_descriptions:
        if isinstance(desc, str):
            match = re.search(r'Sample size: (\d+)', desc)
            sample_sizes.append(int(match.group(1)) if match else None)

            match = re.search(r'Rho: ([-\d.]+)', desc)
            rhos.append(float(match.group(1)) if match else None)
            
            match = re.search(r'Mechanism: (\w+(?:\(\w+\))?)', desc)
            mechanisms.append(match.group(1) if match else None)
            
            match = re.search(r'MissingRate: ([\d.]+)', desc)
            missing_rates.append(float(match.group(1)) if match else None)

        else:
            sample_sizes.append(None)
            rhos.append(None)
            mechanisms.append(None)
            missing_rates.append(None)
    
    structured_data = []
    
    for j, (sample_size, rho, mechanism, missing_rate) in enumerate(
        zip(sample_sizes, rhos, mechanisms, missing_rates)):
        for i, method in enumerate(method_names):
            if i < exclusion_values.shape[0] and j < exclusion_values.shape[1]:
                violation_rate = exclusion_values[i, j]
                
                violation_rate = float(violation_rate)
                structured_data.append({
                    'Method': method_mapping.get(method, method),
                    'Method_Code': method,
                    'Sample_Size': sample_size,
                    'Rho': rho,
                    'Mechanism': mechanism,
                    'Missing_Rate': missing_rate,
                    'Violation_Rate': violation_rate
                })
    
    result_df = pd.DataFrame(structured_data)
    
    if not result_df.empty:
        print("Propensity Score Violation Analysis:")
        print(f"Total records: {len(result_df)}")
        print(f"Scenarios: {result_df[['Sample_Size', 'Rho', 'Mechanism', 'Missing_Rate']].drop_duplicates().shape[0]}")
        print(f"Methods: {result_df['Method'].unique()}")
        print(result_df.head(10))
        
        print("\nViolation Rate Summary by Method:")
        summary = result_df.groupby('Method')['Violation_Rate'].agg(['mean', 'std', 'min', 'max', 'count']).round(3)
        print(summary)
        
        return result_df

def analyse_extreme_propensity(df):
    # parameter mappings
    param_mappings = {
        'Sample_Size': {
            'SMALL': 1000,
            'LARGE': 5000
        },
        'Rho': {
            'LOW': -0.1,
            'MEDIUM': -0.4,
            'HIGH': -0.7
        },
        'Mechanism': {
            "MCAR": "MCAR",
            "MAR(A)": "MAR",
            "MNAR": "MNAR",
            "MAR(Y)": "MARY"
        },
        'Missing_Rate': {
            'LOW': 0.2,
            'HIGH': 0.5
        }
    }
    
    if df.empty:
        print("No data to analyze.")
        return
    
    reverse_mappings = {}
    for param, mapping in param_mappings.items():
        reverse_mappings[param] = {v: k for k, v in mapping.items()}
    
    df_with_levels = df.copy()
    for param in ['Sample_Size', 'Rho', 'Mechanism', 'Missing_Rate']:
        level_col = f'{param}_Level'
        if param == 'Mechanism':
            df_with_levels[level_col] = df_with_levels[param].map(
                lambda x: reverse_mappings[param].get(x, 'UNKNOWN')
            )
        else:
            df_with_levels[level_col] = df_with_levels[param].map(
                lambda x: reverse_mappings[param].get(x, 'UNKNOWN')
            )
    
    summary_data = []
    for param in ['Sample_Size', 'Rho', 'Mechanism', 'Missing_Rate']:
        level_col = f'{param}_Level'
        
        levels = df_with_levels[level_col].unique()
        levels = [l for l in levels if l != 'UNKNOWN']
        
        for level in sorted(levels):
            level_data = df_with_levels[df_with_levels[level_col] == level]
            method_violations = level_data.groupby('Method')['Violation_Rate'].mean()
            row = {
                'Parameter': param.replace('_', ' '),
                'Level': level,
                'Parameter_Level': f"{param.replace('_', ' ')} - {level}"
            }
            
            # add violation rates for each method
            for method in df_with_levels['Method'].unique():
                if method in method_violations:
                    row[method] = round(method_violations[method], 4)
                else:
                    row[method] = 0.0
            
            summary_data.append(row)
    
    summary_df = pd.DataFrame(summary_data)
    method_cols = [col for col in summary_df.columns if col not in ['Parameter', 'Level', 'Parameter_Level']]
    summary_df = summary_df[['Parameter', 'Level', 'Parameter_Level'] + method_cols]
    display_df = summary_df.set_index('Parameter_Level')[method_cols]
    
    print("PROPENSITY SCORE VIOLATIONS BY PARAMETER LEVEL AND METHOD")
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', 20)
    
    print(display_df.round(4))
    
    print("SUMMARY STATISTICS")
    overall_by_method = df.groupby('Method')['Violation_Rate'].agg(['mean', 'max', 'count'])
    print("\nOverall violation rates by method:")
    print(overall_by_method.round(4))
    
    print("\nTop 5 highest violation scenarios:")
    top_violations = df.nlargest(5, 'Violation_Rate')[['Method', 'Sample_Size', 'Rho', 'Mechanism', 'Missing_Rate', 'Violation_Rate']]
    print(top_violations.round(4))
    
    exceedingThreshold = df[df['Violation_Rate'] > 0.05]
    if not exceedingThreshold.empty:
        print(f"\nExceeding threshold violations (>5%): {len(exceedingThreshold)} out of {len(df)} scenarios")
        print("By method:")
        exceeding_by_method = exceedingThreshold.groupby('Method').size()
        print(exceeding_by_method)
    
    return display_df, summary_df
    


csv_path = 'C:/Users/the_o/Desktop/Dissertation/MissingnessSimulation/MissingnessSim/python_missingness_extension/violation_summary.csv'
df = pd.read_csv(csv_path)
violations_df = create_propensity_score_df(df)
analyse_extreme_propensity(violations_df)