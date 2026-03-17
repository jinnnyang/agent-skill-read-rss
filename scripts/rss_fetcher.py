
import sys
import io

# Force UTF-8 encoding for stdout
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import argparse
import json
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen, Request

import markdownify
import requests
from bs4 import BeautifulSoup
# --- Configuration ---

# --- Configuration ---
SKILL_DIR = Path(__file__).parent.parent
ASSETS_DIR = SKILL_DIR / "assets"
CONFIG_FILE = ASSETS_DIR / "config.json"
ITEMS_CACHE_DIR = ASSETS_DIR / "items"
CONTENT_CACHE_DIR = ASSETS_DIR / "content"

# --- Helper Functions ---

def deduplicate_items(items, key='link'):
    """Deduplicate a list of dictionaries based on a unique key."""
    seen = set()
    unique_items = []
    for item in items:
        # Ensure the item has the key before trying to access it
        if key in item and item[key] not in seen:
            seen.add(item[key])
            unique_items.append(item)
    return unique_items

def ensure_dirs():
    """Create necessary directories if they don't exist."""
    ITEMS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CONTENT_CACHE_DIR.mkdir(parents=True, exist_ok=True)

def load_config():
    """Load the OPML URL from the config file."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(data):
    """Save the OPML URL to the config file."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def xml_to_dict(element):
    """Recursively convert an XML element to a dictionary."""
    if not element:
        return None
    if element.text and element.text.strip():
        return element.text.strip()

    d = {}
    for child in element:
        child_dict = xml_to_dict(child)
        tag = child.tag.split('}')[-1] 
        if tag in d:
            if not isinstance(d[tag], list):
                d[tag] = [d[tag]]
            d[tag].append(child_dict)
        else:
            d[tag] = child_dict
    
    # Add attributes to the dictionary
    if element.attrib:
        d.update(('@' + k, v) for k, v in element.attrib.items())
        
    return d

def dump_jsonl(data, path):
    """Append data to a JSONL file."""
    with open(path, "a", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

def load_jsonl(path):
    """Load data from a JSONL file."""
    if not Path(path).exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f]

def sanitize_filename(name):
    """Sanitize a string to be used as a filename."""
    return re.sub(r'[\\/*?:"<>|]', "", name)

