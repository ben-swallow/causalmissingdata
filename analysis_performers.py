import pandas as pd
import numpy as np
from analysis_marginal_ANOVA import convert_df_for_analysis, convert_by_parameter
from postprocess_results import post_process_simulation_results
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

def best_worst_performer(df, method):
    method_data = df[df['method'] == method]
    
    print("Unique mechanisms:", df['scenario_id'].str.split('_').str[0].unique())
    measures = ['bias_avg', 'coverage_avg', 'empirical_se_avg']

    results = []
    
    for measure in measures:
       if measure == 'coverage_avg':
           best_idx = method_data[measure].idxmax()
       elif measure in ['empirical_se_avg', 'bias_avg']:
           best_idx = (method_data[measure].abs()).idxmin()
       best_row = method_data.loc[best_idx]
       
       # split scenario_id
       scenario_parts = best_row['scenario_id'].split('_')
       
       results.append({
           'measure': measure,
           'type': 'best',
           'value': best_row[measure],
           'mechanism': scenario_parts[0],
           'missingness_rate': float(scenario_parts[1]),
           'confounding_strength': float(scenario_parts[2]),
           'sample_size': int(scenario_parts[3])
       })
       
       # worst
       if measure == 'coverage_avg':
           worst_idx = method_data[measure].idxmin()
       elif measure in ['empirical_se_avg', 'bias_avg']:
           worst_idx = (method_data[measure].abs()).idxmax()
       worst_row = method_data.loc[worst_idx]
       
       scenario_parts = worst_row['scenario_id'].split('_')
       print(scenario_parts)
       
       results.append({
           'measure': measure,
           'type': 'worst',
           'value': worst_row[measure],
           'mechanism': scenario_parts[0],
           'missingness_rate': float(scenario_parts[1]),
           'confounding_strength': float(scenario_parts[2]),
           'sample_size': int(scenario_parts[3])
       })
    
    pdFrame = pd.DataFrame(results)
    pdFrame['value'] = pdFrame['value'].round(4)
    
    pdFrame['measure'] = pdFrame['measure'].str.replace('_avg', '', regex=False)
    pdFrame['measure'] = pdFrame['measure'].replace({
        'bias': 'Bias',
        'coverage': 'Coverage',
        'empirical_se': 'EmpSE'
    })
    
    pdFrame['sort_key'] = pdFrame.apply(
        lambda row: (
            0 if row['type'] == 'best' else 1,  # Type order: all best first, then all worst
            0 if row['measure'] == 'Bias' else (1 if row['measure'] == 'Coverage' else 2)  # Measure order within type
        ), 
        axis=1
    )
    pdFrame = pdFrame.sort_values(by='sort_key').reset_index(drop=True)
    
    pdFrame = pdFrame.drop(columns=['sort_key'])
    pdFrame = pdFrame.rename(columns={
        'measure': 'Measure',
        'type': 'Type',
        'value': 'Value',
        'mechanism': 'Mechanism',
        'missingness_rate': 'Rate',
        'confounding_strength': 'Confounding',
        'sample_size': 'Sample Size'
    })
    print("Method:", method)
    print(pdFrame.to_csv(index=False))
    
    fig, ax = plt.subplots(figsize=(10, 3))
    ax.axis('off')
    ax.axis('tight')
    
    table_data = pdFrame[['Measure', 'Type', 'Value', 'Mechanism', 'Rate', 'Confounding', 'Sample Size']]
    colors = []
    for i, row in table_data.iterrows():
        if row['Type'] == 'best':
            colors.append('#E6F2E6')  # light green for best
        else:
            colors.append('#F2E6E6')  # light red for worst
    
    table = ax.table(
        cellText=table_data.values,
        colLabels=table_data.columns,
        loc='center',
        cellLoc='center',
        cellColours=[[c] * len(table_data.columns) for c in colors]
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.2, 1.5)
    
    for j, col in enumerate(table_data.columns):
        cell = table[(0, j)]
        cell.set_text_props(weight='bold', color='white')
        cell.set_facecolor('black')
    
    method_name = method.replace('_', ' ').title()
    method_name = method_name.upper()

    plt.suptitle(f"Best and Worst Performance Scenarios for {method_name}", 
                fontsize=16, fontweight='bold', y=0.98)
    output_file = f"zfig_bestworst_performers_{method_name}.png"
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    plt.close()
    
    return pdFrame

