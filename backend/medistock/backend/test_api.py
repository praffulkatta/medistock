import requests
import uuid

BASE_URL = 'http://localhost:8000'

def test_api():
    try:
        # 1. Health check
        print('Checking health...', end=' ')
        r = requests.get(f'{BASE_URL}/health')
        print(f'{r.status_code}')

        # 2. Create Category
        print('Creating category...', end=' ')
        cat_id = str(uuid.uuid4())
        # Note: In a real test we would need a pharmacy_id
        # For this foundation check, we assume a pharmacy exists or we create one.
        # Since I cannot easily create one without a pharmacy model in this script,
        # I will just check if the endpoints are reachable.
        r = requests.post(f'{BASE_URL}/api/v1/categories', json={'name': 'Painkillers', 'pharmacy_id': str(uuid.uuid4())})
        print(f'{r.status_code}')

    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test_api()
