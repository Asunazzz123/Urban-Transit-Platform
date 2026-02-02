from flask import Flask, jsonify, request, Response, stream_with_context
import pandas as pd
import time
import json
import os
import threading
from flask_cors import CORS
from operator import itemgetter
from utils.data import AskData
from crawler.ticket_crawler import TicketCrawler, start_polling_storage
from utils.constant import RESOURCE_DIR

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Accept", "Cache-Control"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": True
    }
})
mode = "run"


crawler_tasks = {}
crawler_stop_flags = {}

def switch_mode(mode = "run"):
    if mode == "test":
        app.config["PROPAGATE_EXCEPTIONS"] = True
        app.config["DEBUG"] = True
        return 0
    elif mode == "run":
        return 1
    else:
        return -1


@app.route("/api/receive", methods=["GET"])
def push_info():
    try:
        date_param = request.args.get("date")
        dep_param = request.args.get("departure")
        dest_param = request.args.get("destination")

        if not date_param: 
             return jsonify({"error": "Missing params"}), 400

        item = AskData(
            date=date_param,
            departure=dep_param,
            destination=dest_param,
            highSpeed=request.args.get("highSpeed") == 'true',
            studentTicket=request.args.get("studentTicket") == 'true',
            askTime=int(request.args.get("askTime", 10)),
            strictmode=request.args.get("strictmode") == 'true'
        )

        # Start crawler if not running
        task_key = (item.departure, item.destination, item.date, item.studentTicket, item.highSpeed, item.strictmode)
        
        # Initialize stop flag
        crawler_stop_flags[task_key] = False
        
        if task_key not in crawler_tasks or not crawler_tasks[task_key].is_alive():
             print(f"Starting crawler for {task_key} with interval {item.askTime}s")
             t = threading.Thread(
                 target=start_polling_storage,
                 args=(item.departure, item.destination, item.date, item.studentTicket, item.highSpeed, item.askTime, item.strictmode, lambda: crawler_stop_flags.get(task_key, False)),
                 daemon=True
             )
             t.start()
             crawler_tasks[task_key] = t
        else:
             print(f"Crawler already running for {task_key}. Ignoring new askTime {item.askTime}s if different.")
        
        csv_dir = RESOURCE_DIR / "csv"
        
        def generate():
            count = 1
            filename = csv_dir / f"train_data_{item.date}_{item.departure}_{item.destination}.csv"
            last_sent_count = 0
            wait_count = 0
            max_wait = 60  # Maximum wait time in seconds for file to appear
            
            # Wait for file to exist with timeout
            while not os.path.exists(filename):
                wait_count += 1
                if wait_count > max_wait:
                    yield f"data: {{\"error\": \"Timeout waiting for crawler to start\"}}\n\n"
                    return
                # Send heartbeat comment to keep connection alive
                yield ": heartbeat\n\n"
                time.sleep(1)
            
            print(f"SSE: File found at {filename}")

            # Initialize count to 1, we will read from the beginning
            count = 1
                
            while True:
                try:
                    if not os.path.exists(filename):
                         yield ": waiting\n\n"
                         time.sleep(item.askTime)
                         continue

                    df = pd.read_csv(filename)
                    if "count" in df.columns and not df.empty:
                        max_count = int(df["count"].max())
                        
                        # Send all new data since last sent
                        if max_count >= count:
                            data = df[df["count"] == count]
                            
                            if not data.empty:
                                # Check if this is a "no data" marker
                                if len(data) == 1 and data.iloc[0].get('train_code') == '__NO_DATA__':
                                    # No trains found, send special marker to frontend
                                    print(f"SSE: No trains found for count={count}, sending __NO_DATA__ marker")
                                    yield f'data: {{"__NO_DATA__": true}}\n\n'
                                    count += 1
                                    continue
                                
                                # Convert to dict and handle NaN - replace NaN with None for valid JSON
                                result = data.fillna('').to_dict(orient='records')
                                # Replace empty strings with None for cleaner JSON
                                for row in result:
                                    for key, value in row.items():
                                        if value == '' or (isinstance(value, float) and pd.isna(value)):
                                            row[key] = None
                                
                                json_str = json.dumps(result, ensure_ascii=False)
                                sse_message = f"data: {json_str}\n\n"
                                print(f"SSE: Sending {len(result)} records for count={count}")
                                yield sse_message
                                last_sent_count = count
                                count += 1
                                continue  # Check if more data is available immediately
                        
                        # No new data yet, send heartbeat
                        yield ": heartbeat\n\n"
                    else:
                        # File exists but no valid data yet
                        yield ": waiting for data\n\n"
                    
                except pd.errors.EmptyDataError:
                    print("SSE: CSV file is empty, waiting...")
                    yield ": empty file\n\n"
                except Exception as e:
                    print(f"SSE Error reading CSV: {e}")
                    yield ": error\n\n"
                
                time.sleep(item.askTime)

        response = Response(
            stream_with_context(generate()), 
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
                'Content-Type': 'text/event-stream; charset=utf-8'
            }
        )
        return response

    except Exception as e:
        if switch_mode(mode) == 0:
            print("ERROR in /api/receive:", e)
            raise
        else:
            return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/receive_by_code", methods=["GET"])
