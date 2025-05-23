#!/usr/bin/env python3

import json
import re
import os
from typing import Dict, List

def create_json (hepdata_path, mass_points_json):
    meta_data_values = extract_meta_data (mass_points_json)
    expected_values = loop_over_json_files (hepdata_path)
    #expected_values = extract_expected_limits (hepdata_path)
    output_data = meta_data_values
    output_data ["mass_points"] = expected_values
    filename = "../data/mass_points/SbbHtautau_CMS.json"
    with open(filename, 'w') as file:
        json.dump(output_data, file, indent=4 )

def extract_meta_data (mass_points_json):
    with open(mass_points_json, 'r', encoding=' utf-8') as file:
        data = json.load(file)     

    meta_data = {}
    meta_data ['collaboration'] = data['collaboration']
    meta_data ['arxiv'] = data['arxiv']
    meta_data ['doi'] = data['doi']
    meta_data ['year'] = data['year']
    meta_data ['sqrt_s'] = data['sqrt_s']
    meta_data ['decay_channel'] = data['decay_channel']
    return meta_data

def loop_over_json_files(directory_path):

    all_results = []
    for file_name in sorted(os.listdir(directory_path),  key=lambda f: int(re.search(r'\d+', f).group())):
        file_path = os.path.join(directory_path, file_name)
        if file_name.endswith('.json'):
            mx: int = int(re.search(r'\d+', file_name).group())
            file_results = extract_expected_limits(file_path, mx)
            all_results.extend(file_results)

    return all_results

def extract_expected_limits(hep_data_json: str,
                            mx: int = 0) -> List[Dict[str, any]]:
    with open(hep_data_json, 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    expected_limits = []
    
    for entry in data.get("values", []):
        if "y" in entry and len(entry["y"]) > 0:
            
            new_points = {#"mX" : float(entry["x"][0]["value"]), 
                          "mX" : mx,
                          "mS" : int(entry["x"][0]["value"]),
                          "expected_limit" : float(entry["y"][1]["value"]),
                          "observed_limit" : float(entry["y"][0]["value"]),
                          "resolvable" : True }

            expected_limits.append(new_points)

    return expected_limits

if __name__ == "__main__":
    mass_points_json = "../data/mass_points/SbbHtautau_CMS_old.json"
    hep_data_path = "../data/hepdata/SbbHtautau_CMS" 
    #hep_data_path = "../data/hepdata/SHbbbb_CMS_boosted.json" # Replace with the actual JSON filename
    create_json (hep_data_path, mass_points_json)




