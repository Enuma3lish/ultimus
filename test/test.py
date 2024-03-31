import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import combinations
import os

def draw(csv_path, output_folder):
    df = pd.read_csv(csv_path)

    # Define the specific groups of interest
    specific_combinations = [
        ('RMLFQ_L2_Norm/SRPT_L2_Norm', 'RMLFQ_L2_Norm/FCFS_L2_Norm'),
        ('RMLFQ_L2_Norm/BAL_L2_Norm',)  # Single element tuple for consistency
    ]

    # Plot for each specific combination group
    for combination_group in specific_combinations:
        if len(combination_group) == 1:
            # Handle the single combination case
            plot_combination(df, combination_group[0], output_folder, single=True)
        else:
            # Handle the case with multiple combinations (pairwise)
            plot_combination(df, combination_group, output_folder)

def plot_combination(df, combinations, output_folder, single=False):
    # Filter the DataFrame based on the combinations provided
    if single:
        df_filtered = df[df['arithmetic'] == combinations]
        title = combinations
    else:
        df_filtered = df[df['arithmetic'].isin(combinations)]
        title = " vs ".join(combinations)

    # Plotting
    plt.figure(figsize=(10, 6))
    sns.lineplot(
        data=df_filtered, x="arrival_rate", y="value", hue="arithmetic", style="bp_parms", markers=True,
        dashes=False, palette="tab10", estimator=None, linewidth=1
    )
    plt.title(title)
    plt.legend(loc='upper right')
    plt.xlabel("Mean Inter Arrival Time")
    plt.ylabel("Comparison")
    plt.tight_layout()

    # Save the plot
    output_filename = title.replace('/', '_').replace(' ', '_') + '.pdf'
    save_plot(output_folder, output_filename)

def save_plot(output_folder, filename):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    plt_path = os.path.join(output_folder, filename)
    plt.savefig(plt_path)
    plt.close()  # Close the plot to free memory and avoid overlap in subsequent plots

draw("/home/melowu/Work/expri/test/l2norm_compare_with_needed.csv","/home/melowu/Work/expri/test")
# Example call
# draw('path/to/your.csv', 'path/to/output_folder')
