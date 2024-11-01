import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load the data
check = [128]

# Define the bp_parameter
bp_parameter = [
    {"L": 4.073, "H": pow(2, 18)},
    {"L": 4.639, "H": pow(2, 15)},
    {"L": 5.649, "H": pow(2, 12)},
    {"L": 7.918, "H": pow(2, 9)},
    {"L": 16.772, "H": pow(2, 6)}
]

# Ensure directory for plots exists or is created
plots_dir = "/Users/melowu/Desktop/ultimus/log/img"
os.makedirs(plots_dir, exist_ok=True)

# Define markers and line styles
srpt_markers = [
    {'marker': '^', 'size': 10},  # Large upward triangle
    {'marker': '^', 'size': 6},   # Small upward triangle
    {'marker': 'o', 'size': 8},   # Circle
    {'marker': 'v', 'size': 6},   # Small downward triangle
    {'marker': 'v', 'size': 10}   # Large downward triangle
]
fcfs_markers = srpt_markers
srpt_color = 'blue'  # Fixed color for SRPT lines
fcfs_color = 'red'   # Fixed color for FCFS lines

# Function to get the index of a bp_parameter in the ordered list
def get_bp_index(bp_param):
    for i, param in enumerate(bp_parameter):
        if f"{param['L']:.3f}" in bp_param:
            return i
    return len(bp_parameter)  # Return max index if not found

# Loop over each check
for c in check:
    data = pd.read_csv(f'/Users/melowu/Desktop/ultimus/log/result{c}.csv')  # Adjust path as needed
    
    # Prepare the plot
    plt.figure(figsize=(12, 8))

    # Sort the unique bp_parameters based on the defined order
    unique_bp_params = sorted(data['bp_parameter'].unique(), key=get_bp_index)

    # First, plot SRPT comparisons
    for color_index, bp_param in enumerate(unique_bp_params):
        specific_data = data[data['bp_parameter'] == bp_param]
        if not specific_data.empty:
            marker_style = srpt_markers[color_index % len(srpt_markers)]['marker']
            marker_size = srpt_markers[color_index % len(srpt_markers)]['size']
            plt.plot(
                specific_data['arrival_rate'],
                specific_data['DYNAMIC_L2_Norm/SRPT_L2_Norm'],
                marker=marker_style,
                markersize=marker_size,
                linestyle='-',
                label=f'SRPT BP={bp_param}',
                color=srpt_color
            )

    # Now, plot FCFS comparisons
    for color_index, bp_param in enumerate(unique_bp_params):
        specific_data = data[data['bp_parameter'] == bp_param]
        if not specific_data.empty:
            marker_style = fcfs_markers[color_index % len(fcfs_markers)]['marker']
            marker_size = fcfs_markers[color_index % len(fcfs_markers)]['size']
            plt.plot(
                specific_data['arrival_rate'],
                specific_data['DYNAMIC_L2_Norm/FCFS_L2_Norm'],
                marker=marker_style,
                markersize=marker_size,
                linestyle='--',
                label=f'FCFS BP={bp_param}',
                color=fcfs_color
            )

    # Add titles, labels, and grid
    plt.title(f'Comparison of L2 Norm for DYNAMIC vs SRPT and FCFS (Check={c})')
    plt.xlabel('Mean Interarrival Time')
    plt.ylabel('L2 Norm Ratio')
    plt.legend(title='Comparison Type and BP Parameter', loc='best')
    plt.grid(True)

    # Set y-limits for zooming into values close to 1
    plt.ylim(0, 2)
    plt.yticks(np.arange(0, 2.1, 0.1))

    # Set custom x-ticks for mean interarrival time (arrival_rate)
    plt.xticks(ticks=np.arange(20, 41, 2))
    
    # Adjust layout and save the figure
    plt.tight_layout()
    filename = f'{plots_dir}/L2_Norm_Comparison_{c}.pdf'
    plt.savefig(filename)
    plt.close()