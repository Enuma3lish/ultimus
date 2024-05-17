import os
import pandas as pd
import matplotlib.pyplot as plt

# Load the data
data = pd.read_csv('/home/melowu/Work/expri/DataSet/result3.csv')  # Adjust this to the path of your CSV file

# Specify the specific values for quantum_multiplier and quantum_increase
quantum_multiplier = [1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]
quantum_increase = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]

# Define the metrics you're interested in
metrics = [
    'MMLFQ_L2_Norm/SRPT_L2_Norm',
    'MMLFQ_L2_Norm/FCFS_L2_Norm',
    'MMLFQ_L2_Norm/RR_L2_Norm',
    'MMLFQ_L2_Norm/SETF_L2_Norm'
]

# Ensure directory for plots exists or is created
plots_dir = "img/result3"
os.makedirs(plots_dir, exist_ok=True)

for i in quantum_multiplier:
    for j in quantum_increase:
        # Filter data for the specific quantum_multiplier and quantum_increase
        filtered_data = data[(data['quantum_multiplier'] == i) & (data['quantum_decrease'] == j)]

        for metric in metrics:
            plt.figure(figsize=(10, 6))

            for bp_param in filtered_data['bp_parameter'].unique():
                specific_data = filtered_data[filtered_data['bp_parameter'] == bp_param]

                if not specific_data.empty:
                    plt.plot(specific_data['arrival_rate'], specific_data[metric], marker='o', linestyle='-', label=f'BP={bp_param}')
                    
            # Check if any lines were added to the plot
            if len(plt.gca().get_lines()) > 0:
                plt.title(f'{metric} for QM {i}, QI {j}')
                plt.xlabel('Mean Arrival Time')
                plt.ylabel(metric)
                plt.legend(title='BP Parameter', loc='best')
                plt.grid(True)

                # Highlighting specific points
                plt.axhline(y=1.2, color='r', linestyle='--')  # Add a horizontal line at y=1.2
                plt.axhline(y=1.5, color='g', linestyle='--')  # Add a horizontal line at y=1.5
                
                # Annotating a specific point
                for line in plt.gca().get_lines():
                    for x_value, y_value in zip(line.get_xdata(), line.get_ydata()):
                        if y_value == 1.2 or y_value == 1.5:
                            plt.annotate(f'Important: {y_value}', (x_value, y_value), textcoords="offset points", xytext=(0,10), ha='center')

                # Set a fixed y-axis range
                plt.ylim(ymin=0, ymax=10)

                filename = f'{plots_dir}/{metric.replace("/", "_")}_QM{i}_QI{j}_BP_diff.png'
                plt.savefig(filename)
            
            plt.close()
