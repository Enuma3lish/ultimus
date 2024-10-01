import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm

# Load the data
data = pd.read_csv('/home/melowu/Work/ultimus/log/combined_results.csv')  # Adjust this to the path of your CSV file
metrics = [
    "Dynamic_L2_Norm_vs_FCFS", "Dynamic_L2_Norm_vs_SRPT"
]

# Ensure directory for plots exists or is created
plots_dir = "/home/melowu/Work/ultimus/log/img"
os.makedirs(plots_dir, exist_ok=True)

# Color palette for different bp_parameters (restrict to 4 colors)
colors = cm.get_cmap('viridis', 5)

# Define four different marker styles (symbols)
markers = ['o', 's', '^', 'D','>']  # You can modify these symbols as you prefer
linestyle = '-'  # Only one kind of line

for metric in metrics:
    plt.figure(figsize=(12, 8))
    
    color_index = 0
    # Loop over unique bp_parameter (limit to 4 iterations)
    for bp_param in data['bp_parameter'].unique()[:5]:  # Ensure we only get the first 4 unique parameters
        specific_data = data[data['bp_parameter'] == bp_param]

        # Debugging: Print specific data
        print(f"bp_parameter: {bp_param}")
        print(specific_data.head())

        if not specific_data.empty:
            # Check for NaN or infinite values in the metric column
            if specific_data[metric].isnull().values.any():
                print(f"Warning: NaN values found in {metric} for bp_param {bp_param}")
            if np.isinf(specific_data[metric].values).any():
                print(f"Warning: Infinite values found in {metric} for bp_param {bp_param}")

            # Plotting the data
            plt.plot(
                specific_data['arrival_rate'],  # X-axis: arrival_rate (mean interarrival time)
                specific_data[metric],          # Y-axis: metric value
                marker=markers[color_index % len(markers)],  # Different marker for each bp_param
                linestyle=linestyle,            # Same line style for all bp_param
                label=f'BP={bp_param}',         # Label for each bp_param
                color=colors(color_index)       # Use a different color for each line
            )
            color_index += 1

    plt.title(f'{metric}')
    plt.xlabel('Mean Interarrival Time (Arrival Rate)')  # X-axis label for mean interarrival time
    plt.ylabel(metric)                                   # Y-axis label for metric comparison
    plt.legend(title='BP Parameter', loc='best')
    plt.grid(True)

    # Set a narrower y-axis range for zooming into values close to 1
    plt.ylim(0, 2)  # Setting y-limits between 0 and 2 for a clearer view of values near 0 and 1
    
    # Set y-ticks with smaller intervals between 0 and 2
    plt.yticks(np.arange(0, 2.1, 0.1))  # Smaller intervals (0.1) for better clarity
    
    # Set custom x-ticks for mean interarrival time (arrival_rate)
    plt.xticks(ticks=np.arange(20, 41, 2))  # Assuming arrival rates are between 20 and 40 with a step of 2
    
    plt.tight_layout()  # Adjust the layout to make room for the y-axis label
    
    # Save the plot
    filename = f'{plots_dir}/{metric.replace("/", "_")}_comparison_limited.pdf'
    plt.savefig(filename)
    plt.close()