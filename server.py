#print("Hello world")
import socket

def start_server(host='127.0.0.1', port=8080):
    """Start a simple HTTP server."""
    try:
        # Create TCP socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"Server running on http://{host}:{port}")

        while True:
            client_conn, client_addr = server_socket.accept()
            print(f"Connection from {client_addr}")

            # Receive request
            request = client_conn.recv(1024).decode('utf-8')
            print("Request received:\n", request)

            # Simple HTTP response
            response_body = "<html><body><h1>Hello from Python Server!</h1></body></html>"
            response = (
                "HTTP/1.1 200 OK\r\n"
                f"Content-Length: {len(response_body)}\r\n"
                "Content-Type: text/html\r\n"
                "Connection: close\r\n"
                "\r\n"
                f"{response_body}"
            )

            client_conn.sendall(response.encode('utf-8'))
            client_conn.close()

    except KeyboardInterrupt:
        print("\nServer shutting down...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()
