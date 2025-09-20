import re


def extract_version_from_path(folder_path):
    """Extract version number (1-10) from folder path like 'avg_30_2' or 'freq_16_2'"""
    # Match patterns like avg_30_1, freq_16_2, softrandom_3, etc.
    pattern = r'_(\d+)$'
    match = re.search(pattern, folder_path)
    if match:
        return int(match.group(1))