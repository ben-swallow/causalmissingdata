import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pingouin as pg
from postprocess_results import post_process_simulation_results
from analysis_marginal_ANOVA import convert_df_for_analysis

def analyze_bias_relative_to_se(df):
    df['bias_to_emp_se'] = df['bias_avg'].abs() / df['empirical_se_avg']
    
    df_filtered = df[df['bias_to_emp_se'].between(0, 5)].copy()
    
    print("=== ONE-WAY ANOVA: METHOD EFFECT ON |BIAS|/SE ===")
    anova_method = pg.anova(data=df_filtered, dv='bias_to_emp_se', between='method', detailed=True)
    print(anova_method)
    
    if anova_method.loc[0, 'p-unc'] < 0.05:
        print("\n=== POST-HOC TESTS: PAIRWISE COMPARISONS BETWEEN METHODS ===")
        posthoc = pg.pairwise_tukey(data=df_filtered, dv='bias_to_emp_se', between='method').round(4)
        print(posthoc.to_csv(index=False))

    parameters = ['mechanism', 'sample_size', 'missing_rate', 'rho']
    
    for param in parameters:
        if param in df.columns and df_filtered[param].nunique() > 1:
            print(f"\n=== TWO-WAY ANOVA: METHOD × {param.upper()} EFFECT ON |BIAS|/SE ===")
            anova_interaction = pg.anova(data=df_filtered, 
                                         dv='bias_to_emp_se', 
                                         between=['method', param], 
                                         detailed=True)
            print(anova_interaction)
    
    plt.figure(figsize=(12, 6))
    sns.boxplot(data=df_filtered, x='method', y='bias_to_emp_se')
    plt.axhline(y=1.96, color='r', linestyle='--', label='95% Significance')
    plt.title('|Bias| / Empirical SE by Method')
    plt.ylabel('|Bias| / Empirical SE')
    plt.xticks(rotation=45)
    plt.legend()
    
    # add mean values above each box
    means = df_filtered.groupby('method')['bias_to_emp_se'].mean()
    for i, method in enumerate(df_filtered['method'].unique()):
        if method in means:
            plt.text(i, means[method] + 0.1, f'{means[method]:.2f}', 
                     ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('zfig_bias_to_se_by_method.png', dpi=300)
    plt.show()
    
    return df

if __name__ == "__main__":
    input_csv_path = 'C:/Users/the_o/Desktop/Dissertation/MissingnessSimulation/MissingnessSim/python_missingness_extension/all_scenario_results.csv'
    df = post_process_simulation_results(input_csv_path, conditioningDict={})
    df = convert_df_for_analysis(df)
    result_df = analyze_bias_relative_to_se(df)
