import pandas as pd
import matplotlib.pyplot as plt
import json

# Load the CSV file into 'df'
file_path = '/home/melowu/Work/expri/DataSet/result32.csv'
df = pd.read_csv(file_path)

# Assuming you want to focus on a subset of 'df' with fixed 'base_quantum'
filtered_df = df[df['base_quantum'] == 15].copy()

# Define your new_bp_parameters
new_bp_parameters = [
    {"L": 16.772, "H": pow(2, 6)},
    {"L": 7.918, "H": pow(2, 9)},
    {"L": 5.649, "H": pow(2, 12)},
    {"L": 4.639, "H": pow(2, 15)},
    {"L": 4.073, "H": pow(2, 18)}
]

# Manually extend the new_bp_parameters list to match the length of filtered_df
# Here we use a simple repetition pattern
extended_bp_parameters = (new_bp_parameters * (len(filtered_df) // len(new_bp_parameters) + 1))[:len(filtered_df)]

# Now you can safely serialize each dictionary in the extended list to JSON
filtered_df['bp_parameter'] = [json.dumps(bp) for bp in extended_bp_parameters]
filtered_df['L_value'] = [bp['L'] for bp in extended_bp_parameters]

# Plotting and annotating, adjusted for starting annotations from 0
plt.figure(figsize=(14, 7))
plt.plot(filtered_df['quantum_multiplier'], filtered_df['RMLFQ_L2_Norm/SRPT_L2_Norm'], label='RMLFQ_L2_Norm/SRPT_L2_Norm', marker='o')

for i, row in filtered_df.iterrows():
    plt.annotate(f"{i % len(new_bp_parameters)}: L={row['L_value']}", 
                 (row['quantum_multiplier'], row['RMLFQ_L2_Norm/SRPT_L2_Norm']),
                 textcoords="offset points", xytext=(0,10), ha='center')

plt.title('Trend of RMLFQ_L2_Norm/SRPT_L2_Norm across Quantum Multipliers')
plt.xlabel('Quantum Multiplier')
plt.ylabel('RMLFQ_L2_Norm/SRPT_L2_Norm Value')
plt.legend()
plt.grid(True)

# Save the plot as a PDF
pdf_path = '/home/melowu/Work/expri/DataSet/result32.pdf'
plt.savefig(pdf_path)
plt.close()

# Output the path to the saved PDF file
print(pdf_path)
