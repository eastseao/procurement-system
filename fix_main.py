#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 main.py 第21-22行的错误内容"""

import os

file_path = r"I:\采购管理系统\采购管理系统1.4\main.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 查找并删除第21-22行的错误内容
new_lines = []
skip_next = False
for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
    
    # 跳过包含分隔符的行
    if '───────────────────────────────────' in line:
        skip_next = True  # 跳过下一行（LOG_FILE = os.path.join(DATA_DIR, "error.log")）
        continue
    
    # 跳过 LOG_FILE = os.path.join(DATA_DIR, "error.log") 这一行
    if 'LOG_FILE = os.path.join(DATA_DIR, "error.log")' in line:
        continue
    
    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("修复完成")
