import pandas as pd
import pingouin as pg
from pyparsing import col
from postprocess_results import post_process_simulation_results
from analysis_marginal_ANOVA import convert_df_for_analysis
import matplotlib.pyplot as plt
import numpy as np

def run_parameter_ANOVA(df, dv, numInteractions=0, onlySignificant= False, columns=[]):
    print(f"\n{'='*60}")
    print(f"REPEATED MEASURES ANOVA ANALYSIS FOR: {dv.upper()}")
    print(f"{'='*60}")

    between = columns
    anova_result = pg.anova(
        data=df,
        dv=dv,
        between=between,
        detailed=True,
        effsize='np2'
    ).round(5)
    
    print("\nANOVA Results:")
    filtered_result = anova_result[anova_result['Source'].str.count(' \* ') <= numInteractions]
    filtered_result = filtered_result.sort_values(by=['p-unc', 'np2'], ascending=[True, False])
    filtered_result = filtered_result.drop(columns=['MS', 'SS'], errors='ignore')
    filtered_result['DF'] = filtered_result['DF'].round(0)

    if onlySignificant:
        filtered_result = filtered_result[filtered_result['p-unc'] < 0.001]

    print(filtered_result.to_csv(index=False))
    return anova_result



def create_combined_tukey_table(df, param_tested):
    measures = ['bias_avg', 'coverage_avg', 'empirical_se_avg']
    measure_names = ['Bias', 'Coverage', 'Empirical SE']
    
    combined_results = []
    
    for i, measure in enumerate(measures):
        posthoc = pg.pairwise_tukey(data=df, dv=measure, between=param_tested)
        result_df = posthoc[['A', 'B', 'mean(A)', 'mean(B)', 'diff', 'p-tukey']].round(4).copy()
        
        result_df['Measure'] = measure_names[i]
        result_df['Significance'] = ''
        result_df.loc[result_df['p-tukey'] < 0.05, 'Significance'] = '*'
        result_df.loc[result_df['p-tukey'] < 0.01, 'Significance'] = '**'
        result_df.loc[result_df['p-tukey'] < 0.001, 'Significance'] = '***'
        
        combined_results.append(result_df)
    
    combined_df = pd.concat(combined_results, ignore_index=True)
    
    combined_df.columns = ['Level A', 'Level B', f'Mean {param_tested} A', 
                          f'Mean {param_tested} B', 'Difference', 'p-value', 
                          'Measure', 'Significance']
    combined_df = combined_df[['Measure', 'Level A', 'Level B', f'Mean {param_tested} A', 
                              f'Mean {param_tested} B', 'Difference', 'p-value', 'Significance']]
    combined_df = combined_df.sort_values(['Measure', 'p-value'])
    
    return combined_df

def visualise_tukey_table(combined_df, param_tested):
    fig, ax = plt.subplots(figsize=(12, len(combined_df) * 0.4 + 0.4))
    ax.axis('off')
    ax.axis('tight')
    
    display_df = combined_df.copy()
    display_df['p-value'] = display_df['p-value'].apply(lambda x: f"{x:.4f} {display_df.loc[display_df['p-value']==x, 'Significance'].values[0]}")
    display_df = display_df.drop(columns=['Significance'])
    
    for col in ['Mean '+param_tested+' A', 'Mean '+param_tested+' B', 'Difference']:
        display_df[col] = display_df[col].apply(lambda x: f"{x:.4f}")
    
    table = ax.table(
        cellText=display_df.values,
        colLabels=display_df.columns,
        loc='center',
        cellLoc='center'
    )
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    for j, col in enumerate(display_df.columns):
        cell = table[(0, j)]
        cell.set_text_props(weight='bold', color='white')
        cell.set_facecolor('black')

    current_measure = None
    for i, measure in enumerate(display_df['Measure']):
        if measure != current_measure:
            current_measure = measure
            cell = table[(i+1, 0)]
            cell.set_text_props(weight='bold')
            cell.set_facecolor('#E6E6E6')
            for j in range(1, len(display_df.columns)):
                cell = table[(i+1, j)]
                cell.set_facecolor('#F5F5F5')
    
    for i in range(1, len(display_df) + 1, 2):
        for j in range(1, len(display_df.columns)):
            cell = table[(i, j)]
            current_color = cell.get_facecolor()
            if np.all(current_color == [1, 1, 1, 1]):
                cell.set_facecolor('#F9F9F9')
    
    plt.title(f"Tukey's HSD Post-hoc Tests for {param_tested.title()}", fontsize=14, fontweight='bold', pad=20)
    footnote = "Note: * p < 0.05, ** p < 0.01, *** p < 0.001"
    plt.figtext(0.5, 0.01, footnote, ha='center', fontsize=10, style='italic')
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.05)
    plt.savefig(f'zfig_tukey_hsd_{param_tested}.png', dpi=300, bbox_inches='tight')
    plt.show()
    plt.close()
    
    return fig






input_csv_path = 'C:/Users/the_o/Desktop/Dissertation/MissingnessSimulation/MissingnessSim/python_missingness_extension/all_scenario_results.csv'
df = post_process_simulation_results(input_csv_path, conditioningDict={})
print(f"Data shape before filtering: {df.shape}")
df = df[(df['method'] != 'full_')].copy()
print(f"Data shape after filtering: {df.shape}")
df = convert_df_for_analysis(df)

#dfSplit = convert_by_parameter(df)
for param_tested in ['sample_size', 'rho', 'missing_rate', 'mechanism', 'method']:
    results = []
    results.append(run_parameter_ANOVA(df, 'bias_avg', numInteractions=1, onlySignificant=False, columns=[param_tested]))
    results.append(run_parameter_ANOVA(df, 'coverage_avg', numInteractions=1, onlySignificant=False, columns=[param_tested]))
    results.append(run_parameter_ANOVA(df, 'empirical_se_avg', numInteractions=1, onlySignificant=False, columns=[param_tested]))

    combined_results = create_combined_tukey_table(df, param_tested)
    visualise_tukey_table(combined_results, param_tested)