import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def visualize_distribution_table(data_dict, title, output_file=None):
    df = pd.DataFrame(list(data_dict.items()), columns=['Category', 'Value'])
    
    fig, ax = plt.subplots(figsize=(8.5, len(df) * 0.4 + 1))
    ax.axis('off')
    ax.axis('tight')
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        loc='center',
        cellLoc='center'
    )
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.3, 1.8)
    
    col_widths = {'Category': 0.6, 'Value': 0.4}
    
    for (i, j), cell in table.get_celld().items():
        if i == 0:
            column_name = df.columns[j]
            cell.set_width(col_widths[column_name])
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('black')
        else:
            column_name = df.columns[j]
            cell.set_width(col_widths[column_name])
            
            if j == 0:
                cell.set_text_props(ha='left', x=0.05, weight='bold')
                cell.set_facecolor('#E6E6E6')
            else:
                cell.set_text_props(weight='bold')
    
    # add alternating row shading
    for i in range(1, len(df) + 1, 2):
        if i < len(df) + 1:
            value_cell = table[(i, 1)]
            value_cell.set_facecolor('#F5F5F5')
    
    plt.suptitle(title, fontsize=16, fontweight='bold', y=0.95)
    plt.tight_layout()
    plt.subplots_adjust(top=0.85, bottom=0.1)
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.show()
    
    return fig

def show_univariate_distributions(df):
    print("UNIVARIATE DISTRIBUTIONS")
    print("="*50)
    
    print("\n1. TREATMENT AND OUTCOME DISTRIBUTIONS")
    print("-" * 40)
    
    # combine treatment and outcome columns
    treatment_cols = ['A1', 'A2', 'A3']
    outcome_cols = ['Y1', 'Y2', 'Y3', 'Y4']
    all_vars = treatment_cols + outcome_cols
    available_vars = [col for col in all_vars if col in df.columns]
    
    if available_vars:
        wide_data = {'Value': ['0', '1']}
        
        for col in available_vars:
            var_counts = df[col].value_counts().sort_index()
            var_props = df[col].value_counts(normalize=True).sort_index()
            
            col_data = []
            for value in [0, 1]:
                if value in var_counts.index:
                    count = var_counts[value]
                    prop = var_props[value]
                    col_data.append(f"{count} ({prop:.1%})")
                else:
                    col_data.append("0 (0.0%)")
            
            wide_data[col] = col_data
        
        wide_df = pd.DataFrame(wide_data)

        fig, ax = plt.subplots(figsize=(8.5, 3))
        ax.axis('off')
        ax.axis('tight')
        table = ax.table(
            cellText=wide_df.values,
            colLabels=wide_df.columns,
            loc='center',
            cellLoc='center'
        )
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.2, 3.0)
        
        num_cols = len(wide_df.columns)
        col_width = 1.0 / num_cols
        for (i, j), cell in table.get_celld().items():
            cell.set_width(col_width)
            
            if i == 0:
                cell.set_text_props(weight='bold', color='white')
                cell.set_facecolor('black')
            else:
                if j == 0:
                    cell.set_text_props(ha='center', weight='bold')
                    cell.set_facecolor('#E6E6E6')
                else:
                    cell.set_text_props(ha='center', weight='bold')
        
        for i in range(1, len(wide_df) + 1):
            if i % 2 == 0:
                for j in range(1, len(wide_df.columns)):
                    cell = table[(i, j)]
                    cell.set_facecolor('#F5F5F5')
        
        plt.suptitle("Marginal Distributions of Treatments (A) and Outcomes (Y)", fontsize=16, fontweight='bold', y=0.9)
        plt.tight_layout()
        plt.subplots_adjust(top=0.8, bottom=0.1)
        plt.savefig("zfig_distribution_treatments_outcomes.png", dpi=300, bbox_inches='tight')
        plt.show()
    
    print("\n3. CONFOUNDER DISTRIBUTIONS")
    print("-" * 35)
    
    confounder_cols = ['NumComorbidities']
    for col in confounder_cols:
        if col in df.columns:
            conf_counts = df[col].value_counts().sort_index()
            conf_props = df[col].value_counts(normalize=True).sort_index()
            
            dist_data = {}
            for value in conf_counts.index:
                count = conf_counts[value]
                prop = conf_props[value]
                dist_data[f"{col} = {value}"] = f"{count} ({prop:.1%})"
            
            dist_data["Total"] = f"{len(df)}"
            
            visualize_distribution_table(
                dist_data,
                f"Marginal Distribution of {col} (Z)",
                f"zfig_distribution_{col.lower()}.png"
            )

