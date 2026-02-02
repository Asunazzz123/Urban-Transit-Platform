import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.constant import JSON_DIR
from pathlib import Path

class StationIndexer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StationIndexer, cls).__new__(cls)
            cls._instance.name_to_code = {}
            cls._instance.code_to_name = {}
            cls._instance.loaded = False
        return cls._instance

    def load_data(self, json_path=None):
        if self.loaded and not json_path:
            return

        if json_path is None:
            json_path = JSON_DIR / "station.json"
        
        if not os.path.exists(json_path):
            print(f"Error: Station file not found at {json_path}")
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for city in data:
                    for station in city.get('stations', []):
                        name = station.get('station')
                        code = station.get('id')
                        if name and code:
                            self.name_to_code[name] = code
                            self.code_to_name[code] = name
            self.loaded = True
            print(f"Index loaded: {len(self.name_to_code)} stations.")
        except Exception as e:
            print(f"Failed to load station index: {e}")

    def get_code(self, name):
        if not self.loaded:
            self.load_data()
        return self.name_to_code.get(name)

    def get_name(self, code):
        if not self.loaded:
            self.load_data()
        return self.code_to_name.get(code, code)

    def update_mapping(self, map_info):
        if not map_info:
            return
        self.code_to_name.update(map_info)
        # Simultaneously update reverse mapping
        for code, name in map_info.items():
            self.name_to_code[name] = code

# Global instance
indexer = StationIndexer()

def link(file_path, start_station=None, destination_station=None, **kwargs):
    # Support extracting arguments from kwargs
    if start_station is None:
        start_station = kwargs.get('start_station')
    
    if destination_station is None:
        destination_station = kwargs.get('destination_station') or kwargs.get('destination')
        
    # Use the indexer for efficient lookup
    # Note: file_path argument is kept for compatibility but we prefer using the internal loader if pointing to default
    
    # Check if we need to reload from a specific file, or just use the singleton
    # For optimization, we use the singleton indexer
    start_code = indexer.get_code(start_station)
    dest_code = indexer.get_code(destination_station)
            
    return {
        "start_station": start_code,
        "destionation_station": dest_code
    }


if __name__ == "__main__":
    # Test the function
    json_path = JSON_DIR / "station.json"
    print(f"Looking for JSON at: {json_path}")
    
    # Example usage
    result = link(str(json_path), "北京南", "上海虹桥")
    print("Result:", result)
    