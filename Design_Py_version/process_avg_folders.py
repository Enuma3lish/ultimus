import glob
import os
import re
import extract_version_from_path as evfp
import run
import logging
import read_jobs_from_csv as rjfc
import csv
import parse_avg_filename as paf

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_avg_folders(algo, algo_name, data_dir, output_dir):
    """Process all avg_30_*, avg_60_*, avg_90_* folders"""
    
    # Find all avg folders with version numbers
    avg_patterns = ['avg_30_*']
    
    for pattern in avg_patterns:
        avg_folders = glob.glob(os.path.join(data_dir, pattern))
        
        for avg_folder in sorted(avg_folders):
            if not os.path.isdir(avg_folder):
                continue
                
            folder_name = os.path.basename(avg_folder)
            version = evfp.extract_version_from_path(folder_name)
            
            # Extract avg type (30, 60, or 90)
            avg_type_match = re.search(r'avg_(\d+)', folder_name)
            if not avg_type_match:
                continue
            avg_type = avg_type_match.group(1)
            
            logger.info(f"Processing folder: {folder_name} (version={version})")
            
            # Create output directory
            avg_result_dir = os.path.join(output_dir, f'avg{avg_type}_result')
            os.makedirs(avg_result_dir, exist_ok=True)
            
            # Group results by arrival_rate
            results_by_arrival_rate = {}
            
            # Process all CSV files in this folder
            csv_files = glob.glob(os.path.join(avg_folder, '*.csv'))
            
            for csv_file in csv_files:
                filename = os.path.basename(csv_file)
                arrival_rate, bp_L, bp_H = paf.parse_avg_filename(filename)
                
                if arrival_rate is None:
                    logger.warning(f"Could not parse filename: {filename}")
                    continue
                
                logger.info(f"  Processing {filename}: arrival_rate={arrival_rate}, bp_L={bp_L}, bp_H={bp_H}")
                
                # Read jobs
                jobs = rjfc.read_jobs_from_csv(csv_file)
                if jobs is None:
                    continue
                
                # Run Algorithm
                _results = run.run(algo, jobs)
                
                # Store results
                if arrival_rate not in results_by_arrival_rate:
                    results_by_arrival_rate[arrival_rate] = []
                
                results_by_arrival_rate[arrival_rate].append({
                    'bp_parameter_L': bp_L,
                    'bp_parameter_H': bp_H,
                    'results': _results
                })
            
            # Write results grouped by arrival_rate with version number
            for arrival_rate, results in results_by_arrival_rate.items():
                if version:
                    output_file = os.path.join(avg_result_dir, f"{int(arrival_rate)}_{algo_name}_{version}_result.csv")
                else:
                    output_file = os.path.join(avg_result_dir, f"{int(arrival_rate)}_{algo_name}_result.csv")
                
                with open(output_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Header format: arrival_rate,bp_parameter_L,bp_parameter_H,{algo_name}_L2_norm_flow_time
                    header = ['arrival_rate', 'bp_parameter_L', 'bp_parameter_H', f'{algo_name}_L2_norm_flow_time']
                    writer.writerow(header)
                    
                    # Sort results by bp_L and bp_H for consistency
                    results.sort(key=lambda x: (x['bp_parameter_L'], x['bp_parameter_H']))
                    
                    # Write data rows
                    for result in results:
                        row = [arrival_rate, result['bp_parameter_L'], result['bp_parameter_H']]
                        # Put calculated L2 norm flow time under the corresponding column
                        value = result['results']
                        row.append(value if value is not None else '')
                        writer.writerow(row)
                
                logger.info(f"  Saved results for arrival_rate={arrival_rate} to {output_file}")