import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm

# Load the data
data = pd.read_csv('/home/melowu/Work/expri/DataSet/result_new.csv')  # Adjust this to the path of your CSV file
metrics = [
   "RMLFQ_aFF_L2_Norm/FCFS_L2_Norm",
   "RMLFQ_aFF_L2_Norm/RR_L2_Norm",
   "RMLFQ_aFF_L2_Norm/SETF_L2_Norm",
   "RMLFQ_aFF_L2_Norm/RMLFQ_L2_Norm",
   "RMLFQ_aFF_L2_Norm/MLFQ_L2_Norm",
   "RMLFQ_aFF_L2_Norm/SRPT_L2_Norm"
]

# Ensure directory for plots exists or is created
plots_dir = "img/total/result/"
os.makedirs(plots_dir, exist_ok=True)

# Color palette for different bp_parameters
colors = cm.get_cmap('viridis', len(data['bp_parameter'].unique()))

for metric in metrics:
    plt.figure(figsize=(12, 8))
    
    color_index = 0
    for bp_param in data['bp_parameter'].unique():
        specific_data = data[data['bp_parameter'] == bp_param]
        
        if not specific_data.empty:
            plt.plot(specific_data['arrival_rate'], specific_data[metric], marker='o', linestyle='-', label=f'BP={bp_param}', color=colors(color_index))
            color_index += 1

    plt.title(f'{metric}')
    plt.xlabel('Mean Arrival Time')
    plt.ylabel(metric)
    plt.legend(title='BP Parameter', loc='best')
    plt.grid(True)
    
    # Highlighting specific points
    plt.axhline(y=1, color='b', linestyle='--', label='y=1')   # Add a horizontal line at y=1
    plt.axhline(y=1.2, color='r', linestyle='--', label='y=1.2')  # Add a horizontal line at y=1.2
    plt.axhline(y=1.5, color='g', linestyle='--', label='y=1.5')  # Add a horizontal line at y=1.5
    
    # Annotating specific points
    for line in plt.gca().get_lines():
        for x_value, y_value in zip(line.get_xdata(), line.get_ydata()):
            if y_value in [1, 1.2, 1.5]:
                plt.annotate(f'Important: {y_value}', (x_value, y_value), textcoords="offset points", xytext=(0,10), ha='center')
    
    # Set a fixed y-axis range and custom y-ticks
    plt.ylim(ymin=0, ymax=10)
    plt.yticks(np.arange(0, 11, 1))  # Set y-ticks at every integer value
    
    # Add custom vertical lines and ticks
    plt.axvline(x=25, color='black', linestyle='--')
    plt.axvline(x=35, color='black', linestyle='--')
    plt.xticks(ticks=np.arange(20, 41, 2))
    
    plt.tight_layout()  # Adjust the layout to make room for the y-axis label
    
    filename = f'{plots_dir}/{metric.replace("/", "_")}_combined.png'
    plt.savefig(filename)
    plt.close()
