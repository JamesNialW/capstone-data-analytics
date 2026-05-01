import requests
import csv
from dotenv import load_dotenv
import os
import base64
import json
import time

# Load environment variables from a .env file
load_dotenv()

# Encode username and password in Base64
credentials = f"{os.getenv('RAVELRY_USERNAME')}:{os.getenv('RAVELRY_PASSWORD')}"
encoded_credentials = base64.b64encode(credentials.encode()).decode()

search_url = "https://api.ravelry.com/patterns/search.json"
pattern_url = "https://api.ravelry.com/patterns.json"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Basic {encoded_credentials}"
}

page_size = 500

categories = ["clothing", "accessories", "medical", "home", "toysandhobbies", "pet", "pattern-component"]
weights = ["thread", "cobweb", "lace", "light-fingering", "fingering", "sport", "dk", "worsted", "aran", "bulky", "super-bulky", "jumbo", "unknown"]

collected_ids = set()

CHECKPOINT_FILE = 'progress_checkpoint.json'
MAX_RETRIES = 5
RETRY_BACKOFF_BASE = 2  # seconds

def load_checkpoint():
    """Load progress from checkpoint file"""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                data = json.load(f)
                return data.get('last_category'), data.get('last_weight'), data.get('last_page'), set(data.get('collected_ids', []))
        except:
            pass
    return None, None, None, set()

def save_checkpoint(category, weight, page, collected_ids):
    """Save progress to checkpoint file"""
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump({
            'last_category': category,
            'last_weight': weight,
            'last_page': page,
            'collected_ids': list(collected_ids)
        }, f)

