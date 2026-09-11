from flask import Flask
import socket, os
 
app = Flask(__name__)
 
@app.route("/")
def home():
    return f"Hello from {socket.gethostname()} | Version: {os.getenv('APP_VERSION','v1')}"
 
@app.route("/health")
def health():
    return "OK", 200
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
