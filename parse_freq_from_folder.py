import re


def parse_freq_from_folder(folder_name):
    """Extract frequency value from folder name like freq_2"""
    pattern = r'freq_(\d+)(?:_\d+)?'
    match = re.search(pattern, folder_name)
    if match:
        return int(match.group(1))
    return None