import urllib.request
import json

def submit_to_indexnow():
    host = "calculatordrive.com"
    key = "5b2c8a149f3e4d7a8b6e2d1f0c5a9b8e"
    key_location = f"https://{host}/{key}.txt"
    
    languages = ['es', 'fr', 'de', 'pt', 'ja', 'hi', 'it', 'ru', 'nl']
    base_paths = [
        "/finance/house-affordability-calculator/",
        "/finance/discount-calculator/",
        "/finance/down-payment-calculator/",
        "/health/healthy-weight-calculator/",
        "/health/overweight-calculator/",
        "/health/pace-calculator/",
        "/health/gfr-calculator/"
    ]
    
    url_list = []
    
    # Add root (English) versions
    for base in base_paths:
        url_list.append(f"https://{host}{base}")
        # Add translated versions
        for lang in languages:
            url_list.append(f"https://{host}/{lang}{base}")
    
    print(f"Submitting {len(url_list)} URLs to IndexNow...")
    
    data = {
        "host": host,
        "key": key,
        "keyLocation": key_location,
        "urlList": url_list
    }
    
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        response = urllib.request.urlopen(req)
        print(f"Success! Status Code: {response.getcode()}")
        print(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error submitting to IndexNow: {e}")

if __name__ == "__main__":
    submit_to_indexnow()