if __name__ == "__main__":
    input_csv_path = 'C:/Users/the_o/Desktop/Dissertation/MissingnessSimulation/MissingnessSim/python_missingness_extension/all_scenario_results.csv'
    df = post_process_simulation_results(input_csv_path, conditioningDict={})

    df = convert_df_for_analysis(df)
    performers = []
    performers.append(best_worst_performer(df, method = 'CCA_'))
    performers.append(best_worst_performer(df, method = 'SMI_'))
    performers.append(best_worst_performer(df, method = 'HD_'))
    performers.append(best_worst_performer(df, method = 'MI_'))
    performers.append(best_worst_performer(df, method = 'full_'))
    
    combined_table = pd.concat(performers)
    combined_table['Method'] = ['CCA'] * 6 + ['SMI'] * 6 + ['HD'] * 6 + ['MI'] * 6 + ['Full'] * 6
    cols = ['Method'] + [col for col in combined_table.columns if col != 'Method']
    combined_table = combined_table[cols]
    
    # sort by best/worst, then method
    combined_table['sort_key'] = combined_table.apply(
        lambda row: (
            0 if row['Type'] == 'best' else 1,
            0 if row['Measure'] == 'Bias' else (1 if row['Measure'] == 'Coverage' else 2),
            ['CCA', 'SMI', 'HD', 'MI', 'Full'].index(row['Method']) if row['Method'] in ['CCA', 'SMI', 'HD', 'MI', 'Full'] else 999
        ), 
        axis=1
    )
    combined_table = combined_table.sort_values(by='sort_key').reset_index(drop=True)
    combined_table = combined_table.drop(columns=['sort_key'])
    fig, ax = plt.subplots(figsize=(12, 3))
    ax.axis('off')
    ax.axis('tight')
    
    method_colors = {
        'CCA': ('#FFF2CC', '#FFE699'),
        'SMI': ('#E6F2E6', '#D9E6D9'),
        'HD': ('#E6F0FF', '#CCE0FF'),
        'MI': ('#E6E6FF', '#CCCCFF'),
        'Full': ('#F2F2F2', '#E6E6E6')
    }
    
    cell_colors = []
    for i, row in combined_table.iterrows():
        if row['Type'] == 'best':
            cell_colors.append(method_colors[row['Method']][0])
        else:
            cell_colors.append(method_colors[row['Method']][1])
    
    table_data = combined_table[['Method', 'Measure', 'Type', 'Value', 'Mechanism', 'Rate', 'Confounding', 'Sample Size']]
    table = ax.table(
        cellText=table_data.values,
        colLabels=table_data.columns,
        loc='center',
        cellLoc='center',
        cellColours=[[c] * len(table_data.columns) for c in cell_colors]
    )
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.5)
    for j, col in enumerate(table_data.columns):
        cell = table[(0, j)]
        cell.set_text_props(weight='bold', color='white')
        cell.set_facecolor('black')

    plt.suptitle("Best and Worst Performance Scenarios for All Methods", 
                fontsize=16, fontweight='bold', y=0.98)
    legend_text = "Color Legend:\n"
    for method, (best_color, worst_color) in method_colors.items():
        legend_text += f"{method}: {best_color} (best), {worst_color} (worst)\n"
    
    plt.figtext(0.02, 0.02, legend_text, fontsize=8)
    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    plt.savefig("zfig_performance_all_methods.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    combined_table.to_csv("performance_summary.csv", index=False)

