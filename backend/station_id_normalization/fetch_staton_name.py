import requests
import re
import json
import os
from utils.constant import BASE_DIR, JS_DIR
class StationFetcher:
    def __init__(self):
        self.url = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
        self.header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.output_dir = JS_DIR

    def fetch(self):
        try:
            response = requests.get(self.url, headers=self.header, timeout=10)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching station data: {e}")
            return None
    def save_js(self,content,filename="station_name.js"):
        path = os.path.join(self.output_dir, filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def run(self):
        content = self.fetch()
        if content:
            self.save_js(content)

    