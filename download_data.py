import argparse
import os
import re
import time
import requests
from bs4 import BeautifulSoup
import gdown
from urllib.parse import urljoin, urlparse, unquote

def sanitize_filename(filename):
    """Sanitize the filename to remove invalid characters."""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def dataset_slug(url):
    """Return the OpenCity dataset slug for a URL when present."""
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.strip('/').split('/')
    if len(path_parts) >= 2 and path_parts[0] == 'dataset':
        return path_parts[1]
    return ''

def download_file(url, output_path):
    """Download a file from a URL to the specified output path."""
    if os.path.exists(output_path):
        print(f"  [SKIPPED] {output_path} already exists.")
        return True

    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Check if the response is HTML, if so, it might not be a direct file
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type and not url.endswith(('.kml', '.csv', '.pdf', '.zip')):
             print(f"  [WARNING] {url} returned HTML content, might not be the actual file.")
             # We might still want to download it, or maybe skip
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"  [SUCCESS] Downloaded {output_path}")
        return True
    except Exception as e:
        print(f"  [ERROR] Failed to download {url}: {e}")
        if os.path.exists(output_path):
            os.remove(output_path) # Clean up partial file
        return False

def process_opencity_url(url, base_dir):
    """Process a data.opencity.in URL to find and download resources."""
    print(f"\nProcessing OpenCity URL: {url}")
    try:
        # Extract the slug for the folder name
        dataset_name = dataset_slug(url) or 'uncategorized'
            
        dataset_dir = os.path.join(base_dir, sanitize_filename(dataset_name))
        os.makedirs(dataset_dir, exist_ok=True)
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all download links with class resource-url-analytics
        download_links = soup.find_all('a', class_='resource-url-analytics')
        
        if not download_links:
            print("  [INFO] No standard download links found on this page.")
            return
            
        for link in download_links:
            href = link.get('href')
            if href:
                # Some hrefs might be relative
                if not href.startswith('http'):
                    href = urljoin('https://data.opencity.in', href)
                
                # Try to get a meaningful filename
                # Often it's the last part of the URL
                filename = unquote(href.split('/')[-1])
                # If there's no extension, it might be tricky, but we'll try to use it as is
                if not '.' in filename:
                    filename += '.download'
                    
                output_path = os.path.join(dataset_dir, sanitize_filename(filename))
                download_file(href, output_path)
                time.sleep(1) # Be polite
                
    except Exception as e:
        print(f"  [ERROR] Failed to process {url}: {e}")

def process_gdrive_url(url, base_dir):
    """Process a Google Drive URL using gdown."""
    print(f"\nProcessing Google Drive URL: {url}")
    try:
        dataset_dir = os.path.join(base_dir, "google_drive_files")
        os.makedirs(dataset_dir, exist_ok=True)
        
        print("  [INFO] Starting gdown...")
        old_cwd = os.getcwd()
        os.chdir(dataset_dir)
        try:
            output_file = gdown.download(url, quiet=False, fuzzy=True)
        finally:
            os.chdir(old_cwd)
        
        if output_file:
            target_path = os.path.join(dataset_dir, os.path.basename(output_file))
            print(f"  [SUCCESS] Downloaded to {target_path}")
        else:
            print("  [ERROR] gdown failed to download the file.")
            
    except Exception as e:
         print(f"  [ERROR] Failed to process Google Drive URL {url}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Download waterquality source datasets.")
    parser.add_argument(
        '--only',
        nargs='*',
        default=None,
        help="Only process URLs whose dataset slug or full URL contains one of these tokens.",
    )
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    urls_file = os.path.join(base_dir, 'urls.txt')
    
    if not os.path.exists(urls_file):
        print(f"Error: {urls_file} not found.")
        return
        
    with open(urls_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    if args.only:
        tokens = [token.lower() for token in args.only]
        urls = [
            url for url in urls
            if any(token in dataset_slug(url).lower() or token in url.lower() for token in tokens)
        ]
        
    print(f"Found {len(urls)} URLs to process.")
    
    for url in urls:
        if 'data.opencity.in' in url:
            process_opencity_url(url, data_dir)
        elif 'drive.google.com' in url:
            process_gdrive_url(url, data_dir)
        else:
            print(f"\n[WARNING] Unrecognized URL format, skipping: {url}")
            
        time.sleep(2) # Be polite between pages

if __name__ == '__main__':
    main()
