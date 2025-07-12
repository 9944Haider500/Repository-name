from flask import Flask, jsonify
import csv
import requests
import os
import time

# Initialize Flask app
app = Flask(__name__)

# Service configuration
SERVICE_CONFIG = {
    "APP_KEY": "x16ll6hh",
    "KV_KEY": "mykey",
    "KV_BASE_URL": "https://keyvalue.immanuel.co/api/KeyVal",
    "SHEET_URL": "https://docs.google.com/spreadsheets/d/1LJIQnjwfv9Quy_suS4B-aUAfoq5p3NasgK6mO1lCA_A/export?format=csv"
}

class KeyRotator:
    @staticmethod
    def get_current_index():
        """Get current index from KeyValue service"""
        url = f"{SERVICE_CONFIG['KV_BASE_URL']}/GetValue/{SERVICE_CONFIG['APP_KEY']}/{SERVICE_CONFIG['KV_KEY']}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return int(response.text.strip('"')) if response.text.strip('"') else 0
            return 0
        except Exception as e:
            app.logger.error(f"Error getting current index: {e}")
            return 0

    @staticmethod
    def update_index(new_index):
        """Update index in KeyValue service"""
        url = f"{SERVICE_CONFIG['KV_BASE_URL']}/UpdateValue/{SERVICE_CONFIG['APP_KEY']}/{SERVICE_CONFIG['KV_KEY']}/{new_index}"
        try:
            response = requests.post(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            app.logger.error(f"Error updating index: {e}")
            return False

    @staticmethod
    def fetch_api_keys():
        """Fetch API keys from Google Sheet"""
        try:
            response = requests.get(SERVICE_CONFIG['SHEET_URL'], timeout=10)
            response.raise_for_status()
            return [row[0].strip() for row in csv.reader(response.text.splitlines()) 
                   if row and row[0].strip().startswith('sk-or-v1-')]
        except Exception as e:
            app.logger.error(f"Error fetching API keys: {e}")
            return []

@app.route("/")
def api_key_rotation():
    """Main endpoint for key rotation"""
    try:
        keys = KeyRotator.fetch_api_keys()
        if not keys:
            return jsonify({
                "status": "error",
                "message": "No valid API keys found in the sheet",
                "timestamp": int(time.time())
            }), 500
        
        current_index = KeyRotator.get_current_index()
        next_index = (current_index + 1) % len(keys)
        
        if not KeyRotator.update_index(next_index):
            app.logger.warning("Failed to update index in KeyValue service")
        
        return jsonify({
            "status": "success",
            "api_key": keys[next_index],
            "current_index": next_index,
            "total_keys": len(keys),
            "timestamp": int(time.time())
        })
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": int(time.time())
        }), 500

@app.route("/health")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": int(time.time())
    })

def create_app():
    """Application factory for deployment"""
    return app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
