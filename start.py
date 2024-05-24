import os
import sys
import subprocess
from venv import logger
from dotenv import load_dotenv
import time

def start_server():
    print("Starting Flask server...")
    try:
        python_executable = sys.executable
        subprocess.Popen([python_executable, "server.py"])
    except Exception as e:
        logger.error(f"Failed to start Flask server: {e}")
        sys.exit(1)

def set_ngrok_auth_token(auth_token):
    print("Setting ngrok auth token...")
    try:
        subprocess.run(["ngrok", "authtoken", auth_token])
    except Exception as e:
        logger.error(f"Failed to set ngrok token: {e}")
        sys.exit(1)

def start_ngrok(domain, port):
    print("Starting ngrok...")
    try:
        subprocess.Popen(["ngrok", "http", "--domain=" + domain, port])
    except Exception as e:
        logger.error(f"Failed to start ngrok: {e}")
        sys.exit(1)

if __name__ == "__main__":
    
    load_dotenv()

    port = os.getenv('FLASK_PORT')
    ngrok_auth_token = os.getenv('NGROK_AUTH_TOKEN')
    ngrok_server_domain = os.getenv('NGROK_SERVER_DOMAIN')

    start_server()
    time.sleep(5)

    set_ngrok_auth_token(ngrok_auth_token)

    start_ngrok(ngrok_server_domain, port)