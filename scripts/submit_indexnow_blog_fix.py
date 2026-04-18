import urllib.request
import json

def submit_blog_urls():
    host = "calculatordrive.com"
    key = "5b2c8a149f3e4d7a8b6e2d1f0c5a9b8e"
    key_location = f"https://{host}/{key}.txt"
    
    languages = ['de', 'it', 'es', 'ja', 'nl', 'ru', 'hi', 'pt', 'fr']
    
    url_list = []
    
    for lang in languages:
        url_list.append(f"https://{host}/{lang}/blog/")
    
    # Also add the english version just in case
    url_list.append(f"https://{host}/blog/")
    
    # And the sitemap itself
    url_list.append(f"https://{host}/sitemap.xml")
    
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
    submit_blog_urls()
