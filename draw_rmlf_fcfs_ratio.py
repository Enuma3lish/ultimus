import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import ast

def plot_ratio_trends(csv_file):
    try:
        # Create output directory for PDFs if it doesn't exist
        pdf_dir = 'ratio_pdfs'
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
            
        # Read the CSV file
        df = pd.read_csv(csv_file)
        
        # Convert arrival_rate to mean interarrival time
        df['mean_interarrival_time'] = df['arrival_rate']
        
        # Create figure with appropriate size
        plt.figure(figsize=(15, 10))
        
        # Set consistent markers and colors for BP parameters
        markers = {
            "{'L': 16.772, 'H': 64}": 'o',
            "{'L': 7.918, 'H': 512}": 's',
            "{'L': 5.649, 'H': 4096}": '^',
            "{'L': 4.639, 'H': 32768}": 'v',
            "{'L': 4.073, 'H': 262144}": 'D'
        }
        
        # Plot lines for each BP parameter
        for bp in markers.keys():
            # Filter data for this BP parameter
            mask = df['bp_parameter'] == bp
            data = df[mask].copy()
            
            # Sort by mean_interarrival_time
            data = data.sort_values('mean_interarrival_time')
            
            # Plot RMLF ratio (blue lines)
            plt.plot(data['mean_interarrival_time'], data['rmlf_ratio'], 
                    color='blue', marker=markers[bp],
                    linestyle='-', label=f"RMLF {bp}")
            
            # Plot FCFS ratio (red dashed lines)
            plt.plot(data['mean_interarrival_time'], data['fcfs_ratio'], 
                    color='red', marker=markers[bp],
                    linestyle='--', label=f"FCFS {bp}")

        # Customize the plot
        plt.title('Comparison of Usage Ratios for RMLF and FCFS (Check=64)', fontsize=12, pad=20)
        plt.xlabel('Mean Interarrival Time')
        plt.ylabel('Usage Ratio (%)')
        
        # Set x-axis ticks and range
        plt.xlim(20, 40)
        x_ticks = np.arange(20, 42, 2)
        plt.xticks(x_ticks)
        
        # Set y-axis range
        plt.ylim(0, 100)
        
        # Add grid
        plt.grid(True, alpha=0.3)
        
        # Customize legend
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)
        
        # Adjust layout to prevent legend cutoff
        plt.tight_layout()
        
        # Get number from input filename
        input_number = os.path.basename(csv_file).split('@')[0]
        
        # Save the plot
        output_filename = os.path.join(pdf_dir, f'ratio_trends_{input_number}.pdf')
        plt.savefig(output_filename, format='pdf', bbox_inches='tight', dpi=300)
        print(f"Created PDF: {output_filename}")
        
        # Close the plot
        plt.close()
        
    except FileNotFoundError:
        print(f"Error: File '{csv_file}' not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        csv_files = ['log/ratio1.csv','log/ratio2.csv','log/ratio4.csv','log/ratio8.csv','log/ratio16.csv','log/ratio30.csv']
        
        for csv_file in csv_files:
            print(f"\nProcessing {csv_file}...")
            plot_ratio_trends(csv_file)
            
    except Exception as e:
        print(f"Failed to execute the script: {str(e)}")