import pandas as pd
import numpy as np
from analysis_marginal_ANOVA import convert_df_for_analysis, convert_by_parameter
from postprocess_results import post_process_simulation_results

import matplotlib.pyplot as plt
import seaborn as sns

def reorder_mechanism_levels(subsets, desired_order=None):
    if desired_order is None:
        desired_order = ["MCAR", "MAR(A)", "MAR(Y)", "MNAR"]
    ordered_subsets = []
    
    for mechanism in desired_order:
        for level_name, subset_df in subsets:
            if level_name == mechanism:
                ordered_subsets.append((level_name, subset_df))
                break
    
    for level_name, subset_df in subsets:
        if level_name not in desired_order:
            ordered_subsets.append((level_name, subset_df))
    
    return ordered_subsets

def plot_results(split_dfs):    
    # performance measures and conversions
    measures = ['bias', 'coverage', 'empirical_se']
    measure_titles = ['Bias', 'Coverage', 'Empirical SE']
    
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
            "MCAR": "",
            "MAR(A)": "",
            "MAR(Y)": "",
            "MNAR": ""
        },
        'missing_rate': {
            'LOW': "20%",
            'HIGH': "50%"
        }
    }
    
    for param_name, subsets in split_dfs.items():
        n_levels = len(subsets)
        n_measures = len(measures)
        
        if param_name == 'mechanism':
            fig, axes = plt.subplots(n_levels, n_measures, figsize=(10, 5 * n_levels + 40))
            desired_order = ["MCAR", "MAR(A)", "MAR(Y)", "MNAR"]
            subsets = reorder_mechanism_levels(subsets, desired_order)
        else:
            fig, axes = plt.subplots(n_levels, n_measures, figsize=(10, 5 * n_levels))

        plt.subplots_adjust(left=0.15)
        if n_levels == 1:
            axes = axes.reshape(1, -1)
        elif n_measures == 1:
            axes = axes.reshape(-1, 1)
        
        display_name = param_name.replace('_', ' ').title()
        if display_name == "Rho":
            display_name = "Confounding Strength"
        fig.suptitle(f'Method by {display_name}', 
            fontsize=16, fontweight='bold')
        
        y_limits = {}
        for measure in measures:
            column_name = f'{measure}_avg'
            
            if measure == 'bias':
                y_limits[measure] = (0, 20)
            elif measure == 'empirical_se':
                y_limits[measure] = (0, 25)
            else:
                all_values = [val for _, subset_df in subsets 
                            if column_name in subset_df.columns
                            for val in subset_df[column_name].dropna()]
                if all_values:
                    y_min, y_max = min(all_values), max(all_values)
                    padding = (y_max - y_min) * 0.05
                    y_limits[measure] = (y_min - padding, y_max + padding)
                else:
                    y_limits[measure] = (0, 1)
        
        for level_idx, (level_name, subset_df) in enumerate(subsets):
            display_level = level_name
            
            if param_name in param_mappings and level_name in param_mappings[param_name]:
                mapped_value = param_mappings[param_name][level_name]
                if(mapped_value == ""):
                    display_level = f"{level_name}"
                else:
                    display_level = f"{level_name} ({mapped_value})"
            else:
                level_value = float(level_name)
                display_level = f"{level_value:.2f}" if level_value != int(level_value) else f"{int(level_value)}"

            
            row_label = f"{display_level}"
            y_pos = 1.0 - ((level_idx + 0.5) / n_levels)
            fig.text(0.02, y_pos, row_label, 
                va='center', ha='left', fontsize=12, 
                fontweight='bold',
                rotation=90,
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=3.0))
                
            for measure_idx, (measure, measure_title) in enumerate(zip(measures, measure_titles)):
                column_name = f'{measure}_avg'
                if column_name in subset_df.columns:

                    if measure == 'bias':
                        plot_df = subset_df.copy()
                        sns.boxplot(data=plot_df, x='method', y=column_name, 
                                ax=axes[level_idx, measure_idx])
                    else:
                        sns.boxplot(data=subset_df, x='method', y=column_name, 
                                ax=axes[level_idx, measure_idx])

                    xticklabels = [label.get_text().replace("_", "") for label in axes[level_idx, measure_idx].get_xticklabels()]
                    axes[level_idx, measure_idx].set_xticklabels(xticklabels)

                    axes[level_idx, measure_idx].set_title(
                        f'{measure_title}', fontsize=12
                    )
                    axes[level_idx, measure_idx].set_xlabel('')
                    axes[level_idx, measure_idx].set_ylabel(measure_title)
                    axes[level_idx, measure_idx].tick_params(axis='x', rotation=45)
                    axes[level_idx, measure_idx].set_ylim(y_limits[measure])
                    if measure == 'bias':
                        axes[level_idx, measure_idx].axhline(y=0, color='red', linestyle='--', alpha=0.7)
                    elif measure == 'coverage':
                        axes[level_idx, measure_idx].axhline(y=0.95, color='red', linestyle='--', alpha=0.7)

        
        plt.subplots_adjust(
            top=0.93,
            bottom=0.05,
            left=0.1,
            right=0.95,
            hspace=0.4,
            wspace=0.3
        )
        plt.show()
        fig.savefig(f'zfig_marginal_plot_{param_name}.png', dpi=300)

