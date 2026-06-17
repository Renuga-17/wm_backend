import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def main():
    print("==================================================")
    print("      WMS API MANUAL CLIENT TEST SYSTEM           ")
    print("==================================================")
    
    # 1. Login to retrieve simple-jwt access token
    login_url = f"{BASE_URL}/api/users/login/"
    payload = {
        "username": "api_test_user",
        "password": "Test@12345"
    }
    
    print(f"\n1. Requesting JWT Token from: {login_url}")
    try:
        response = requests.post(login_url, json=payload)
        if response.status_code != 200:
            print(f"Failed to log in: {response.status_code} - {response.text}")
            return
        
        tokens = response.json()
        access_token = tokens["access"]
        print("Login Success!")
        print(f"Access Token (truncated): {access_token[:50]}...")
    except Exception as e:
        print(f"Error connecting to server: {e}. Make sure runserver is running!")
        return

    # 2. Setup auth header
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # 3. Fetch list of Warehouses
    warehouses_url = f"{BASE_URL}/api/warehouses/"
    print(f"\n2. Querying Warehouses Endpoint: {warehouses_url}")
    res = requests.get(warehouses_url, headers=headers)
    print(f"Status Code: {res.status_code}")
    print("Warehouses Response:")
    print(json.dumps(res.json(), indent=2))

    # 4. Fetch list of Zones
    zones_url = f"{BASE_URL}/api/zones/"
    print(f"\n3. Querying Zones Endpoint: {zones_url}")
    res_zones = requests.get(zones_url, headers=headers)
    print(f"Status Code: {res_zones.status_code}")
    
    zones_data = res_zones.json()
    # If list, print count and first few
    if isinstance(zones_data, list):
        print(f"Found {len(zones_data)} Zones.")
        if len(zones_data) > 0:
            print("First Zone Sample:")
            print(json.dumps(zones_data[0], indent=2))
    elif isinstance(zones_data, dict) and "results" in zones_data:
        # Standard paginated DRF response
        results = zones_data["results"]
        print(f"Found {zones_data.get('count', len(results))} Zones (Paginated).")
        if len(results) > 0:
            print("First Zone Sample:")
            print(json.dumps(results[0], indent=2))
    else:
        print(json.dumps(zones_data, indent=2))

if __name__ == "__main__":
    main()