def show_comorbidity_relationships(df):
    print("\n" + "="*60)
    print("RELATIONSHIPS: NUMCOMORBIDITIES vs TREATMENTS/OUTCOMES")
    print("="*60)
    
    if 'NumComorbidities' not in df.columns:
        print("NumComorbidities column not found!")
        return
    
    treatment_cols = ['A1', 'A2', 'A3']
    available_treatments = [col for col in treatment_cols if col in df.columns]
    
    if available_treatments:
        print("\n1. NUMCOMORBIDITIES vs TREATMENTS")
        print("-" * 40)
        
        crosstab_data = {'NumComorbidities': []}
        comorbidity_levels = sorted(df['NumComorbidities'].unique())

        for level in comorbidity_levels:
            crosstab_data['NumComorbidities'].append(f"Level {level}")
        
        for col in available_treatments:
            crosstab_data[f"{col} (%)"] = []
            
            for level in comorbidity_levels:
                subset = df[df['NumComorbidities'] == level]
                if len(subset) > 0:
                    treatment_1_prop = subset[col].mean()
                    crosstab_data[f"{col} (%)"].append(f"{treatment_1_prop:.1%}")
                else:
                    crosstab_data[f"{col} (%)"].append("N/A")
        
        crosstab_df = pd.DataFrame(crosstab_data)
        
        fig, ax = plt.subplots(figsize=(8.5, len(crosstab_df) * 0.6))
        ax.axis('off')
        ax.axis('tight')
        table = ax.table(
            cellText=crosstab_df.values,
            colLabels=crosstab_df.columns,
            loc='center',
            cellLoc='center'
        )
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.2, 1.8)
        
        num_cols = len(crosstab_df.columns)
        col_width = 1.0 / num_cols
        for (i, j), cell in table.get_celld().items():
            cell.set_width(col_width)
            
            if i == 0:
                cell.set_text_props(weight='bold', color='white')
                cell.set_facecolor('black')
            else:
                if j == 0:
                    cell.set_text_props(ha='center', weight='bold')
                    cell.set_facecolor('#E6E6E6')
                else:
                    cell.set_text_props(ha='center', weight='bold')
        for i in range(1, len(crosstab_df) + 1):
            if i % 2 == 0:
                for j in range(1, len(crosstab_df.columns)):
                    cell = table[(i, j)]
                    cell.set_facecolor('#F5F5F5')
        
        plt.suptitle("Treatment Rates by Number of Comorbidities", fontsize=14, fontweight='bold', y=0.9)
        plt.tight_layout()
        plt.subplots_adjust(top=0.8, bottom=0.1)
        plt.savefig("zfig_comorbidities_treatments.png", dpi=300, bbox_inches='tight')
        plt.show()
    
    outcome_cols = ['Y1', 'Y2', 'Y3', 'Y4']
    available_outcomes = [col for col in outcome_cols if col in df.columns]
    
    if available_outcomes:
        print("\n2. NUMCOMORBIDITIES vs OUTCOMES")
        print("-" * 35)
        
        outcome_crosstab_data = {'NumComorbidities': []}
        for level in comorbidity_levels:
            outcome_crosstab_data['NumComorbidities'].append(f"Level {level}")
    
        for col in available_outcomes:
            outcome_crosstab_data[f"{col} (%)"] = []
            
            for level in comorbidity_levels:
                subset = df[df['NumComorbidities'] == level]
                if len(subset) > 0:
                    event_prop = subset[col].mean()
                    outcome_crosstab_data[f"{col} (%)"].append(f"{event_prop:.1%}")
                else:
                    outcome_crosstab_data[f"{col} (%)"].append("N/A")
        
        outcome_crosstab_df = pd.DataFrame(outcome_crosstab_data)
        
        fig, ax = plt.subplots(figsize=(8.5, len(outcome_crosstab_df) * 0.6))
        ax.axis('off')
        ax.axis('tight')
        
        table = ax.table(
            cellText=outcome_crosstab_df.values,
            colLabels=outcome_crosstab_df.columns,
            loc='center',
            cellLoc='center'
        )
        
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.2, 1.8)
        num_cols = len(outcome_crosstab_df.columns)
        col_width = 1.0 / num_cols
        
        for (i, j), cell in table.get_celld().items():
            cell.set_width(col_width)
            
            if i == 0:
                cell.set_text_props(weight='bold', color='white')
                cell.set_facecolor('black')
            else:
                if j == 0:
                    cell.set_text_props(ha='center', weight='bold')
                    cell.set_facecolor('#E6E6E6')
                else:
                    cell.set_text_props(ha='center', weight='bold')
        
        for i in range(1, len(outcome_crosstab_df) + 1):
            if i % 2 == 0:
                for j in range(1, len(outcome_crosstab_df.columns)):
                    cell = table[(i, j)]
                    cell.set_facecolor('#F5F5F5')
        
        plt.suptitle("Survival Outcomes (Y) by Number of Comorbidities (Z)", fontsize=14, fontweight='bold', y=0.9)
        plt.tight_layout()
        plt.subplots_adjust(top=0.8, bottom=0.1)
        plt.savefig("zfig_comorbidities_outcomes.png", dpi=300, bbox_inches='tight')
        plt.show()

df = pd.read_csv("C:/Users/the_o/Desktop/Dissertation/MissingnessSimulation/MissingnessSim/python_missingness_extension/describe_data.csv")
print("Data Overview:")
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")
print("\nFirst few rows:")
print(df.head())

show_univariate_distributions(df)
show_comorbidity_relationships(df)

