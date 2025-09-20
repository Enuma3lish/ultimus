import glob
import os
import extract_version_from_path as evfp
import parse_freq_from_folder as pfff
import read_jobs_from_csv as rjfc
import csv
import logging
import run 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
def process_softrandom_folders(algo,algo_name,data_dir, output_dir):
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
                _results = run.run(algo,jobs)
                # Group results by version
                if base_version not in results_by_version:
                    results_by_version[base_version] = []
                
                results_by_version[base_version].append({
                    'frequency': frequency,
                    'results':_results
                })
    
    # Write results grouped by version
    for version, results in results_by_version.items():
        if results:
            if version:
                output_file = os.path.join(softrandom_result_dir, f"softrandom_result_{algo_name}_{version}.csv")
            else:
                output_file = os.path.join(softrandom_result_dir, f"softrandom_result_{algo_name}.csv")
            
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Create header - FIXED format
                header = ['frequency']
                writer.writerow(header)
                
                # Sort by frequency
                results.sort(key=lambda x: x['frequency'])
                
                # Write data rows
                for result in results:
                    row = [result['frequency']]
                    value = result['results']
                    row.append(value if value is not None else '')
                    writer.writerow(row)
            
            logger.info(f"  Saved softrandom results (version {version}) to {output_file}")
