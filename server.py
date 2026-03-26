import socket
import threading
import os
import datetime

# The port is like a "door number" on the computer.
# Web browsers will connect to this port to talk to our server.
PORT = 8080

# A name for our server that will be sent to browsers in the HTTP response.
SERVER_NAME = "MyCOSC350Server/1.0"

# The folder where the server will look for files to send to users.
# For example: index.html, images, etc.
ROOT_DIR = os.getcwd()


def handle_client(client_conn, client_addr):
    """
    This function runs every time a user connects to the server.

    When someone opens a browser and goes to our server, a connection
    is created between the browser and our program. This function
    handles everything that happens during that connection.
    """

    # Requirement IX
    # Print who connected to the server (for debugging and verification)
    print(f"[+] Connection from {client_addr}")

    try:
        # Requirement VII
        # A single connection can send multiple requests.
        # This loop allows the connection to stay open and handle them.
        while True:

            # Receive data sent from the browser.
            # This will contain the HTTP request (like GET /index.html)
            request_data = client_conn.recv(4096).decode('utf-8')

            # If the browser sends nothing, the connection is closed.
            if not request_data:
                break

            # Requirement IX
            # Print the request so we can see exactly what the browser sent.
            print(f"\n--- Incoming HTTP Request ---\n{request_data}---------------------------")

            # Determine connection status for the response headers
            conn_status = "close" if "Connection: close" in request_data else "keep-alive"

            # Requirement I
            # Split the request into individual lines.
            # HTTP requests are separated by line breaks.
            lines = request_data.split("\r\n")

            # The first line is the "request line"
            # Example: GET /index.html HTTP/1.1
            if not lines[0]:
                break

            parts = lines[0].split(" ")

            # The request line should contain three things:
            # method, path, and protocol
            if len(parts) < 3:
                break

            method, path, protocol = parts

            # Requirement VI
            # Security protection:
            # Prevent someone from accessing files outside the server folder.
            # Example attack: ../../passwords.txt
            if ".." in path or "\\" in path:
                send_response(client_conn, "403 Forbidden", "Access Denied.", method=method, connection_status=conn_status)
                continue

            # Requirement II
            # Our server only understands GET and HEAD requests.
            # If the browser sends something else (POST, PUT, etc),
            # we return an error.
            if method not in ["GET", "HEAD"]:
                send_response(client_conn, "501 Not Implemented", "Method not supported.", method=method, connection_status=conn_status)
                continue

            # Requirement I
            # Remove the "/" at the start of the URL so we get the filename.
            filename = path.lstrip("/")

            # If the user just requests "/", send index.html by default.
            if filename == "":
                filename = "index.html"

            # Combine the folder path and filename to find the real file.
            filepath = os.path.join(ROOT_DIR, filename)

            # Requirement V
            # If the file does not exist, send a 404 error.
            if not os.path.isfile(filepath):
                send_response(client_conn, "404 Not Found", "File not found.", method=method, connection_status=conn_status)
                continue

            # Requirement III
            # Get the time when the file was last modified.
            file_mtime = os.path.getmtime(filepath)

            # Convert that time to the standard HTTP date format.
            last_mod_dt = datetime.datetime.fromtimestamp(file_mtime, tz=datetime.timezone.utc)
            last_mod_str = last_mod_dt.strftime('%a, %d %b %Y %H:%M:%S GMT')

            # Some browsers ask:
            # "Has this file changed since the last time I downloaded it?"
            # They send this using the If-Modified-Since header.
            if_mod_since = None

            for line in lines:
                if line.lower().startswith("if-modified-since:"):
                    if_mod_since = line.split(": ", 1)[1]

            # If the browser sent that header, compare the dates.
            if if_mod_since:
                try:
                    ims_date = datetime.datetime.strptime(
                        if_mod_since, '%a, %d %b %Y %H:%M:%S GMT'
                    ).replace(tzinfo=datetime.timezone.utc)

                    # If the file has NOT changed, we tell the browser
                    # it can use its cached copy instead of downloading again.
                    if last_mod_dt <= ims_date:
                        # Requirement IV
                        # 304 Not Modified response (Rubric: Last-Modified ONLY for 200 OK)
                        send_response(
                            client_conn,
                            "304 Not Modified",
                            "",
                            method=method,
                            connection_status=conn_status
                        )
                        continue

                except ValueError:
                    # If the date format is wrong, just ignore it.
                    pass

            # Requirement IV
            # If we reach here, we need to send the file normally.

            # Open the file and read its contents
            with open(filepath, "rb") as f:
                content = f.read()

            # Send a successful response (200 OK)
            send_response(
                client_conn,
                "200 OK",
                content,
                is_binary=True,
                method=method,
                headers={"Last-Modified": last_mod_str},
                connection_status=conn_status
            )

            # Requirement VII
            # If the browser specifically asks to close the connection,
            # we end the loop and close it.
            if conn_status == "close":
                break

    except Exception as e:
        print(f"Error handling {client_addr}: {e}")

    finally:
        # Close the connection with the client
        client_conn.close()
        print(f"[-] Connection closed for {client_addr}")


def send_response(sock, status, body, is_binary=False, method="GET", headers=None, connection_status="keep-alive"):
    """
    This function builds and sends an HTTP response back to the browser.

    Every HTTP response has:
    1. A status line (like 200 OK or 404 Not Found)
    2. Several headers with extra information
    3. Optional body content (like the HTML file)
    """

    # Requirement IV
    # Get the current time to include in the response headers
    curr_date = datetime.datetime.now(datetime.timezone.utc).strftime('%a, %d %b %Y %H:%M:%S GMT')

    # Requirement IV
    # Some responses should not contain any body content.
    # HEAD requests and 304 responses must have length 0.
    if status == "304 Not Modified" or method == "HEAD":
        content_length = 0
    else:
        content_length = len(body) if body else 0

    # These are the standard headers sent in the response
    resp_headers = [
        f"HTTP/1.1 {status}",
        f"Date: {curr_date}",
        f"Server: {SERVER_NAME}",
        f"Content-Length: {content_length}",
        f"Connection: {connection_status}"
    ]

    # Add any extra headers if needed (like Last-Modified)
    if headers:
        for k, v in headers.items():
            resp_headers.append(f"{k}: {v}")

    # HTTP requires headers to end with a blank line
    header_str = "\r\n".join(resp_headers) + "\r\n\r\n"

    # Requirement IX
    # Print the response headers to the console
    print(f"\n--- Outgoing HTTP Response ---\n{header_str}----------------------------")

    # Send the headers first
    sock.sendall(header_str.encode('utf-8'))

    # Requirement II & III
    # Send the body for all requests except HEAD, or if it's a 304 response
    if method != "HEAD" and status != "304 Not Modified" and body:
        if is_binary:
            sock.sendall(body)
        else:
            sock.sendall(body.encode('utf-8'))


def start_server():
    """
    Starts the web server and waits for users to connect.

    When someone connects, we create a new thread
    so multiple people can use the server at the same time.
    """

    # Requirement VIII
    # Create a TCP socket (this allows computers to communicate over a network)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allows the server to restart quickly without waiting for the port to free
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Attach the server to our chosen port
    server.bind(("", PORT))

    # Start listening for incoming connections
    server.listen(10)

    print(f"[*] Server running on port {PORT}...")

    while True:
        # Wait until a client connects
        client_sock, addr = server.accept()

        # Requirement VIII
        # Start a new thread to handle that client
        thread = threading.Thread(target=handle_client, args=(client_sock, addr))
        thread.start()


# Start the server when the program is run
if __name__ == "__main__":
    start_server()