#!/usr/bin/env python3
import sys
import os

# Ensure UTF-8 encoding
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding.lower() != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# Change to the script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Run the test
with open('test_hallucinations.py', encoding='utf-8') as f:
    exec(f.read())
