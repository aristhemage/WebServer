import socket
import time

def run_test():
    host = '127.0.0.1'
    port = 8080
    
    try:
        # Create a single TCP socket for multiple requests (Requirement VII)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((host, port))
        
        # 1. Standard GET Request
        print("\n--- TEST 1: Standard GET ---")
        request1 = "GET /index.html HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: keep-alive\r\n\r\n"
        client.sendall(request1.encode())
        print(client.recv(4096).decode())

        time.sleep(1)

        # 2. HEAD Request (No body should be returned)
        print("\n--- TEST 2: HEAD Request ---")
        request2 = "HEAD /index.html HTTP/1.1\r\nHost: 127.0.0.1\r\nConnection: keep-alive\r\n\r\n"
        client.sendall(request2.encode())
        print(client.recv(4096).decode())

        time.sleep(1)

        # 3. Conditional GET (304 Not Modified)
        print("\n--- TEST 3: Conditional GET (304) ---")
        # Requesting a future date to trigger 304
        future_date = "Wed, 01 Jan 2030 00:00:00 GMT"
        request3 = (f"GET /index.html HTTP/1.1\r\n"
                    f"Host: 127.0.0.1\r\n"
                    f"If-Modified-Since: {future_date}\r\n"
                    f"Connection: close\r\n\r\n")
        client.sendall(request3.encode())
        
        # Final response should show 304 with Content-Length: 0
        print(client.recv(4096).decode())
        
        client.close()

    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    run_test()