import re


def parse_avg30_filename(filename):
    """Parse avg30 filename to extract arrival_rate, bp_L, and bp_H"""
    # Pattern: (arrival_rate, bp_L_bp_H).csv
    # Example: (20, 4.073_262144).csv or (28, 7.918_512).csv
    pattern = r'\((\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)_(\d+)\)'
    match = re.search(pattern, filename)
    if match:
        arrival_rate = float(match.group(1))
        bp_L = float(match.group(2))
        bp_H = int(match.group(3))
        return arrival_rate, bp_L, bp_H
    return None, None, None