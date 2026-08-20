# Python script for adding missingness patterns to longitudinal data
import pandas as pd
import numpy as np
from simulateMAR import simulate_MAR
from simulateMCAR import simulate_MCAR
from simulateMNAR import simulate_MNAR
from method_completeCase import apply_method_complete_case
from method_singleImputation import apply_method_single_imputation
from method_hotDeck import apply_method_hot_deck_imputation
import math

strCensoringA1 = "censoringA1"
strCensoringA2 = "censoringA2"

def pipeline_python(df, mechanism, target_vars, predictors, missing_percent, method):
    original_values = {}
    for var in target_vars:
            if var in df.columns:
                original_values[var] = df[var].copy()

    #df_original = df.copy()
    
    try:
        df, colA1, colA2 = preprocess_dataframe(df) # preprocess dataframe
        #print("preprocessed dataframe")
    except Exception as e:
        print(mechanism, target_vars, predictors, missing_percent, method)
        print(f"An error occurred in preprocess_dataframe: {e}")
        raise e
    try:
        df = simulate_missingness(df, target_vars=target_vars, predictors=predictors, missing_type=mechanism, missing_percent=missing_percent) # Simulate missingness patterns
        #print("simulated missingness")
    except Exception as e:
        print(mechanism, target_vars, predictors, missing_percent, method)
        print(f"An error occurred in simulate_missingness: {e}")
        raise e
    
    # #Validation check for missingness patterns
    # try:
    #     if mechanism != "None" and method == "CCA":  # Only check for missingness when it's applied and before imputation
    #         validate_missingness(df, mechanism, target_vars, predictors, missing_percent, original_values)
    # except Exception as e:
    #     print(f"Warning: Missingness validation failed: {e}")
    
    try:
        df = run_method(df, method=method, target_vars=target_vars) # run methods on the data
        #print("ran method on data")
    except Exception as e:
        print(mechanism, target_vars, predictors, missing_percent, method)
        print(f"An error occurred in run_method: {e} - method: {method}")
        raise e

    # df_with_missing = df.copy()
    # distribution_comparison = compare_distributions(df_original, df_with_missing, df, target_vars, predictors)
    # print(f"\nDistribution Comparison for {method}:")
    # for key, value in distribution_comparison.items():
    #     print(f"\n{key}:")
    #     if "conditional" not in key:
    #         print(f"  Original: {value['original']}")
    #         print(f"  Observed: {value['observed']}")
    #         print(f"  Imputed:  {value['imputed']}")

    try:
        df = postprocess_dataframe(df, colA1, colA2, method, target_vars) # postprocess dataframe
        #print("postprocessed dataframe")
    except Exception as e:
        print(mechanism, target_vars, predictors, missing_percent, method)
        print(f"An error occurred in postprocess_dataframe: {e}")
        raise e
    

    return df

def validate_missingness(df, mechanism, target_vars, predictors, missing_percent, original_values):
    validation_results = {}
    
    for i, var in enumerate(target_vars):
        if var not in df.columns:
            continue
            
        actual_rate = df[var].isna().mean()
        rate_error = actual_rate - missing_percent
        
        validation_results[var] = {
            'mechanism': mechanism,
            'target_rate': missing_percent,
            'actual_rate': round(actual_rate, 3),
            'rate_error': round(rate_error, 3)
        }
        
        # Check mechanism-specific patterns
        if mechanism == 'MCAR':
            # For MCAR: Check if missingness is evenly distributed across arbitrary groups
            if len(predictors) > i:
                predictor = predictors[i]
                if predictor in df.columns and df[predictor].nunique() > 1:
                    group_rates = df.groupby(predictor)[var].apply(lambda x: x.isna().mean())
                    max_diff = group_rates.max() - group_rates.min()
                    validation_results[var]['group_diff'] = round(max_diff, 3)
        
        elif mechanism == 'MAR' or mechanism == 'MARY':
            # For MAR: Check if missingness depends on predictor
            if len(predictors) > i:
                predictor = predictors[i]
                if predictor in df.columns and df[predictor].nunique() > 1:
                    group_rates = df.groupby(predictor)[var].apply(lambda x: x.isna().mean())
                    max_diff = group_rates.max() - group_rates.min()
                    validation_results[var]['predictor_dependency'] = round(max_diff, 3)
        
        elif mechanism == 'MNAR':
            # For MNAR: Check if missingness depends on original values of the target
            if var in original_values:
                orig_series = original_values[var]
                
                if orig_series.nunique() > 1:
                    if not orig_series.index.equals(df.index):
                        orig_series = pd.Series(orig_series.values, index=df.index)
                    
                    if pd.api.types.is_numeric_dtype(orig_series):
                        median = orig_series.median()
                        high_vals = df[orig_series > median][var]
                        low_vals = df[orig_series <= median][var]
                    else:
                        most_common = orig_series.value_counts().idxmax()
                        high_vals = df[orig_series == most_common][var]
                        low_vals = df[orig_series != most_common][var]
                    
                    high_missing_rate = high_vals.isna().mean() if len(high_vals) > 0 else 0
                    low_missing_rate = low_vals.isna().mean() if len(low_vals) > 0 else 0
                    
                    val_diff = abs(high_missing_rate - low_missing_rate)
                    validation_results[var]['value_dependency'] = round(val_diff, 3)
    
    # Print validation summary
    print("\nMissingness Validation Summary:")
    print(f"Mechanism: {mechanism}, Target Rate: {missing_percent}")
    
    for var, results in validation_results.items():
        print(f"  Variable: {var}")
        print(f"    Actual Missing Rate: {results['actual_rate']} (error: {results['rate_error']})")
        
        if mechanism == 'MCAR' and 'group_diff' in results:
            print(f"    Group Difference: {results['group_diff']} (should be close to 0 for MCAR)")
        elif (mechanism == 'MAR' or mechanism == 'MARY') and 'predictor_dependency' in results:
            print(f"    Predictor Dependency: {results['predictor_dependency']} (should be > 0 for MAR)")
        elif mechanism == 'MNAR' and 'value_dependency' in results:
            print(f"    Value Dependency: {results['value_dependency']} (should be > 0 for MNAR)")
    
    return validation_results

