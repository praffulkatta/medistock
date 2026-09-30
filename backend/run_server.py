import os
import sys

sys.path.append(os.getcwd())
os.system('python -m uvicorn app.main:app --port 8000')
