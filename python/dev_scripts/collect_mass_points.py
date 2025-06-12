#!/usr/bin/env python3

import os
import json

def collect_mass_points(output_filename):
    all_points = set()
    directory = os.path.join(os.environ['DATA_DIR'], "mass_points")
    output_path = os.path.join(directory, output_filename)

    # Read each JSON file in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".json") and os.path.join(directory, filename) != output_path:
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as f:
                try:
                    data = json.load(f)
                    for point in data.get("mass_points", []):
                        mX = point.get("mX")
                        mS = point.get("mS")
                        if isinstance(mX, int) and isinstance(mS, int):
                            all_points.add((mX, mS))
                except json.JSONDecodeError as e:
                    print(f"Error reading {filename}: {e}")

    # Convert set to sorted list of dicts
    sorted_points = sorted(all_points, key=lambda x: (x[0], x[1]))
    output = {"mass_points": [{"mX": mX, "mS": mS, "resolvable": True} for mX, mS in sorted_points]}

    # Write to output JSON
    with open(output_path, 'w') as out_f:
        json.dump(output, out_f, indent=2)
    print(f'Collected {len(output["mass_points"])} unique mass points into {output_filename}')

# Example usage
collect_mass_points("prescan_global.json")
