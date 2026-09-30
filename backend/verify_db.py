import sys
import os
import subprocess
import time
import requests

current_dir = os.getcwd()
sys.path.append(current_dir)

os.environ['DATABASE_URL'] = 'postgresql://postgres:medistock_pass@localhost:5432/medistock_db'

print('Starting server...')
proc = subprocess.Popen(['python', '-m', 'uvicorn', 'app.main:app', '--port', '8000'], 
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

time.sleep(7)
try:
    resp = requests.get('http://localhost:8000/health')
    print(f'Status: {resp.status_code}')
    print(f'Response: {resp.json()}')
except Exception as e:
    print(f'Error: {e}')
    print('Server output:')
    print(proc.stdout.read())
    print(proc.stderr.read())

proc.terminate()
