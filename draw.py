import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Define plotting support structures
comparison_columns = [
    "Rdynamic_sqrt_6/RR_ratio", "Rdynamic_sqrt_6/SRPT_ratio", "Rdynamic_sqrt_6/SETF_ratio", "Rdynamic_sqrt_6/FCFS_ratio",
    "Rdynamic_sqrt_6/RMLF_ratio", "Rdynamic_sqrt_6/Dynamic_ratio", "Rdynamic_sqrt_8/RR_ratio", "Rdynamic_sqrt_8/SRPT_ratio",
    "Rdynamic_sqrt_8/SETF_ratio", "Rdynamic_sqrt_8/FCFS_ratio", "Rdynamic_sqrt_8/RMLF_ratio", "Rdynamic_sqrt_8/Dynamic_ratio",
    "Rdynamic_sqrt_10/RR_ratio", "Rdynamic_sqrt_10/SRPT_ratio", "Rdynamic_sqrt_10/SETF_ratio", "Rdynamic_sqrt_10/FCFS_ratio",
    "Rdynamic_sqrt_10/RMLF_ratio", "Rdynamic_sqrt_10/Dynamic_ratio", "Dynamic/SRPT_ratio",
    "Rdynamic_sqrt_6/Rdynamic_sqrt_8_ratio", "Rdynamic_sqrt_6/Rdynamic_sqrt_10_ratio", "Rdynamic_sqrt_8/Rdynamic_sqrt_10_ratio",
    "Rdynamic_sqrt_2/RR_ratio", "Rdynamic_sqrt_2/SRPT_ratio", "Rdynamic_sqrt_2/SETF_ratio", "Rdynamic_sqrt_2/FCFS_ratio",
    "Rdynamic_sqrt_2/RMLF_ratio", "Rdynamic_sqrt_2/Dynamic_ratio", "Rdynamic_sqrt_2/Rdynamic_sqrt_6_ratio",
    "Rdynamic_sqrt_2/Rdynamic_sqrt_8_ratio", "Rdynamic_sqrt_2/Rdynamic_sqrt_10_ratio", "RMLF/FCFS_ratio"
]

frequencies = ["1", "10", "100", "500", "1000", "10000"]
categories = ["", "softrandom"]

markers = [
    {'marker': 'o', 'size': 8}, {'marker': '^', 'size': 10}, {'marker': 's', 'size': 8},
    {'marker': 'v', 'size': 10}, {'marker': 'D', 'size': 8}, {'marker': '*', 'size': 10},
    {'marker': 'p', 'size': 8}, {'marker': 'h', 'size': 10}
]

line_styles = {
    'RR': '-', 'SRPT': '--', 'SETF': '-.', 'FCFS': ':', 'RMLF': '-', 'Dynamic': '--',
    'Rdynamic_sqrt_2': '-', 'Rdynamic_sqrt_6': '--', 'Rdynamic_sqrt_8': '-.', 'Rdynamic_sqrt_10': ':'
}

algorithm_colors = {
    'RR': '#FF0000', 'SRPT': '#0000FF', 'SETF': '#00CC00', 'FCFS': '#9900CC', 'RMLF': '#FF6600', 'Dynamic': '#996633',
    'Rdynamic_sqrt_2': '#FF00FF', 'Rdynamic_sqrt_6': '#00CCCC', 'Rdynamic_sqrt_8': '#FFCC00', 'Rdynamic_sqrt_10': '#00FF00'
}

algorithm_display_names = {
    'Rdynamic_sqrt_2': 'RDY_2', 'Rdynamic_sqrt_6': 'RDY_6', 'Rdynamic_sqrt_8': 'RDY_8', 'Rdynamic_sqrt_10': 'RDY_10'
}

def get_rdy_display_name(name):
    if 'Rdynamic_sqrt_' in name:
        try:
            num = name.split('_')[-1]
            return f"RDY_{num}"
        except:
            pass
    return algorithm_display_names.get(name, name)

plots_dir = "log/img/"
os.makedirs(plots_dir, exist_ok=True)

# Placeholder dummy plotting functions (to be replaced by full logic if needed)
def create_individual_plots(data, output_dir, freq_value, category_name):
    print(f"[Simulate] Creating individual plots for {category_name} freq={freq_value}")

def create_rdynamic_comparison_plots(data, output_dir, freq_value, category_name):
    print(f"[Simulate] Creating RDY comparisons for {category_name} freq={freq_value}")

def create_algorithm_variant_plots(data, output_dir, freq_value, category_name):
    print(f"[Simulate] Creating algorithm vs benchmark plots for {category_name} freq={freq_value}")

# === Main processing loop ===
for category in categories:
    for freq in frequencies:
        if category == "":
            file_path = f'freq_comp_result/all_result_freq_{freq}_cp30.csv'
        else:
            file_path = f'softrandom_comp_result/all_result_freq_{freq}_cp30.csv'

        output_dir = f"{plots_dir}/freq_{freq}/{category}"
        os.makedirs(output_dir, exist_ok=True)

        if os.path.exists(file_path):
            try:
                data = pd.read_csv(file_path)
                if data.empty:
                    print(f"Warning: Empty data file: {file_path}")
                    continue

                for col in data.columns:
                    if col != 'arrival_rate' and data[col].dtype == object:
                        data[col] = pd.to_numeric(data[col], errors='coerce')

                data = data.dropna(subset=['arrival_rate'])

                create_individual_plots(data, output_dir, freq, category)
                create_rdynamic_comparison_plots(data, output_dir, freq, category)
                create_algorithm_variant_plots(data, output_dir, freq, category)

                print(f"Created all plots for {category}freq_{freq}")
            except Exception as e:
                print(f"Error processing file {file_path}: {e}")
        else:
            print(f"File not found: {file_path}")
