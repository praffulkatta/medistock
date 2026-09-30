import sys
import os
sys.path.append(os.getcwd())
try:
    from app.api import endpoints
    print('Import successful')
except Exception as e:
    print(f'Import failed: {e}')
