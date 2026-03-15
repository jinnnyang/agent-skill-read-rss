# RSS Reader Skill

## 1. Purpose

This skill enables an agent to discover, fetch, and read content from online RSS and OPML feeds. It is designed to be operated via command-line execution.

## 2. Prerequisites

The execution environment must support:
- Python 3.x.
- The ability to install Python packages from a `requirements.txt` file.
- Network access to fetch remote content.

The required Python packages are listed in `scripts/requirements.txt`.

## 3. Configuration

Before first use, a configuration file must be set up to specify the source of the RSS feeds.

- **File to Edit:** `assets/config.json`
- **Action:** Provide a valid URL for an OPML file in the `opml_url` field.

**Example `config.json`:**
```json
{
  "opml_url": "https://your-opml-provider.com/feeds.opml"
}
```

**Note:** The `assets` directory is used for local configuration and caching. It should be excluded from version control.

## 4. Core Commands

The skill's functionality is exposed through the `scripts/rss_fetcher.py` script.

### Command: List Feeds
**Action:** Discovers all available RSS feeds from the configured OPML URL.
**Syntax:**
```
python scripts/rss_fetcher.py --opml-url <your-opml-url>
```

### Command: List Articles from a Feed
**Action:** Fetches the list of recent articles from a specified RSS feed.
**Syntax:**
```
python scripts/rss_fetcher.py --feed-url "<feed_xml_url>" --name "<feed_name>"
```
- **`<feed_xml_url>`**: The direct URL to the feed's XML file.
- **`<feed_name>`**: A unique name for the feed, used for caching.

### Command: Read Article Content
**Action:** Fetches the full content of a specific article.
**Syntax:**
```
python scripts/rss_fetcher.py --content-url "<article_url>" --title "<article_title>" --author "<article_author>" --date "<publication_date>"
```
- **`<article_url>`**: The URL of the article to read.
- Other parameters are used for creating a unique cache entry.
