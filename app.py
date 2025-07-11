from flask import Flask, jsonify
import csv
import requests
import os

app = Flask(__name__)

# KeyValue service configuration
APP_KEY = "x16ll6hh"
KV_KEY = "mykey"
KV_BASE_URL = "https://keyvalue.immanuel.co/api/KeyVal"

def get_current_index():
    """Get the current index from KeyValue service"""
    url = f"{KV_BASE_URL}/GetValue/{APP_KEY}/{KV_KEY}"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return int(response.text.strip('"')) if response.text.strip('"') else 0
        return 0
    except:
        return 0

def update_index(new_index):
    """Update the index in KeyValue service"""
    url = f"{KV_BASE_URL}/UpdateValue/{APP_KEY}/{KV_KEY}/{new_index}"
    try:
        response = requests.post(url, timeout=5)
        return response.status_code == 200
    except:
        return False

def get_next_api_key():
    """Retrieve API keys from Google Sheet with index tracking"""
    sheet_url = "https://docs.google.com/spreadsheets/d/1LJIQnjwfv9Quy_suS4B-aUAfoq5p3NasgK6mO1lCA_A/export?format=csv"
    try:
        last_index = get_current_index()
        response = requests.get(sheet_url, timeout=10)
        response.raise_for_status()
        
        keys = []
        for row in csv.reader(response.text.splitlines()):
            if row and row[0].strip().startswith('sk-or-v1-'):
                keys.append(row[0].strip())
        
        if not keys:
            return {'status': 'error', 'message': 'No valid keys found'}
        
        next_index = (last_index + 1) % len(keys)
        update_index(next_index)
        
        return {
            'status': 'success',
            'api_key': keys[next_index],
            'current_index': next_index,
            'total_keys': len(keys)
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@app.route("/")
def index():
    result = get_next_api_key()
    return jsonify(result)

def create_app():
    return app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
