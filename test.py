from dotenv import load_dotenv
import os
import json
import urllib.request
import urllib.error

load_dotenv()

key = os.environ["GEMINI_API_KEY"]

req = urllib.request.Request(
    "https://generativelanguage.googleapis.com/v1beta/interactions",
    data=json.dumps({
        "model": "gemini-3.8-flash",
        "input": "Say OK"
    }).encode(),
    headers={
        "x-goog-api-key": key,
        "Content-Type": "application/json"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(req) as response:
        print("STATUS:", response.status)
        print(response.read().decode())

except urllib.error.HTTPError as e:
    print("STATUS:", e.code)
    print(e.read().decode())