import sys
import time
import json
import urllib.request
import urllib.error

def make_request(url, method='GET', data=None):
    req = urllib.request.Request(url, method=method)
    if data:
        json_data = json.dumps(data).encode('utf-8')
        req.add_header('Content-Type', 'application/json')
        req.data = json_data
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            body = response.read().decode('utf-8')
            return response.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return None, str(e)

def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    print(f"=== Testing Flask MongoDB Application at {base_url} ===\n")

    # 1. Test Root Endpoint (GET /)
    print("1. Testing Root Endpoint: GET /")
    status, body = make_request(f"{base_url}/")
    print(f"   Status: {status}")
    print(f"   Response: {body.strip()}\n")
    assert status == 200, f"Expected 200, got {status}"

    # 2. Test Health Endpoint (GET /health)
    print("2. Testing Health Endpoint: GET /health")
    status, body = make_request(f"{base_url}/health")
    print(f"   Status: {status}")
    print(f"   Response: {body.strip()}\n")

    # 3. Test Insert Data (POST /data)
    test_doc = {
        "item": "Kubernetes Cluster Node",
        "timestamp": time.time(),
        "status": "active",
        "environment": "Production Kubernetes"
    }
    print(f"3. Testing Insert Data: POST /data with payload {json.dumps(test_doc)}")
    status, body = make_request(f"{base_url}/data", method='POST', data=test_doc)
    print(f"   Status: {status}")
    print(f"   Response: {body.strip()}\n")
    assert status == 201, f"Expected 201, got {status}"

    # 4. Test Retrieve Data (GET /data)
    print("4. Testing Retrieve Data: GET /data")
    status, body = make_request(f"{base_url}/data")
    print(f"   Status: {status}")
    print(f"   Response: {body.strip()}\n")
    assert status == 200, f"Expected 200, got {status}"

    print("SUCCESS: All endpoint tests passed successfully!")

if __name__ == '__main__':
    main()