def make_get_request(url):
    """Make a GET request."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

# --- Core Class ---

class RSSFetcher:
    """
    Fetches, parses, and caches RSS feeds and articles.
    """

    def __init__(self, opml_url=None):
        self.config = load_config()
        if opml_url:
            self.config["opml_url"] = opml_url
            save_config(self.config)
        self.opml_url = self.config.get("opml_url")

    def fetch_feeds(self):
        """Fetch and parse the OPML file to get a list of RSS feeds."""
        if not self.opml_url:
            raise ValueError("OPML URL not configured. Please provide one with --opml-url.")
        
        req = Request(self.opml_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req) as response:
            xml_string = response.read().decode('utf-8')
        
        root = ET.fromstring(xml_string)
        feeds = []
        for outline in root.findall(".//outline[@type='rss']"):
            feeds.append({
                "text": outline.attrib.get("text"),
                "title": outline.attrib.get("title"),
                "type": outline.attrib.get("type"),
                "xmlUrl": outline.attrib.get("xmlUrl"),
                "htmlUrl": outline.attrib.get("htmlUrl"),
            })
        return feeds

    def fetch_items(self, feed_url, name=None):
        """Fetch, parse, and update the cache for an RSS feed."""
        # 1. Always fetch fresh items from the network
        req = Request(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req) as response:
            xml_string = response.read().decode('utf-8')

        root = ET.fromstring(xml_string)
        new_items = []
        for item in root.findall(".//item"):
            tags = [tag.text.strip() for tag in item.findall("tag") if tag.text]
            keywords = [keyword.text.strip() for keyword in item.findall("keyword") if keyword.text]
            new_items.append({
                "title": item.findtext("title", "").strip(),
                "link": item.findtext("link", "").strip(),
                "guid": item.findtext("guid", "").strip(),
                "pubDate": item.findtext("pubDate", "").strip(),
                "description": item.findtext("description", "").strip(),
                "author": item.findtext("author", "").strip(),
                "tags": tags,
                "keywords": keywords,
            })

        # 2. The cache key is the feed URL, ensuring a consistent cache file.
        # The optional 'name' now controls whether to read existing cache (sync) or just refresh.
        cache_file = ITEMS_CACHE_DIR / f"{sanitize_filename(feed_url)}.jsonl"

        # 3. If a name is provided, load old items to sync. Otherwise, start fresh.
        old_items = []
        if name and cache_file.exists():
            old_items = load_jsonl(cache_file)

        # 4. Combine, deduplicate, and sort. This always happens.
        combined_items = old_items + new_items
        unique_items = deduplicate_items(combined_items, key='link')

        try:
            unique_items.sort(key=lambda x: datetime.strptime(x['pubDate'], "%a, %d %b %Y %H:%M:%S %Z"), reverse=True)
        except (ValueError, KeyError):
            # If date parsing fails, do not sort
            pass

        # 5. Overwrite cache with the updated list. This always happens.
        with open(cache_file, "w", encoding="utf-8") as f:
            for item in unique_items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

        # 6. Return the processed items.
        return unique_items

    def fetch_content(self, content_url, title, author, date):
        """Fetch the content of an article."""
        if date:
            try:
                date_obj = datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %Z")
                date_str = date_obj.strftime("%Y%m%d")
            except ValueError:
                date_str = "nodate"
        else:
            date_str = "nodate"

        filename = f"{sanitize_filename(title)}-{sanitize_filename(author)}-{date_str}.html"
        cache_file = CONTENT_CACHE_DIR / filename
        
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                return f.read()

        content = make_get_request(content_url)

        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        return content

    @staticmethod
    def ppprint_feeds(feeds):
        """Print feeds in a markdown format."""
        print("# RSS Feeds")
        for feed in feeds:
            print(f"- **{feed['title']}**")
            print(f"  - XML URL: `{feed['xmlUrl']}`")

    @staticmethod
    def ppprint_items(items):
        """Print items in a markdown format."""
        print("# Articles")
        for item in items:
            print(f"## {item['title']}")
            print(f"- **Author**: {item.get('author', 'N/A')}")
            print(f"- **Date**: {item.get('pubDate', 'N/A')}")
            print(f"- **Link**: {item.get('link', '#')}")
            if item.get("tags"):
                print(f"- **Tags**: {', '.join(item['tags'])}")
            if item.get("keywords"):
                print(f"- **Keywords**: {', '.join(item['keywords'])}")
            print(f"\n> {item.get('description', 'No description available.')}\n")

    @staticmethod
    def ppprint_content(html_content):
        """Convert HTML content to markdown and print it."""
        md_content = markdownify.markdownify(html_content, heading_style="ATX")
        print(md_content)


if __name__ == "__main__":
    ensure_dirs()

    parser = argparse.ArgumentParser(description="Fetch RSS feeds and articles.")
    parser.add_argument("--opml-url", help="URL of the OPML file.")
    parser.add_argument("--feed-url", help="URL of the RSS feed.")
    parser.add_argument("--name", help="Name of the RSS feed (for caching).")
    parser.add_argument("--head", type=int, default=5, help="Number of recent articles to display (default: 5).")
    parser.add_argument("--content-url", help="URL of the article content.")
    parser.add_argument("--title", help="Title of the article (for caching).")
    parser.add_argument("--author", help="Author of the article (for caching).")
    parser.add_argument("--date", help="Publication date of the article (for caching).")

    args = parser.parse_args()

    fetcher = RSSFetcher(opml_url=args.opml_url)

    if args.content_url:
        if not all([args.title, args.author, args.date]):
            print("Warning: Missing title, author, or date. Cache will not be used effectively.")
        
        content = fetcher.fetch_content(args.content_url, args.title or "", args.author or "", args.date or "")
        fetcher.ppprint_content(content)
    elif args.feed_url:
        items = fetcher.fetch_items(args.feed_url, args.name)
        fetcher.ppprint_items(items[:args.head])
    elif args.opml_url or fetcher.opml_url:
        feeds = fetcher.fetch_feeds()
        fetcher.ppprint_feeds(feeds)
    else:
        print("No valid arguments provided. Use --help for more information.")
