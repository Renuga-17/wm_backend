import requests, json, sys

BASE_URL = 'http://127.0.0.1:8000/api/warehouses/'

def print_resp(label, resp):
    print(f'=== {label} ===')
    print('Status:', resp.status_code)
    try:
        print('JSON:', resp.json())
    except Exception:
        print('Text:', resp.text)

# 1. GET list
resp = requests.get(BASE_URL)
print_resp('GET list', resp)

# 2. POST create
payload = {
    "name": "Test Warehouse",
    "location": "Test Location",
    "total_area_sqft": 1000.0
}
resp = requests.post(BASE_URL, json=payload)
print_resp('POST create', resp)
if resp.status_code != 201:
    sys.exit(0)
wid = resp.json().get('id')
if not wid:
    sys.exit(0)
# 3. GET detail
resp = requests.get(f'{BASE_URL}{wid}/')
print_resp('GET detail', resp)
# 4. PUT update (full)
payload_put = {
    "name": "Updated Warehouse",
    "location": "Updated Location",
    "total_area_sqft": 2000.0
}
resp = requests.put(f'{BASE_URL}{wid}/', json=payload_put)
print_resp('PUT update', resp)
# 5. PATCH update (partial)
payload_patch = {
    "location": "Patched Location"
}
resp = requests.patch(f'{BASE_URL}{wid}/', json=payload_patch)
print_resp('PATCH update', resp)
# 6. DELETE
resp = requests.delete(f'{BASE_URL}{wid}/')
print_resp('DELETE', resp)