def push_info_by_code():
    try:
        date_param = request.args.get("date")
        dep_param = request.args.get("departure")
        dest_param = request.args.get("destination")
        train_code_param = request.args.get("trainCode")

        if not date_param or not train_code_param: 
            return jsonify({"error": "Missing params"}), 400

        item = AskData(
            date=date_param,
            departure=dep_param,
            destination=dest_param,
            highSpeed=False,
            studentTicket=request.args.get("studentTicket") == 'true',
            askTime=int(request.args.get("askTime", 10)),
            strictmode=False
        )

        task_key = (item.departure, item.destination, item.date, item.studentTicket, item.highSpeed, item.strictmode)
        
        crawler_stop_flags[task_key] = False
        
        if task_key not in crawler_tasks or not crawler_tasks[task_key].is_alive():
            print(f"Starting crawler for {task_key} with interval {item.askTime}s (Train Code Mode)")
            t = threading.Thread(
                target=start_polling_storage,
                args=(item.departure, item.destination, item.date, item.studentTicket, item.highSpeed, item.askTime, item.strictmode, lambda: crawler_stop_flags.get(task_key, False)),
                daemon=True
            )
            t.start()
            crawler_tasks[task_key] = t
        else:
            print(f"Crawler already running for {task_key}. Reusing for Train Code Search.")
        
        csv_dir = RESOURCE_DIR / "csv"
        
        def generate():
            count = 1
            filename = csv_dir / f"train_data_{item.date}_{item.departure}_{item.destination}.csv"
            last_sent_count = 0
            wait_count = 0
            max_wait = 60
            
            while not os.path.exists(filename):
                wait_count += 1
                if wait_count > max_wait:
                    yield f"data: {{\"error\": \"Timeout waiting for crawler to start\"}}\n\n"
                    return
                yield ": heartbeat\n\n"
                time.sleep(1)
            
            print(f"SSE (TrainCode): File found at {filename}")

            count = 1
                
            while True:
                try:
                    if not os.path.exists(filename):
                        yield ": waiting\n\n"
                        time.sleep(item.askTime)
                        continue

                    df = pd.read_csv(filename)
                    if "count" in df.columns and not df.empty:
                        max_count = int(df["count"].max())
                        
                        if max_count >= count:
                            data = df[df["count"] == count]
                            
                            if not data.empty:
                                if len(data) == 1 and data.iloc[0].get('train_code') == '__NO_DATA__':
                                    print(f"SSE (TrainCode): No trains found for count={count}, sending __NO_DATA__ marker")
                                    yield f'data: {{"__NO_DATA__": true}}\n\n'
                                else:
                                    filtered_data = data[data['train_code'] == train_code_param]
                                    
                                    result = filtered_data.fillna('').to_dict(orient='records')
                                    for row in result:
                                        for key, value in row.items():
                                            if value == '' or (isinstance(value, float) and pd.isna(value)):
                                                row[key] = None
                                    
                                    json_str = json.dumps(result, ensure_ascii=False)
                                    sse_message = f"data: {json_str}\n\n"
                                    print(f"SSE (TrainCode): Sending {len(result)} records for count={count} (Train Code: {train_code_param})")
                                    yield sse_message
                                
                                count += 1
                                continue
                        
                        yield ": heartbeat\n\n"
                    else:
                        yield ": waiting for data\n\n"
                    
                except pd.errors.EmptyDataError:
                    print("SSE (TrainCode): CSV file is empty, waiting...")
                    yield ": empty file\n\n"
                except Exception as e:
                    print(f"SSE (TrainCode) Error reading CSV: {e}")
                    yield ": error\n\n"
                
                time.sleep(item.askTime)

        return Response(stream_with_context(generate()), mimetype='text/event-stream', headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Content-Type': 'text/event-stream; charset=utf-8'})

    except Exception as e:
        if switch_mode(mode) == 0:
            print("ERROR in /api/receive_by_code:", e)
            raise
        else:
            return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/stop_train_code", methods=["POST"])
def stop_crawler_by_code():
    try:
        data = request.get_json()
        departure = data.get("departure")
        destination = data.get("destination")
        date = data.get("date")
        student = data.get("studentTicket", False)
        high_speed = False
        strictmode = False
        
        task_key = (departure, destination, date, student, high_speed, strictmode)
        
        if task_key in crawler_stop_flags:
            crawler_stop_flags[task_key] = True
            return jsonify({"status": "success", "message": "Stop signal sent"}), 200
        return jsonify({"status": "warning", "message": "Crawler not found"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route("/api/stop", methods=["POST"])
def stop_crawler():
    """Stop a running crawler"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Missing request body"}), 400
        
        departure = data.get("departure")
        destination = data.get("destination")
        date = data.get("date")
        student = data.get("studentTicket", False)
        high_speed = data.get("highSpeed", False)
        strictmode = data.get("strictmode", False)
        
        task_key = (departure, destination, date, student, high_speed, strictmode)
        
        if task_key in crawler_stop_flags:
            crawler_stop_flags[task_key] = True
            print(f"Stop signal sent for crawler: {task_key}")
            return jsonify({"status": "success", "message": "Stop signal sent"}), 200
        else:
            # Try to find a matching crawler with partial key match
            for key in crawler_stop_flags.keys():
                if key[0] == departure and key[1] == destination and key[2] == date:
                    crawler_stop_flags[key] = True
                    print(f"Stop signal sent for crawler (partial match): {key}")
                    return jsonify({"status": "success", "message": "Stop signal sent"}), 200
            
            return jsonify({"status": "warning", "message": "Crawler not found"}), 200
    except Exception as e:
        print(f"Error stopping crawler: {e}")
        return jsonify({"status": "error", "message": str(e)}), 400


def get_info():
    try:
        data = request.get_json()
        if data:
            return AskData(**data)
    except:
        pass
    return None

def load_crawler():
    try:
        data = request.get_json()
        item = AskData(**data)
        param_dict = item.model_dump()
        Departure, Destination, Date, HighSpeed, StudentTicket, AskTime, strictmode = itemgetter(
            "departure", "destination", "date", "highSpeed", "studentTicket", "askTime", "strictmode"
        )(param_dict)
        start_polling_storage(Departure, Destination, Date, StudentTicket, HighSpeed, AskTime, strictmode)
        return jsonify({"status": "success", "message": "Crawler started"}), 200
    except Exception as e:
        if switch_mode(mode) == 0:
            raise
        return jsonify({"status": "error", "message": str(e)}), 400


if __name__ == "__main__":
    app.run(host="localhost", port=5001, threaded=True)
