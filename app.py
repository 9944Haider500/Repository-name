import csv
import requests

# KeyValue service configuration
APP_KEY = "x16ll6hh"
KV_KEY = "mykey"
KV_BASE_URL = "https://keyvalue.immanuel.co/api/KeyVal"

def get_current_index():
    """Get the current index from KeyValue service"""
    url = f"{KV_BASE_URL}/GetValue/{APP_KEY}/{KV_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return int(response.text.strip('"')) if response.text.strip('"') else 0
        return 0
    except:
        return 0

def update_index(new_index):
    """Update the index in KeyValue service"""
    url = f"{KV_BASE_URL}/UpdateValue/{APP_KEY}/{KV_KEY}/{new_index}"
    try:
        response = requests.post(url)
        return response.status_code == 200
    except:
        return False

def get_next_api_key():
    """
    Retrieve API keys with persistent index tracking using KeyValue service
    """
    sheet_url = "https://docs.google.com/spreadsheets/d/1LJIQnjwfv9Quy_suS4B-aUAfoq5p3NasgK6mO1lCA_A/export?format=csv"
    
    try:
        # Get current index from KeyValue service
        last_index = get_current_index()
        
        # Fetch keys from Google Sheets
        response = requests.get(sheet_url)
        response.raise_for_status()
        
        keys = []
        for row in csv.reader(response.text.splitlines()):
            if row and row[0].strip().startswith('sk-or-v1-'):
                keys.append(row[0].strip())
        
        if not keys:
            return {'status': 'error', 'message': 'No valid keys found'}

        # Calculate next index
        next_index = (last_index + 1) % len(keys)
        
        # Update the index in KeyValue service
        if not update_index(next_index):
            print("Warning: Failed to update index in KeyValue service")
        
        return {
            'status': 'success',
            'api_key': keys[next_index],
            'current_index': next_index,
            'total_keys': len(keys)
        }

    except Exception as e:
        return {'status': 'error', 'message': str(e)}

if __name__ == "__main__":
    result = get_next_api_key()
    
    if result['status'] == 'success':
        print("✅ Success:")
        print(f"API Key: {result['api_key']}")
        print(f"Current Index: {result['current_index']}")
        print(f"Total Keys: {result['total_keys']}")
    else:
        print("❌ Error:", result['message'])
