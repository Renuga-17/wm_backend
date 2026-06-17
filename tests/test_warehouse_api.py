import requests
import json

BASE_URL = 'http://127.0.0.1:8000/api'
LOGIN_URL = f"{BASE_URL}/users/login/"
WAREHOUSE_URL = f"{BASE_URL}/warehouses/"

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

    # List warehouses
    r = requests.get(WAREHOUSE_URL, headers=headers)
    print_result('GET', WAREHOUSE_URL, r.status_code, r.json() if r.ok else None)

    # Create warehouse (adjust fields as per model, using placeholder fields)
    payload = {
        "name": "Test Warehouse",
        "location": "Test Location"
    }
    r = requests.post(WAREHOUSE_URL, headers=headers, json=payload)
    print_result('POST', WAREHOUSE_URL, r.status_code, r.json() if r.ok else None)
    if not r.ok:
        return
    wh_id = r.json().get('id')
    detail_url = f"{WAREHOUSE_URL}{wh_id}/"

    # Retrieve warehouse
    r = requests.get(detail_url, headers=headers)
    print_result('GET', detail_url, r.status_code, r.json() if r.ok else None)

    # Update warehouse (PUT)
    update_payload = {"name": "Updated Warehouse", "location": "Updated Location"}
    r = requests.put(detail_url, headers=headers, json=update_payload)
    print_result('PUT', detail_url, r.status_code, r.json() if r.ok else None)

    # Partial update (PATCH)
    patch_payload = {"name": "Patched Warehouse"}
    r = requests.patch(detail_url, headers=headers, json=patch_payload)
    print_result('PATCH', detail_url, r.status_code, r.json() if r.ok else None)

    # Delete warehouse
    r = requests.delete(detail_url, headers=headers)
    print_result('DELETE', detail_url, r.status_code)

if __name__ == '__main__':
    main()