def plot_marginal(df):
    # performance measures and conversions
    measures = ['bias', 'coverage', 'empirical_se']
    measure_titles = ['Bias', 'Coverage', 'Empirical SE']
    n_measures = len(measures)
    
    fig, axes = plt.subplots(1, n_measures, figsize=(10, 6))
    
    # calculate y-axis limits for each measure
    y_limits = {}
    for measure in measures:
        column_name = f'{measure}_avg'
        
        if measure == 'bias':
            y_limits[measure] = (0, 20)
        elif measure == 'empirical_se':
            filtered_values = df[df[f'{measure}_avg'] <= 25][f'{measure}_avg'].dropna().values
            if len(filtered_values) > 0:
                y_min, y_max = np.min(filtered_values), np.max(filtered_values)
                y_limits[measure] = (0, 25)
            else:
                y_limits[measure] = (0, 25)
        else:
            all_values = df[column_name].dropna().values
            if len(all_values) > 0:
                y_min, y_max = np.min(all_values), np.max(all_values)
                padding = (y_max - y_min) * 0.1
                y_limits[measure] = (y_min - padding, y_max + padding)
            else:
                y_limits[measure] = (0, 1)

    # plotting
    for measure_idx, (measure, measure_title) in enumerate(zip(measures, measure_titles)):
        column_name = f'{measure}_avg'
        
        if column_name in df.columns:
            sns.boxplot(data=df, x='method', y=column_name, ax=axes[measure_idx])
            
            xticklabels = [label.get_text().replace("_", "") for label in axes[measure_idx].get_xticklabels()]
            axes[measure_idx].set_xticklabels(xticklabels)
            axes[measure_idx].set_title(f'{measure_title}', fontsize=14)
            axes[measure_idx].set_xlabel('Method', fontsize=12)
            axes[measure_idx].set_ylabel(measure_title, fontsize=12)
            axes[measure_idx].tick_params(axis='x', rotation=45)
            
            if measure in y_limits:
                axes[measure_idx].set_ylim(y_limits[measure])
            
            if measure == 'bias':
                axes[measure_idx].axhline(y=0, color='red', linestyle='--', alpha=0.7)
            elif measure == 'coverage':
                axes[measure_idx].axhline(y=0.95, color='red', linestyle='--', alpha=0.7)
    
    fig.suptitle('Performance Measures Across All Methods (A1)', fontsize=16, fontweight='bold')
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig('zfig_marginal_plot_overall.png', dpi=300)
    plt.show()
    
    return fig


if __name__ == "__main__":
    input_csv_path = 'C:/Users/the_o/Desktop/Dissertation/MissingnessSimulation/MissingnessSim/python_missingness_extension/all_scenario_results.csv'  # Path to the input CSV file
    df = post_process_simulation_results(input_csv_path, conditioningDict={})

    df = convert_df_for_analysis(df)

    print("Column names in df:")
    print(df.columns.tolist())

    plot_marginal(df)
    split_dfs = convert_by_parameter(df)
    plot_results(split_dfs)
