import requests
import time
import json
import random
import sys
import os
import csv
from datetime import datetime
#from station_id_normalization.station_id_link import link
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.constant import JSON_DIR, RESOURCE_DIR
from station_id_normalization.station_id_link import link, indexer

class TicketCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False  # 忽略系统代理设置，防止 ProxyError
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
            "Host": "kyfw.12306.cn"
        })
        self.init_cookies()
        
        self.station_codes_map = JSON_DIR / "station.json"
        
        # 预加载车站数据（利用 StationIndexer 的单例机制）
        print("正在加载车站信息...")
        indexer.load_data(self.station_codes_map)
        
        self.query_url = "https://kyfw.12306.cn/otn/leftTicket/queryG"

    def init_cookies(self):
        try:
            print("正在初始化 Cookie (访问 init 页面)...")
            # 访问查询页面以获取必要的 Cookie
            self.session.get("https://kyfw.12306.cn/otn/leftTicket/init", timeout=10)
            print("Cookie 初始化成功")
            print("当前 Cookies:", self.session.cookies.get_dict())
        except Exception as e:
            print(f"Cookie 初始化失败: {e}")

    def get_station_name(self, code):
        return indexer.get_name(code)
    
    def get_station_code(self,start_station,destination_station):
        # 仍然调用 link 函数，但现在 link 内部使用 StationIndexer，避免了重复 IO
        return link(str(self.station_codes_map), start_station, destination_station)
    
    def query(self, from_station_name, to_station_name, date, is_student=False, is_high_speed=False, strict_mode=False):
        # 使用字典解包(unpacking)语法直接获取值
        codes = self.get_station_code(from_station_name, to_station_name)
        from_code, to_code = codes.values()
        

        if not from_code or not to_code:
            print(f"错误: 找不到车站代码 - {from_station_name} 或 {to_station_name}")
            return []

        params = {
            "leftTicketDTO.train_date": date,
            "leftTicketDTO.from_station": from_code,
            "leftTicketDTO.to_station": to_code,
            "purpose_codes": "0X00" if is_student else "ADULT"
        }

        try:
            print(f"DEBUG: 请求 URL: {self.query_url}")
            print(f"DEBUG: 请求参数: {params}")
            # print(f"DEBUG: 当前 Headers: {self.session.headers}")
            
            response = self.session.get(self.query_url, params=params, timeout=10)
            
            print(f"DEBUG: 响应状态码: {response.status_code}")
            
            # 检查是否需要更新 URL (12306 动态 URL 机制)
            if response.status_code == 200:
                try:
                    data = response.json()
                    # print(f"DEBUG: 响应数据预览: {str(data)[:200]}...")
                    
                    if "c_url" in data:
                        self.query_url = "https://kyfw.12306.cn/otn/" + data["c_url"]
                        print(f"更新查询接口为: {self.query_url}")
                        # 使用新 URL 重试
                        return self.query(from_station_name, to_station_name, date, is_student, is_high_speed, strict_mode)
                    
                    if "data" in data and "result" in data["data"]:
                        return self.parse_result(data["data"], is_high_speed, strict_query_codes=(from_code, to_code) if strict_mode else None)
                    else:
                        print("查询结果为空或格式错误")
                        print(f"DEBUG: 完整响应: {data}")
                        return []
                except json.JSONDecodeError:
                    print("解析响应失败")
                    print(f"DEBUG: 响应内容不是 JSON: {response.text[:200]}")
                    return []
            else:
                print(f"请求失败: {response.status_code}")
                return []

        except Exception as e:
            print(f"发生异常: {e}")
            import traceback
            traceback.print_exc()
            return []

    def parse_result(self, data, is_high_speed, strict_query_codes=None):
        results = []
        raw_list = data.get("result", [])
        map_info = data.get("map", {})
        
        # 更新 StationIndexer 的全局映射
        indexer.update_mapping(map_info)

        for item in raw_list:
            parts = item.split("|")
            if len(parts) < 30:
                continue

            # 数据索引映射 (基于常见 12306 结构)
            # 3: 车次
            # 6: 出发地代码
            # 7: 目的地代码
            # 8: 出发时间
            # 9: 到达时间
            # 10: 历时
            # 30: 二等座
            # 31: 一等座
            # 32: 商务座
            # 26: 无座
            # 29: 硬座
            # 28: 硬卧
            # 23: 软卧
            
            train_no = parts[3]
            
            # 过滤高铁/动车
            if is_high_speed and not (train_no.startswith("G") or train_no.startswith("D") or train_no.startswith("C")):
                continue

            from_station_code = parts[6]
            to_station_code = parts[7]
            
            # 严格模式筛选：如果设置了 strict_query_codes，则要求出发或到达站必须完全匹配查询值
            if strict_query_codes:
                q_from, q_to = strict_query_codes
                # 这里可以根据需求决定是"且"还是"或"。
                # 通常严格模式意味着：出发站必须是我查的那个站，到达站必须是我查的那个站
                if from_station_code != q_from or to_station_code != q_to:
                    continue

            start_time = parts[8]
            arrive_time = parts[9]
            duration = parts[10]
            
            # 获取车站名
            from_station = self.get_station_name(from_station_code)
            to_station = self.get_station_name(to_station_code)

            # 票务信息
            tickets = {}
            if parts[32] and parts[32] != "无" and parts[32] != "": tickets["商务座"] = parts[32]
            if parts[25] and parts[25] != "无" and parts[25] != "": tickets["特等座"] = parts[25]
            if parts[31] and parts[31] != "无" and parts[31] != "": tickets["一等座"] = parts[31]
            if parts[30] and parts[30] != "无" and parts[30] != "": tickets["二等座"] = parts[30]
            if parts[23] and parts[23] != "无" and parts[23] != "": tickets["软卧"] = parts[23]
            if parts[28] and parts[28] != "无" and parts[28] != "": tickets["硬卧"] = parts[28]
            if parts[29] and parts[29] != "无" and parts[29] != "": tickets["硬座"] = parts[29]
            if parts[26] and parts[26] != "无" and parts[26] != "": tickets["无座"] = parts[26]

            # Determine High Speed status
            if is_high_speed:
                hs_val = 'y'
            else:
                if train_no.startswith(("G", "D", "C")):
                    hs_val = 'y'
                else:
                     hs_val = 'n'

            train_info = {
                "车次": train_no,
                "出发站": from_station,
                "到达站": to_station,
                "出发时间": start_time,
                "到达时间": arrive_time,
                "历时": duration,
                "余票": tickets,
                "hs": hs_val
            }
            results.append(train_info)
            
        return results

