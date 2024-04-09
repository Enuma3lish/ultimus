import pandas as pd
import matplotlib.pyplot as plt
import json

# Load the CSV file into 'df'
file_path = '/home/melowu/Work/expri/DataSet/result32.csv'
df = pd.read_csv(file_path)

# Assuming you want to focus on a subset of 'df' with fixed 'base_quantum'
filtered_df = df[df['base_quantum'] == 15].copy()

# Correctly parse the 'L' value from the 'bp_parameter' JSON string
filtered_df['L_value'] = filtered_df['bp_parameter'].apply(lambda x: json.loads(x.replace("'", "\""))['L'])

# Start plotting
plt.figure(figsize=(14, 7))

# Plot points for RMLFQ_L2_Norm/SRPT_L2_Norm and RMLFQ_L2_Norm/FCFS_L2_Norm, and annotate with 'L' value
for index, row in filtered_df.iterrows():
    # Plot for RMLFQ_L2_Norm/SRPT_L2_Norm
    plt.scatter(row['quantum_multiplier'], row['RMLFQ_L2_Norm/SRPT_L2_Norm'], color='blue', label='RMLFQ/SRPT' if index == 0 else "")
    plt.annotate(f"{row['L_value']}", 
                 (row['quantum_multiplier'], row['RMLFQ_L2_Norm/SRPT_L2_Norm']),
                 textcoords="offset points", xytext=(5,-5), ha='right', fontsize=9)
    
    # Plot for RMLFQ_L2_Norm/FCFS_L2_Norm
    plt.scatter(row['quantum_multiplier'], row['RMLFQ_L2_Norm/FCFS_L2_Norm'], color='red', label='RMLFQ/FCFS' if index == 0 else "")
    plt.annotate(f"{row['L_value']}", 
                 (row['quantum_multiplier'], row['RMLFQ_L2_Norm/FCFS_L2_Norm']),
                 textcoords="offset points", xytext=(5,-5), ha='right', fontsize=9)

# Set plot title and labels
plt.title('Comparison of RMLFQ Normalized Performance over Quantum Multipliers', fontsize=14)
plt.xlabel('Quantum Multiplier', fontsize=12)
plt.ylabel('Normalized Performance Value', fontsize=12)

# Create the legend
handles, labels = plt.gca().get_legend_handles_labels()
by_label = dict(zip(labels, handles))
plt.legend(by_label.values(), by_label.keys(), fontsize=10)

# Improve legibility
plt.xticks(filtered_df['quantum_multiplier'].unique(), fontsize=10)
plt.yticks(fontsize=10)

# Add gridlines
plt.grid(True, linestyle='--', alpha=0.5)

# Adjust layout to fit all elements and save the plot as a PDF
plt.tight_layout()
pdf_path = '/home/melowu/Work/expri/DataSet/result32_value_next_to_marker.pdf'
plt.savefig(pdf_path)
plt.close()

# Print the path to the saved PDF file
print(pdf_path)
