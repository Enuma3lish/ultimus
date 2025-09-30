import glob
import os
import extract_version_from_path as evfp
import parse_freq_from_folder as pfff
import read_jobs_from_csv as rjfc
import csv
import logging
import run_random 

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_softrandom_folders(algo, algo_name, data_dir, output_dir):
    """Process all softrandom_* folders"""
    
    # Create output directory
    softrandom_result_dir = os.path.join(output_dir, 'softrandom_result')
    os.makedirs(softrandom_result_dir, exist_ok=True)
    
    # Group results by version number
    results_by_version = {}
    
    # Find all softrandom base folders with version numbers
    softrandom_folders = glob.glob(os.path.join(data_dir, 'softrandom_*'))
    
    for softrandom_base in sorted(softrandom_folders):
        if not os.path.isdir(softrandom_base):
            continue
            
        base_folder_name = os.path.basename(softrandom_base)
        base_version = evfp.extract_version_from_path(base_folder_name)
        
        logger.info(f"Processing softrandom base: {base_folder_name} (version={base_version})")
        
        # Look for freq_* folders inside softrandom
        freq_folders = glob.glob(os.path.join(softrandom_base, 'freq_*'))
        
        for freq_folder in sorted(freq_folders):
            if not os.path.isdir(freq_folder):
                continue
                
            folder_name = os.path.basename(freq_folder)
            frequency = pfff.parse_freq_from_folder(folder_name)
            
            if frequency is None:
                logger.warning(f"Could not parse frequency from folder: {folder_name}")
                continue
            
            logger.info(f"  Processing subfolder: {folder_name} (freq={frequency})")
            
            # Look for softrandom_freq_*.csv files
            softrandom_files = glob.glob(os.path.join(freq_folder, 'softrandom_freq_*.csv'))
            
            for softrandom_file in softrandom_files:
                filename = os.path.basename(softrandom_file)
                logger.info(f"    Processing {filename}")
                
                # Read jobs
                jobs = rjfc.read_jobs_from_csv(softrandom_file)
                if jobs is None:
                    continue
                
                # Run algorithm
                try:
                    l2_results, max_flow_results = run_random.run_random(algo, jobs)
                    logger.info(f"  Results: L2={l2_results:.4f}, Max Flow={max_flow_results:.4f}")
                except Exception as e:
                    logger.error(f"Error processing {softrandom_file}: {e}")  # FIXED: variable name
                    continue
                
                # Group results by version
                if base_version not in results_by_version:
                    results_by_version[base_version] = []
                
                # FIXED: Use base_version instead of version
                results_by_version[base_version].append({
                    'frequency': frequency,
                    'l2_results': l2_results,
                    'max_flow_results': max_flow_results
                })
    
    # Write results grouped by version
    for version, results in results_by_version.items():
        if results:
            if version:
                output_file = os.path.join(softrandom_result_dir, f"softrandom_result_{algo_name}_{version}.csv")
            else:
                output_file = os.path.join(softrandom_result_dir, f"softrandom_result_{algo_name}.csv")
            
            logger.info(f"Writing {len(results)} results to {output_file}")  # Added logging
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Header format: frequency,{algo_name}_L2_norm_flow_time,{algo_name}_maximum_flow_time'
                header = ['frequency', f'{algo_name}_L2_norm_flow_time', f'{algo_name}_maximum_flow_time']
                writer.writerow(header)
                
                # Sort by frequency
                results.sort(key=lambda x: x['frequency'])
                
                # Write data rows
                for result in results:
                    row = [
                        result['frequency'],
                        result['l2_results'] if result['l2_results'] is not None else '',
                        result['max_flow_results'] if result['max_flow_results'] is not None else ''
                    ]
                    writer.writerow(row)
                    logger.debug(f"  Wrote row: {row}")
            
            logger.info(f"  Saved softrandom results (version {version}) to {output_file}")