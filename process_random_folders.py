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
def process_random_folders(algo,algo_name,data_dir, output_dir):
    """Process all freq_* folders for random files"""
    # Create output directory
    random_result_dir = os.path.join(output_dir, 'random_result')
    os.makedirs(random_result_dir, exist_ok=True)
    
    # Group results by version number
    results_by_version = {}
    
    # Find all freq folders
    freq_folders = glob.glob(os.path.join(data_dir, 'freq_*'))
    
    for freq_folder in sorted(freq_folders):
        if not os.path.isdir(freq_folder):
            continue
            
        folder_name = os.path.basename(freq_folder)
        frequency = pfff.parse_freq_from_folder(folder_name)
        version = evfp.extract_version_from_path(folder_name)
        
        if frequency is None:
            logger.warning(f"Could not parse frequency from folder: {folder_name}")
            continue
        
        logger.info(f"Processing folder: {folder_name} (freq={frequency}, version={version})")
        
        # Look for random_freq_*.csv files
        random_files = glob.glob(os.path.join(freq_folder, 'random_freq_*.csv'))
        
        for random_file in random_files:
            filename = os.path.basename(random_file)
            logger.info(f"  Processing {filename}")
            
            # Read jobs
            jobs = rjfc.read_jobs_from_csv(random_file)
            if jobs is None:
                continue
            
            # Run BAL
            _results = run.run(algo,jobs)
            # Group results by version
            if version not in results_by_version:
                results_by_version[version] = []
            
            results_by_version[version].append({
                'frequency': frequency,
                'results': _results
            })
    
    # Write results grouped by version
    for version, results in results_by_version.items():
        if results:
            if version:
                output_file = os.path.join(random_result_dir, f"random_result_{algo_name}_{version}.csv")
            else:
                output_file = os.path.join(random_result_dir, f"random_result_{algo_name}.csv")
            
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
            
            logger.info(f"  Saved random results (version {version}) to {output_file}")