def start_polling(from_station, to_station, date, is_student=False, is_high_speed=False, interval=5, strict_mode=False):
    crawler = TicketCrawler()
    print(f"开始查询: {date} {from_station} -> {to_station} (高铁/动车: {is_high_speed}, 学生票: {is_student}, 严格模式: {strict_mode})")
    
    count = 1
    while True:
        print(f"\n--- 第 {count} 次查询 ---")
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"查询时间: {current_time}")
        
        results = crawler.query(from_station, to_station, date, is_student, is_high_speed, strict_mode)
        
        if results:
            print(f"{'车次':<6} {'出发-到达':<12} {'时间':<12} {'历时':<6} {'余票信息'}")
            print("-" * 80)
            for train in results:
                time_str = f"{train['出发时间']}-{train['到达时间']}"
                stations = f"{train['出发站']}-{train['到达站']}"
                tickets = ", ".join([f"{k}:{v}" for k, v in train['余票'].items()])
                print(f"{train['车次']:<6} {stations:<12} {time_str:<12} {train['历时']:<6} {tickets}")
        else:
            print("未查询到符合条件的车次或请求被拒绝。")
            
        
        sleep_time = random.uniform(interval * 0.7, interval )
        print(f"随机等待 {sleep_time:.2f} 秒 (设定均值: {interval}s)...")
        time.sleep(sleep_time)
        count += 1
