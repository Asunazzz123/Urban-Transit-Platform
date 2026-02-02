from pathlib import Path
import os



BASE_DIR = Path(__file__).resolve().parent.parent.parent
RESOURCE_DIR = BASE_DIR / 'resource'
JS_DIR = RESOURCE_DIR / 'js' / 'framework'
JSON_DIR = RESOURCE_DIR / 'json'
METRO_JSON_DIR = JSON_DIR / 'metro'
RAIL_JSON_DIR = JSON_DIR / 'rail'
