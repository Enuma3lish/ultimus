import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm

# Load the data
data = pd.read_csv('/home/melowu/Work/ultimus/scheduler_results.csv')  # Adjust this to the path of your CSV file
metrics = [
   "Scheduler/SRPT",
   "Scheduler/FCFS",
   "Scheduler_L2_Norm/SRPT_L2_Norm",
   "Scheduler_L2_Norm/FCFS_L2_Norm"
]

# Ensure directory for plots exists or is created
plots_dir = "/home/melowu/Work/ultimus/img/total/result/"
os.makedirs(plots_dir, exist_ok=True)

# Color palette for different bp_parameters
colors = cm.get_cmap('viridis', len(data['bp_parameter'].unique()))

for metric in metrics:
    plt.figure(figsize=(12, 8))
    
    color_index = 0
    for bp_param in data['bp_parameter'].unique():
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
                specific_data['arrival_rate'], 
                specific_data[metric], 
                marker='o', 
                linestyle='-', 
                label=f'BP={bp_param}', 
                color=colors(color_index)
            )
            color_index += 1

    plt.title(f'{metric}')
    plt.xlabel('Mean Arrival Time')
    plt.ylabel(metric)
    plt.legend(title='BP Parameter', loc='best')
    plt.grid(True)

    # Set a narrower y-axis range for zooming into values close to 1
    plt.ylim(0, 2)  # Setting y-limits between 0 and 2 for a clearer view of values near 0 and 1
    
    # Set y-ticks with smaller intervals between 0 and 2
    plt.yticks(np.arange(0, 2.1, 0.1))  # Smaller intervals (0.1) for better clarity
    
    # Add custom vertical lines and x-ticks
    plt.axvline(x=25, color='black', linestyle='--')
    plt.axvline(x=35, color='black', linestyle='--')
    plt.xticks(ticks=np.arange(20, 41, 2))  # X-ticks as you had before
    
    plt.tight_layout()  # Adjust the layout to make room for the y-axis label
    
    # Save the plot
    filename = f'{plots_dir}/{metric.replace("/", "_")}_combined.png'
    plt.savefig(filename)
    plt.close()