def start_polling_storage(from_station, to_station, date, is_student=False, is_high_speed=False, interval=5, strict_mode=False, should_stop=None):
    """
    Start polling for train tickets and store results in CSV.
    
    Args:
        should_stop: A callable that returns True when the crawler should stop
    """
    crawler = TicketCrawler()
    count = 1
    
    # 构建CSV存储路径 / Build CSV storage path
    csv_dir = RESOURCE_DIR / "csv"
    if not csv_dir.exists():
        csv_dir.mkdir(parents=True, exist_ok=True)
        
    filename = csv_dir / f"train_data_{date}_{from_station}_{to_station}.csv"
    print(f"开始轮询存储: {filename} (高铁: {is_high_speed}, 学生: {is_student})")
    
    # 字段映射
    fieldnames = [
        "count", "train_code", "departure_station", "destination_station", "depart_time", "arrive_time", "during_time",
        "business_class", "special_class", "first_class", "second_class", 
        "soft_sleeper", "hard_sleeper", "hard_seat", "no_seat", "strict_mode", "hs"
    ]
    
    # 若文件已存在，先删除，保证为一次性文件
    if filename.exists():
        try:
            filename.unlink()
        except Exception as e:
            print(f"删除旧文件失败: {e}")

    # 写入表头
    with open(filename, mode='w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

    while True:
        # Check if should stop
        if should_stop and should_stop():
            print(f"\n收到停止信号，停止轮询: {from_station} -> {to_station}")
            break
            
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            print(f"\n--- 第 {count} 次查询 ({current_time}) ---")
            
            results = crawler.query(from_station, to_station, date, is_student, is_high_speed, strict_mode)
            
            if results:
                with open(filename, mode='a', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    for train in results:
                        row = {
                            "count": count,
                            "train_code": train.get('车次'),
                            "departure_station": train.get('出发站'),
                            "destination_station": train.get('到达站'),
                            "depart_time": train.get('出发时间'),
                            "arrive_time": train.get('到达时间'),
                            "during_time": train.get('历时'),
                            "business_class": train['余票'].get('商务座'),
                            "special_class": train['余票'].get('特等座'),
                            "first_class": train['余票'].get('一等座'),
                            "second_class": train['余票'].get('二等座'),
                            "soft_sleeper": train['余票'].get('软卧'),
                            "hard_sleeper": train['余票'].get('硬卧'),
                            "hard_seat": train['余票'].get('硬座'),
                            "no_seat": train['余票'].get('无座'),
                            "strict_mode": "y" if strict_mode else "n",
                            "hs": train.get('hs')
                        }
                        writer.writerow(row)
                print(f"已保存 {len(results)} 条数据到 {filename}")
            else:
                # 没有数据时，写入一条特殊的空记录，让前端知道查询已完成但无结果
                with open(filename, mode='a', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    row = {
                        "count": count,
                        "train_code": "__NO_DATA__",  # 特殊标记表示无数据
                        "departure_station": "",
                        "destination_station": "",
                        "depart_time": "",
                        "arrive_time": "",
                        "during_time": "",
                        "business_class": "",
                        "special_class": "",
                        "first_class": "",
                        "second_class": "",
                        "soft_sleeper": "",
                        "hard_sleeper": "",
                        "hard_seat": "",
                        "no_seat": "",
                        "strict_mode": "y" if strict_mode else "n",
                        "hs": ""
                    }
                    writer.writerow(row)
                print("未查询到符合条件的车次，已写入空记录标记")

            # Check stop flag during sleep with smaller intervals for quicker response
            sleep_time = random.uniform(interval * 0.7, interval)
            print(f"等待 {sleep_time:.2f} 秒...")
            
            # Split sleep into smaller chunks to check stop flag more frequently
            sleep_chunk = 0.5  # Check every 0.5 seconds
            slept = 0
            while slept < sleep_time:
                if should_stop and should_stop():
                    print(f"\n收到停止信号，停止轮询: {from_station} -> {to_station}")
                    return
                time.sleep(min(sleep_chunk, sleep_time - slept))
                slept += sleep_chunk
            
            count += 1

        except KeyboardInterrupt:
            print("\n用户手动停止轮询")
            break
        except Exception as e:
            print(f"轮询过程发生异常: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(interval)



if __name__ == "__main__":
    FROM_STATION = "东莞东"
    TO_STATION = "赣州"
    DATE = "2026-01-19" 
    IS_STUDENT = False
    IS_HIGH_SPEED = False # 只看高铁动车
    POLLING_INTERVAL = 5 # 秒
    STRICT_MODE = False # 是否开启严格模式(True: 仅匹配指定车站; False: 包含同城车站)

    start_polling_storage(FROM_STATION, TO_STATION, DATE, IS_STUDENT, IS_HIGH_SPEED, POLLING_INTERVAL, STRICT_MODE)