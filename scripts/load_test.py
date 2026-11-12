import sys
import time
import json
import threading
import urllib.request
import urllib.error

stop_flag = False
request_count = 0
success_count = 0
error_count = 0
counter_lock = threading.Lock()

def worker(base_url, thread_id):
    global request_count, success_count, error_count
    payload = {"worker": f"thread-{thread_id}", "metric": "load-test-sample"}
    data = json.dumps(payload).encode('utf-8')

    while not stop_flag:
        try:
            # Alternating between POST and GET to generate CPU and DB load
            req_post = urllib.request.Request(f"{base_url}/data", data=data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req_post, timeout=5) as resp:
                if resp.status == 201:
                    with counter_lock:
                        success_count += 1

            req_get = urllib.request.Request(f"{base_url}/data")
            with urllib.request.urlopen(req_get, timeout=5) as resp:
                if resp.status == 200:
                    with counter_lock:
                        success_count += 1
        except Exception:
            with counter_lock:
                error_count += 1
        finally:
            with counter_lock:
                request_count += 2

def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    concurrency = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    print(f"=== Starting High-Traffic Load Simulation ===")
    print(f"Target URL:        {base_url}")
    print(f"Concurrency Level: {concurrency} threads")
    print(f"Duration:          {duration} seconds\n")
    print("Monitor HPA in another terminal using:")
    print("  kubectl get hpa -n flask-mongo-app -w")
    print("  kubectl get pods -n flask-mongo-app -l app=flask-app -w\n")

    threads = []
    global stop_flag
    for i in range(concurrency):
        t = threading.Thread(target=worker, args=(base_url, i))
        t.daemon = True
        threads.append(t)
        t.start()

    start_time = time.time()
    try:
        while time.time() - start_time < duration:
            elapsed = int(time.time() - start_time)
            print(f"[{elapsed}s / {duration}s] Requests: {request_count} | Success: {success_count} | Errors: {error_count}")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nStopping load test early...")

    stop_flag = True
    for t in threads:
        t.join(timeout=2)

    total_time = time.time() - start_time
    rps = request_count / total_time if total_time > 0 else 0
    print("\n=== Load Test Finished ===")
    print(f"Total Time:      {total_time:.2f} seconds")
    print(f"Total Requests:  {request_count}")
    print(f"Successful:      {success_count}")
    print(f"Errors:          {error_count}")
    print(f"Throughput:      {rps:.2f} req/sec")

if __name__ == '__main__':
    main()