def get_response(writer, category, weight, page):
    """Fetch response with retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            # Search for patterns with the specified parameters
            params = [
                ("page_size", page_size),
                ("availability", "-discontinued"),
                ("craft", "crochet|knitting"),
                ("year-published", "2007|2026"),
                ("pc", category),
                ("weight", weight),
                ("page", page)
            ]
            response = requests.get(search_url, headers=headers, params=params, timeout=30)

            # If the request was successful, save the pattern IDs
            if response.status_code == 200:
                data = response.json()
                pattern_ids = [str(pattern['id']) for pattern in data['patterns']]
            else:
                print("search endpoint failed", response.status_code, response.text)
                return 0

            if not pattern_ids:
                # no results this page, so nothing to fetch
                return 0
            
            rows_written = 0

            # Use the pattern IDs to fetch detailed information about each pattern
            response = requests.get(pattern_url + '?ids=' + '+'.join(pattern_ids), headers=headers, timeout=30)

            if response.status_code == 200:
                # Parse the response as JSON
                data = response.json()
                for pattern_id in pattern_ids:
                    if pattern_id in collected_ids:
                        continue

                    if pattern_id in data['patterns']:
                        pattern = data['patterns'][pattern_id]
                        free_status = pattern.get('free', False)
                        projects_count = pattern.get('projects_count', 0)
                        packs = pattern.get('packs')
                        yarn_weight_name = pattern.get('yarn_weight', {}).get('name', None)
                        craft_name = pattern.get('craft', {}).get('name', None)
                        pattern_attributes = [attr.get('permalink') for attr in pattern.get('pattern_attributes', [])]
                        pattern_type_clothing = pattern.get('pattern_type', {}).get('clothing', None)

                        # Traverse up the parent chain and collect names until parent name is "Categories"
                        pattern_categories = []
                        for category_obj in pattern.get('pattern_categories', []):
                            current = category_obj
                            while current:
                                name = current.get('name')
                                parent = current.get('parent')
                                if current.get('name') != "Categories":
                                    pattern_categories.append(name)
                                    current = parent
                                else:
                                    break
                        # Remove duplicates while preserving order
                        pattern_categories = list(dict.fromkeys(pattern_categories))

                        created_at = pattern.get('created_at', None)
                        favorites_count = pattern.get('favorites_count', 0)
                        has_uk_terminology = pattern.get('has_uk_terminology', False)
                        has_us_terminology = pattern.get('has_us_terminology', False)
                        languages = [lang.get('name') for lang in pattern.get('languages', [])]
                        pattern_author = pattern.get('pattern_author', {}).get('name', None)
                        author_id = pattern.get('pattern_author', {}).get('id', None)
                        price = pattern.get('price', None)
                        currency = pattern.get('currency', None)
                        queued_projects_count = pattern.get('queued_projects_count', 0)
                        rating_average = pattern.get('rating_average', None)
                        rating_count = pattern.get('rating_count', 0)
                        yardage = pattern.get('yardage', None)
                        packs = pattern.get('packs')

                        # Extract only the yarn IDs from each pack's 'yarn' dict
                        yarn_ids = []
                        if packs and isinstance(packs, list):
                            for pack in packs:
                                yarn = pack.get('yarn')
                                if yarn and isinstance(yarn, dict):
                                    yarn_id = yarn.get('id')
                                    if yarn_id is not None:
                                        yarn_ids.append(yarn_id)
                        
                        # get "name" from pattern_source_type in printings
                        # Structure: printings[i].pattern_source.pattern_source_type.name
                        pattern_source_type_names = []
                        for printing in pattern.get('printings', []):
                            if isinstance(printing, dict):
                                pattern_source = printing.get('pattern_source')
                                if isinstance(pattern_source, dict):
                                    source_type = pattern_source.get('pattern_source_type')
                                    if isinstance(source_type, dict):
                                        name = source_type.get('name')
                                        if name and name not in pattern_source_type_names:
                                            pattern_source_type_names.append(name)

                        # Write the row to CSV immediately
                        writer.writerow([
                            pattern_id,
                            free_status,
                            projects_count,
                            yarn_weight_name,
                            craft_name,
                            pattern_attributes,
                            pattern_type_clothing,
                            pattern_categories[-1] if len(pattern_categories) > 0 else None,
                            pattern_categories[-2] if len(pattern_categories) > 1 else None,
                            pattern_categories[-3] if len(pattern_categories) > 2 else None,
                            pattern_categories[-4] if len(pattern_categories) > 3 else None,
                            created_at,
                            favorites_count,
                            has_uk_terminology,
                            has_us_terminology,
                            languages,
                            pattern_author,
                            author_id,
                            price,
                            currency,
                            queued_projects_count,
                            rating_average,
                            rating_count,
                            yardage,
                            yarn_ids,
                            pattern_source_type_names
                        ])
                        rows_written += 1
                        collected_ids.add(pattern_id)
            else:
                print(f"Request failed with status code {response.status_code}")
                print(f"Response: {response.text}")
                return 0

            return rows_written
        
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            wait_time = RETRY_BACKOFF_BASE ** attempt
            if attempt < MAX_RETRIES - 1:
                print(f"Connection error on attempt {attempt + 1}/{MAX_RETRIES}: {type(e).__name__}")
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Failed after {MAX_RETRIES} attempts. Error: {e}")
                raise

# Define the field names for the CSV header
field_names = [
    'pattern_id', 'free_status', 'projects_count',
    'yarn_weight', 'craft', 'attributes',
    'is_clothing', 'supercategory', 'category', 'subcategory', 'babycategory',
    'created_at', 'favorites_count', 'has_uk_terminology', 'has_us_terminology',
    'languages', 'pattern_author', 'author_id', 'price', 'currency',
    'queued_projects_count', 'rating_average', 'rating_count', 'yardage', 'yarn_ids', 'pattern_source_type_names'
]

# Open with newline='' to prevent extra blank lines in Windows
with open('complete_patterns.csv', 'w', encoding='utf-8', newline='') as csvfile:
    writer = csv.writer(csvfile)
    # Write the header
    writer.writerow(field_names)
    
    # Load checkpoint to resume from last position
    last_category, last_weight, last_page, collected_ids = load_checkpoint()
    
    if last_category:
        print(f"Resuming from checkpoint: category={last_category}, weight={last_weight}, page={last_page}")
        start_category_idx = categories.index(last_category)
        start_weight_idx = weights.index(last_weight)
        start_page = last_page
    else:
        start_category_idx = 0
        start_weight_idx = 0
        start_page = 1
    
    total_rows = 0

    for cat_idx, category in enumerate(categories[start_category_idx:], start=start_category_idx):
        for weight_idx, weight in enumerate(weights[start_weight_idx if cat_idx == start_category_idx else 0:], start=start_weight_idx if cat_idx == start_category_idx else 0):
            current_page = start_page if (cat_idx == start_category_idx and weight_idx == start_weight_idx) else 1
            print(f"Starting category={category}, weight={weight}, page={current_page}")
            
            while True:
                try:
                    rows_from_page = get_response(writer, category, weight, current_page)
                    if rows_from_page == 0:
                        print(f"No results for category={category}, weight={weight}, page={current_page}, stopping this combo")
                        break

                    total_rows += rows_from_page
                    print(f"category={category}, weight={weight}, page={current_page} completed - {rows_from_page} rows written, total: {total_rows}")
                    
                    # Save checkpoint after each successful page
                    save_checkpoint(category, weight, current_page + 1, collected_ids)
                    
                    current_page += 1
                except Exception as e:
                    print(f"Error occurred: {e}")
                    print(f"Saving checkpoint at category={category}, weight={weight}, page={current_page}")
                    save_checkpoint(category, weight, current_page, collected_ids)
                    raise

    print("\nFinished writing", total_rows, "rows to complete_patterns.csv")
    # Clear checkpoint on successful completion
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
