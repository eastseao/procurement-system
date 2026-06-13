#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Upload release asset with proper Chinese filename support"""
import json, urllib.request, subprocess, os

token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()

filepath = r"I:\采购管理系统\采购管理系统V2.2.1\dist\采购助手_Setup.exe"
filename = "采购助手_Setup.exe"

# Get the upload URL
get_url = "https://api.github.com/repos/eastseao/procurement-system/releases/tags/v2.2.3"
req = urllib.request.Request(get_url)
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Accept", "application/vnd.github.v3+json")
with urllib.request.urlopen(req) as resp:
    release = json.loads(resp.read())

upload_url = release["upload_url"].replace("{?name,label}", f"?name={urllib.request.quote(filename)}")
print(f"Upload URL: {upload_url}")

# Read file
with open(filepath, "rb") as f:
    filedata = f.read()

# Upload using multipart/form-data
import http.client

# Parse the upload URL
from urllib.parse import urlparse
parsed = urlparse(upload_url)

conn = http.client.HTTPSConnection(parsed.hostname)
boundary = "----FormBoundary7MA4YWxkTrZu0gW"

body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
    f"Content-Type: application/x-msdownload\r\n"
    f"\r\n"
).encode("utf-8") + filedata + f"\r\n--{boundary}--\r\n".encode("utf-8")

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": f"multipart/form-data; boundary={boundary}",
}

conn.request("POST", parsed.path + "?" + parsed.query, body, headers)
resp = conn.getresponse()
result = json.loads(resp.read())
print(f"Result: {json.dumps(result, indent=2, ensure_ascii=False)}")
if "name" in result:
    print(f"SUCCESS - Uploaded as: {result['name']}")
    print(f"Download: {result['browser_download_url']}")
