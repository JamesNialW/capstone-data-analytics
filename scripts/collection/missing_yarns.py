import requests
import csv
from dotenv import load_dotenv
import os
import base64
import time

# Load environment variables from a .env file
load_dotenv()


# Encode username and password in Base64
credentials = f"{os.getenv('RAVELRY_USERNAME')}:{os.getenv('RAVELRY_PASSWORD')}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()
# encoded_credentials = "0aba9df92b9fd51d853f6784ea5c3e81:54OSZBskYnYitSMO_s_o5-o0OuDrxOPVvG9ic5bA"

search_url = "https://api.ravelry.com/yarns/search.json"
yarn_url = "https://api.ravelry.com/yarns.json"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {encoded_credentials}"
}

field_names = [
    'id', 'animal_fiber', 'synthetic_fiber', 'vegetable_fiber', 'yarn_fiber_names', 'yarn_weight'
]

# Open with newline='' to prevent extra blank lines in Windows
with open('missing_yarns.csv', 'w', encoding='utf-8', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # Write the header
    writer.writerow(field_names)
    
    total_rows = 0
    weights = ["light-fingering", "fingering", "sport", "dk", "aran", "bulky", "super-bulky", "jumbo"]
    for weight in weights:
        print(f"Starting weight: {weight}")
        current_page = 1
        while True:
            params = [("page_size", 100), ("page", current_page), ("weight", weight)]
            response = requests.get(search_url, headers=headers, params=params)
            time.sleep(0.1)  # Rate limiting
            
            if response.status_code == 200:
                data = response.json()
                if weight == "thread" and current_page == 1:
                    print(f"Paginator for thread: {data['paginator']}")
                yarn_ids = [str(yarn['id']) for yarn in data['yarns']]
                print(f"Weight {weight} page {current_page}: {len(yarn_ids)} yarns found")
                if not yarn_ids:
                    print(f"No more results for weight {weight} at page {current_page}")
                    break
                
                # Fetch detailed information
                response2 = requests.get(yarn_url + '?ids=' + '+'.join(yarn_ids), headers=headers)
                time.sleep(0.1)
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    rows_written = 0
                    for yarn_id in yarn_ids:
                        if yarn_id in data2['yarns']:
                            yarn = data2['yarns'][yarn_id]
                            yarn_fibers = yarn.get('yarn_fibers', [])
                            yarn_weight = yarn.get('yarn_weight', {}).get('name', 'Unknown')

                            # If any fiber_type has `'animal_fiber': True`, then we consider the yarn to be an animal fiber yarn
                            if any(fiber.get('fiber_type', {}).get('animal_fiber', False) for fiber in yarn_fibers):
                                animal_fiber = True
                            else:
                                animal_fiber = False
                            # Repeat for synthetic
                            if any(fiber.get('fiber_type', {}).get('synthetic', False) for fiber in yarn_fibers):
                                synthetic_fiber = True
                            else:
                                synthetic_fiber = False
                            # Repeat for vegetable_fiber
                            if any(fiber.get('fiber_type', {}).get('vegetable_fiber', False) for fiber in yarn_fibers):
                                vegetable_fiber = True
                            else:
                                vegetable_fiber = False

                            # Collect every single `name` from every single fiber_type field for each yarn
                            yarn_fiber_names = [fiber.get('fiber_type', {}).get('name') for fiber in yarn_fibers]

                            # Write the row to CSV immediately
                            writer.writerow([
                                yarn_id, animal_fiber, synthetic_fiber, vegetable_fiber, yarn_fiber_names, yarn_weight
                            ])
                            rows_written += 1
                    total_rows += rows_written
                    print(f'Weight {weight} page {current_page} completed - {rows_written} rows written, total: {total_rows}')
                else:
                    print(f"Request failed for details on weight {weight} page {current_page} with status code {response2.status_code}")
                    break
            else:
                print(f"Search failed for weight {weight} page {current_page} with status code {response.status_code}")
                break
            
            current_page += 1

print("\nFinished writing", total_rows, "rows to missing_yarns.csv")
