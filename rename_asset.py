#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rename GitHub release asset with Chinese filename"""
import json, urllib.request, subprocess, sys

# Get GitHub token
token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()

name = "采购助手_Setup.exe"
url = "https://api.github.com/repos/eastseao/procurement-system/releases/assets/444981197"
data = json.dumps({"name": name}).encode("utf-8")

req = urllib.request.Request(url, data=data, method="PATCH")
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Accept", "application/vnd.github.v3+json")
req.add_header("Content-Type", "application/json")

try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        print(f"SUCCESS - Name: {result.get('name')}")
        print(f"URL: {result.get('browser_download_url')}")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
