import requests
import json

BASE_URL = 'http://127.0.0.1:8000/api'
LOGIN_URL = f"{BASE_URL}/users/login/"
ZONE_URL = f"{BASE_URL}/zones/"

def login(username, password):
    resp = requests.post(LOGIN_URL, json={'username': username, 'password': password})
    resp.raise_for_status()
    return resp.json()['access']

def print_result(method, url, status, data=None):
    print(f"{method} {url} -> {status}")
    if data is not None:
        print(json.dumps(data, indent=2))

def main():
    token = login('api_test_user', 'Test@12345')
    headers = {'Authorization': f'Bearer {token}'}

    # List zones (expected empty initially)
    r = requests.get(ZONE_URL, headers=headers)
    print_result('GET', ZONE_URL, r.status_code, r.json() if r.ok else None)

    # Use an existing warehouse ID for creation
    warehouse_id = '5aaebf44-bfd1-4a68-80e4-e7d44c5174a3'  # adjust if needed

    # Create a zone
    payload = {
        "warehouse": warehouse_id,
        "zone_name": "Test Zone",
        "zone_type": "Storage",
        "x": "0.0",
        "y": "0.0",
        "z": "0.0",
        "width": "10.0",
        "height": "5.0",
        "depth": "3.0"
    }
    r = requests.post(ZONE_URL, headers=headers, json=payload)
    print_result('POST', ZONE_URL, r.status_code, r.json() if r.ok else None)
    if not r.ok:
        return
    zone_id = r.json().get('id')
    detail_url = f"{ZONE_URL}{zone_id}/"

    # Retrieve zone
    r = requests.get(detail_url, headers=headers)
    print_result('GET', detail_url, r.status_code, r.json() if r.ok else None)

    # Full update (PUT)
    update_payload = {
        "warehouse": warehouse_id,
        "zone_name": "Updated Zone",
        "zone_type": "Picking",
        "x": "1.0",
        "y": "1.0",
        "z": "1.0",
        "width": "12.0",
        "height": "6.0",
        "depth": "4.0"
    }
    r = requests.put(detail_url, headers=headers, json=update_payload)
    print_result('PUT', detail_url, r.status_code, r.json() if r.ok else None)

    # Partial update (PATCH)
    patch_payload = {"zone_name": "Patched Zone"}
    r = requests.patch(detail_url, headers=headers, json=patch_payload)
    print_result('PATCH', detail_url, r.status_code, r.json() if r.ok else None)

    # Delete zone
    r = requests.delete(detail_url, headers=headers)
    print_result('DELETE', detail_url, r.status_code)

if __name__ == '__main__':
    main()
