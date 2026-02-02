import re
import json
import os
import sys
from pathlib import Path
# Add src directory to sys.path to allow importing utils
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.constant import BASE_DIR, JSON_DIR, JS_DIR

def parse_station_names(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract the string content inside single quotes
    match = re.search(r"var station_names ='([^']+)';", content)
    if not match:
        print("Could not find station_names variable.")
        return

    data_str = match.group(1)
    stations = data_str.split('@')
    
    city_map = {}

    for station_str in stations:
        if not station_str:
            continue
        
        parts = station_str.split('|')
        if len(parts) < 8:
            continue

        # Mapping based on observation:
        # 0: bjb (abbr/code?)
        # 1: 北京北 (station name)
        # 2: VAP (id)
        # 3: beijingbei (pinyin)
        # 4: bjb (short pinyin)
        # 5: 0 (no)
        # 6: 0357 (cityid)
        # 7: 北京 (city name)

        abbr = parts[0]
        station_name = parts[1]
        station_id = parts[2]
        # pinyin = parts[3]
        # short_pinyin = parts[4]
        no = parts[5]
        city_id = parts[6]
        city_name = parts[7]

        if city_name not in city_map:
            city_map[city_name] = {
                "city": city_name,
                "cityid": city_id,
                "stations": []
            }
        
        # Verify city_id matches (it should, but just in case)
        if city_map[city_name]["cityid"] != city_id:
            # Handle potential conflict or just ignore
            pass

        station_obj = {
            "station": station_name,
            "abbr": abbr,
            "id": station_id,
            "no": no
        }
        
        city_map[city_name]["stations"].append(station_obj)

    # Convert map to list
    result = list(city_map.values())
    
    return result


def main():
    # Try to find the file relative to current script or absolute
    possible_paths = []
    possible_paths.append(JS_DIR / 'station_name.js')
    input_path = None
    for p in possible_paths:
        if os.path.exists(p):
            input_path = p
            break
             
    if not input_path:
        print("Could not find station_name.js")
        return 0

    print(f"Reading from {input_path}")
    data = parse_station_names(input_path)
    
    output_path = JSON_DIR / 'station.json'
    if data:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Successfully wrote to {os.path.abspath(output_path)}")
    else:
        print("No data extracted.")

if __name__ == "__main__":
    main()
