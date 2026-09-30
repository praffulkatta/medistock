import httpx
import asyncio
import uuid

BASE_URL = 'http://localhost:8000/api/v1'

async def test_crud():
    async with httpx.AsyncClient() as client:
        pharmacy_id = str(uuid.uuid4())
        
        print('Testing Categories...')
        cat_id = None
        try:
            r = await client.post(f'{BASE_URL}/categories', json={'name': 'Analgesics', 'pharmacy_id': pharmacy_id})
            print(f'Create Category: {r.status_code}')
            cat_id = r.json()['id']
            
            r = await client.get(f'{BASE_URL}/categories/{cat_id}')
            print(f'Get Category: {r.status_code}')
            
            r = await client.put(f'{BASE_URL}/categories/{cat_id}', json={'name': 'Painkillers'})
            print(f'Update Category: {r.status_code}')
            
            r = await client.delete(f'{BASE_URL}/categories/{cat_id}')
            print(f'Delete Category: {r.status_code}')
        except Exception as e:
            print(f'Category Error: {e}')

        print('\nTesting Suppliers...')
        try:
            r = await client.post(f'{BASE_URL}/suppliers', json={'name': 'Global Pharma', 'pharmacy_id': pharmacy_id})
            print(f'Create Supplier: {r.status_code}')
        except Exception as e:
            print(f'Supplier Error: {e}')

        print('\nTesting Medicines...')
        try:
            # Need a valid category_id for medicine
            r = await client.post(f'{BASE_URL}/categories', json={'name': 'Test Cat', 'pharmacy_id': pharmacy_id})
            cat_id = r.json()['id']
            
            r = await client.post(f'{BASE_URL}/medicines', json={
                'name': 'Dolo 650', 
                'generic_name': 'Paracetamol', 
                'manufacturer': 'GSK', 
                'category_id': cat_id,
                'dosage_form': 'Tablet', 
                'strength': '650mg', 
                'prescription_required': False, 
                'pharmacy_id': pharmacy_id
            })
            print(f'Create Medicine: {r.status_code}')
        except Exception as e:
            print(f'Medicine Error: {e}')

        print('\nTesting Locations...')
        try:
            r = await client.post(f'{BASE_URL}/locations', json={'name': 'Block A', 'type': 'Block', 'level': 1, 'pharmacy_id': pharmacy_id})
            block_id = r.json()['id']
            print(f'Create Block: {r.status_code}')
            
            r = await client.post(f'{BASE_URL}/locations', json={'name': 'Rack 01', 'type': 'Rack', 'level': 2, 'pharmacy_id': pharmacy_id, 'parent_id': block_id})
            rack_id = r.json()['id']
            print(f'Create Rack: {r.status_code}')
            
            # Invalid level jump (L2 -> L4)
            r = await client.post(f'{BASE_URL}/locations', json={'name': 'Bin 01', 'type': 'Bin', 'level': 4, 'pharmacy_id': pharmacy_id, 'parent_id': rack_id})
            print(f'Create Bin (invalid level): {r.status_code}')
        except Exception as e:
            print(f'Location Error: {e}')

if __name__ == '__main__':
    asyncio.run(test_crud())
