import os
import pandas as pd
import matplotlib.pyplot as plt

# Load the data
data = pd.read_csv('/home/melowu/Work/expri/DataSet/result.csv')  # Adjust this to the path of your CSV file

# Specify the specific values for quantum_multiplier and quantum_decrease
quantum_multiplier = [1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]
quantum_increase = [0, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
# Define the metrics you're interested in
metrics = [
    'MMLFQ_L2_Norm/SRPT_L2_Norm',
    'SMLFQ_L2_Norm/SRPT_L2_Norm',
    'MMLFQ_L2_Norm/FCFS_L2_Norm',
    'SMLFQ_L2_Norm/FCFS_L2_Norm',
    'SMLFQ_L2_Norm/RR_L2_Norm',
    'SMLFQ_L2_Norm/SETF_L2_Norm',
    'SMLFQ_L2_Nprm/MMLFQ_L2_Norm'
]

# Ensure directory for plots exists or is created
plots_dir = "img"
os.makedirs(plots_dir, exist_ok=True)

for i in quantum_multiplier:
    for j in quantum_increase:
        # Filter data for the specific quantum_multiplier and quantum_decrease
        filtered_data = data[(data['quantum_multiplier'] == i) & (data['quantum_increase'] == j)]
        for metric in metrics:
            plt.figure(figsize=(10, 6))
            
            for bp_param in filtered_data['bp_parameter'].unique():
                specific_data = filtered_data[filtered_data['bp_parameter'] == bp_param]

                if not specific_data.empty:
                    plt.plot(specific_data['arrival_rate'], specific_data[metric], marker='o', linestyle='-', label=f'BP={bp_param}')
                    
            # Check if any lines were added to the plot
            if len(plt.gca().get_lines()) > 0:
                plt.title(f'{metric} for QM {i}, QD {j}')
                plt.xlabel('Arrival Rate')
                plt.ylabel(metric)
                plt.legend(title='BP Parameter', loc='best')
                plt.grid(True)

                filename = f'{plots_dir}/{metric.replace("/", "_")}_QM{i}_QD{j}_BP_diff.png'
                plt.savefig(filename)
            
            plt.close()