def compare_distributions(df_original, df_with_missing, df_imputed, target_vars, predictors):
    results = {}
    
    # For each target variable with missingness
    for i, var in enumerate(target_vars):
        if var not in df_original.columns:
            continue
            
        # Get the corresponding predictor (if available)
        predictor = predictors[i] if i < len(predictors) else None
        
        # 1. Marginal distribution comparison
        results[f"{var}_marginal"] = {
            "original": df_original[var].value_counts(normalize=True).to_dict(),
            "observed": df_with_missing[var].dropna().value_counts(normalize=True).to_dict(),
            "imputed": df_imputed[var].value_counts(normalize=True).to_dict()
        }
        
        # 2. Conditional distribution (if predictor exists)
        if predictor and predictor in df_original.columns:
            # For each category of the predictor
            pred_cats = df_original[predictor].unique()
            
            conditional_results = {}
            for cat in pred_cats:
                # Original conditional distribution
                orig_cond = df_original[df_original[predictor] == cat][var].value_counts(normalize=True).to_dict()
                
                # Observed conditional distribution (among non-missing)
                obs_mask = (df_with_missing[predictor] == cat) & df_with_missing[var].notna()
                obs_cond = df_with_missing[obs_mask][var].value_counts(normalize=True).to_dict()
                
                # Imputed conditional distribution
                imp_cond = df_imputed[df_imputed[predictor] == cat][var].value_counts(normalize=True).to_dict()
                
                conditional_results[cat] = {
                    "original": orig_cond,
                    "observed": obs_cond,
                    "imputed": imp_cond
                }
            
            results[f"{var}_conditional_{predictor}"] = conditional_results
    
    return results

def preprocess_dataframe(df):
    df = df.replace(-2147483648, np.nan)
    colA1 = df['A1'].tolist()
    colA2 = df['A2'].tolist()
    df[strCensoringA1] = df['A1'].isna()
    df[strCensoringA2] = df['A2'].isna()
    return df, colA1, colA2

def postprocess_dataframe(df, colA1, colA2, method, target_vars):
    if method == 'CCA':
        return df
    
    if not any(var in ['A1', 'A2'] for var in target_vars):
        return df
    
    if 'A1' in df.columns and 'A2' in df.columns:
        n_rows = len(df)
        for idx in range(min(len(colA1), len(colA2), n_rows)):
            val_a1 = colA1[idx]
            val_a2 = colA2[idx]
            if isinstance(val_a1, float) and math.isnan(val_a1):
                df.at[idx, 'A1'] = np.nan
            if isinstance(val_a2, float) and math.isnan(val_a2):
                df.at[idx, 'A2'] = np.nan
    return df

def simulate_missingness(df, target_vars, predictors, missing_type, missing_percent):
    seed = 444
    np.random.seed(seed)
    df_missing = df.copy()
    
    # reset index to ensure we have consecutive integer indices
    df_missing = df_missing.reset_index(drop=True)
    
    if missing_type == 'MCAR':
        for target_var in target_vars:
            df_missing = simulate_MCAR(df_missing, target_var=target_var, missing_fraction=missing_percent, seed=seed)
    elif missing_type == 'MAR' or missing_type == 'MARY':
        if len(target_vars) > len(predictors):
            predictors = predictors + [predictors[0]] * (len(target_vars) - len(predictors))
        for i, target_var in enumerate(target_vars):
            predictor = predictors[i]
            df_missing = simulate_MAR(
                df_missing,
                target_var=target_var,
                predictor=predictor,
                missing_percent=missing_percent,
                seed=seed
            )
    elif missing_type == 'MNAR':
        for i, target_var in enumerate(target_vars):
            df_missing = simulate_MNAR(
                df_missing,
                target_var=target_var,
                missing_percent=missing_percent,
                seed=seed
            )
        
    return df_missing

def run_method(df, method, target_vars):
    if method == 'CCA':
        #print("Running Complete Case Analysis")
        df = apply_method_complete_case(df, missingVariables=target_vars)
    elif method == 'SMI':
        #print("Running Single Imputation")
        try:
            df = apply_method_single_imputation(df, missingVariables=target_vars)
        except Exception as e:
            print(f"Error occurred while applying single imputation: {e}")
    elif method == 'HD':
        #print("Running Hot Deck Imputation")
        try:
            df = apply_method_hot_deck_imputation(df, missingVariables=target_vars)
        except Exception as e:
            print(f"Error occurred while applying hot deck imputation: {e}")
    elif method == 'MI':
        #print("Running Multiple Imputation")
        return df
    else:
        raise ValueError(f"Method {method} is not implemented.")
    return df