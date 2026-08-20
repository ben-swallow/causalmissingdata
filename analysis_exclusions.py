import pandas as pd
import numpy as np
import re

def analyse_exclusions(csv_path='exclusion_summary.csv'):
    df = pd.read_csv(csv_path)
    
    method_names = ["CCA_", "SMI_", "HD_", "MI_", "full_"]
    exclusion_values = df.iloc[:-1, 1:].values
    method_mapping = {
        "CCA_": "Complete Case Analysis",
        "SMI_": "Single Mode Imputation",
        "HD_": "Hot Deck Imputation",
        "MI_": "Multiple Imputation",
        "full_": "Full Data (Reference)"
    }
    
    method_data = []
    for i, method in enumerate(method_names):
        if i < exclusion_values.shape[0]:
            values = exclusion_values[i]
            numeric_values = pd.to_numeric(values, errors='coerce')
            
            if not np.all(np.isnan(numeric_values)):
                method_data.append({
                    'Method': method_mapping.get(method, method),
                    'Mean': np.nanmean(numeric_values),
                    'Median': np.nanmedian(numeric_values),
                    'Min': np.nanmin(numeric_values),
                    'Max': np.nanmax(numeric_values),
                    'Count': np.sum(~np.isnan(numeric_values))
                })

    result_df = pd.DataFrame(method_data)

    if not result_df.empty and 'Mean' in result_df.columns:
        result_df = result_df.sort_values('Mean', ascending=False)
        print("EXCLUSION RATES BY METHOD")
        print(result_df.round(2))
        analyse_by_sample_size(df, method_names, method_mapping)
        analyse_by_missing_rate(df, method_names, method_mapping)

        return result_df


def analyse_by_sample_size(df, method_names, method_mapping):
    exclusion_values = df.iloc[:-1, 1:].values
    scenario_descriptions = df.iloc[-1, 1:].tolist()
    
    sample_sizes = []
    for desc in scenario_descriptions:
        if isinstance(desc, str):
            match = re.search(r'Sample size: (\d+)', desc)
            if match:
                sample_sizes.append(int(match.group(1)))
            else:
                sample_sizes.append(None)
        else:
            sample_sizes.append(None)
    
    structured_data = []
    for i, method in enumerate(method_names):
        if i < exclusion_values.shape[0]:
            method_display = method_mapping.get(method, method)
            
            for j, sample_size in enumerate(sample_sizes):
                if j < exclusion_values.shape[1] and sample_size is not None:
                    exclusion_rate = exclusion_values[i, j]
                    
                    exclusion_rate = float(exclusion_rate)
                    structured_data.append({
                        'Method': method_display,
                        'Sample Size': sample_size,
                        'Exclusion Rate': exclusion_rate
                    })
    
    method_sample_df = pd.DataFrame(structured_data)
    
    if not method_sample_df.empty:
        summary = method_sample_df.groupby(['Method', 'Sample Size'])['Exclusion Rate'].agg(['mean', 'count']).reset_index()
        summary.columns = ['Method', 'Sample Size', 'Mean Exclusion Rate', 'Count']
        summary = summary.sort_values(['Method', 'Sample Size'])
        
        print("EXCLUSION RATES BY METHOD AND SAMPLE SIZE")
        print(summary.round(2))

        return summary

def analyse_by_missing_rate(df, method_names, method_mapping):
    exclusion_values = df.iloc[:-1, 1:].values
    
    scenario_descriptions = df.iloc[-1, 1:].tolist()

    # DEBUG: Print some scenario descriptions to see the format
    print("DEBUG: Sample scenario descriptions")
    for i, desc in enumerate(scenario_descriptions[:5]):
        print(f"Description {i}: {desc}")

    missing_rates = []
    for desc in scenario_descriptions:
        if isinstance(desc, str):
            match = re.search(r'MissingRate: ([\d.]+)', desc)
            if match:
                missing_rates.append(float(match.group(1)))
            else:
                missing_rates.append(None)
        else:
            missing_rates.append(None)
    
    structured_data = []
    for i, method in enumerate(method_names):
        if i < exclusion_values.shape[0]:
            method_display = method_mapping.get(method, method)
            
            for j, missing_rate in enumerate(missing_rates):
                if j < exclusion_values.shape[1] and missing_rate is not None:
                    exclusion_rate = exclusion_values[i, j]
                    
                    exclusion_rate = float(exclusion_rate)
                    structured_data.append({
                        'Method': method_display,
                        'Missing Rate': missing_rate,
                        'Exclusion Rate': exclusion_rate
                    })
    
    method_missing_df = pd.DataFrame(structured_data)
    
    if not method_missing_df.empty:
        summary = method_missing_df.groupby(['Method', 'Missing Rate'])['Exclusion Rate'].agg(['mean', 'count']).reset_index()
        summary.columns = ['Method', 'Missing Rate', 'Mean Exclusion Rate', 'Count']
        summary = summary.sort_values(['Method', 'Missing Rate'])
        
        print("EXCLUSION RATES BY METHOD AND MISSING RATE")
        print(summary.round(3))

        return summary

if __name__ == "__main__":
    exclusion_results = analyse_exclusions()