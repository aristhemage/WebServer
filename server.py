import socket
import threading
import os
import datetime

PORT = 8080
SERVER_NAME = "MyCOSC350Server/1.0"
ROOT_DIR = os.getcwd()

def handle_client(client_conn, client_addr):
    # Print all messages to console for verification (Requirement IX)
    print(f"[+] Connection from {client_addr}")
    try:
        while True: # VII. Persistent Connection
            request_data = client_conn.recv(4096).decode('utf-8')
            if not request_data:
                break

            print(f"\n--- Incoming HTTP Request ---\n{request_data}---------------------------")

            # I. Parse Request
            lines = request_data.split("\r\n")
            if not lines[0]: break
            
            parts = lines[0].split(" ")
            if len(parts) < 3: break
            method, path, protocol = parts

            # VI. Directory Traversal Protection
            if ".." in path or "\\" in path:
                send_response(client_conn, "403 Forbidden", "Access Denied.", method=method)
                continue

            # II. Supported HTTP Methods
            if method not in ["GET", "HEAD"]:
                send_response(client_conn, "501 Not Implemented", "Method not supported.", method=method)
                continue

            # I. Locate File
            filename = path.lstrip("/")
            if filename == "": filename = "index.html"
            filepath = os.path.join(ROOT_DIR, filename)

            # V. 404 Not Found
            if not os.path.isfile(filepath):
                send_response(client_conn, "404 Not Found", "File not found.", method=method)
                continue

            # III. Conditional GET
            file_mtime = os.path.getmtime(filepath)
            last_mod_dt = datetime.datetime.fromtimestamp(file_mtime, tz=datetime.timezone.utc)
            last_mod_str = last_mod_dt.strftime('%a, %d %b %Y %H:%M:%S GMT')

            if_mod_since = None
            for line in lines:
                if line.lower().startswith("if-modified-since:"):
                    if_mod_since = line.split(": ", 1)[1]

            if if_mod_since:
                try:
                    ims_date = datetime.datetime.strptime(if_mod_since, '%a, %d %b %Y %H:%M:%S GMT').replace(tzinfo=datetime.timezone.utc)
                    if last_mod_dt <= ims_date:
                        # 304 Not Modified: Headers only, Content-Length 0 (Section IV)
                        send_response(client_conn, "304 Not Modified", "", method=method, headers={"Last-Modified": last_mod_str})
                        continue
                except ValueError:
                    pass

            # IV. 200 OK Response
            with open(filepath, "rb") as f:
                content = f.read()
            
            # Last-Modified only for 200 OK (Section IV)
            send_response(client_conn, "200 OK", content, is_binary=True, method=method, headers={"Last-Modified": last_mod_str})

            # VII. Proper Handling of Connection: close
            if "Connection: close" in request_data:
                break

    except Exception as e:
        print(f"Error handling {client_addr}: {e}")
    finally:
        client_conn.close()
        print(f"[-] Connection closed for {client_addr}")

def send_response(sock, status, body, is_binary=False, method="GET", headers=None):
    curr_date = datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # IV. Content-Length must be 0 for HEAD or 304 (Requirement IV)
    if status == "304 Not Modified" or method == "HEAD":
        content_length = 0
    else:
        content_length = len(body) if body else 0
    
    resp_headers = [
        f"HTTP/1.1 {status}",
        f"Date: {curr_date}",
        f"Server: {SERVER_NAME}",
        f"Content-Length: {content_length}",
        "Connection: keep-alive"
    ]
    
    if headers:
        for k, v in headers.items():
            resp_headers.append(f"{k}: {v}")
    
    header_str = "\r\n".join(resp_headers) + "\r\n\r\n"
    
    # Print response to console (Requirement IX)
    print(f"\n--- Outgoing HTTP Response ---\n{header_str}----------------------------")
    
    sock.sendall(header_str.encode('utf-8'))
    
    # II & III. Only send body if method is GET and it's not a 304 response
    if method == "GET" and status != "304 Not Modified" and body:
        if is_binary:
            sock.sendall(body)
        else:
            sock.sendall(body.encode('utf-8'))

def start_server():
    # VIII. Concurrency Support (Multi-threading)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("", PORT))
    server.listen(10)
    print(f"[*] Server running on port {PORT}...")

    while True:
        client_sock, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_sock, addr))
        thread.start()

if __name__ == "__main__":
    start_server()