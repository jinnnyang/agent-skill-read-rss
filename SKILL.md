---
name: read-rss
description: Fetches and displays content from RSS feeds using a user-provided OPML source. It includes caching to minimize network requests.
---

# read-rss

This skill fetches and displays content from RSS feeds. It uses a user-provided OPML feed URL to discover RSS sources, caches fetched data, and provides command-line access to the information.

## When to use

Use this skill when you need to:
- Read articles from RSS feeds.
- Get a list of available RSS feeds from an OPML URL.
- Get a list of articles from a specific RSS feed.
- Read the content of a specific article.

## When NOT to use

- If you need to manage or subscribe to new RSS feeds. This skill only reads from a pre-configured OPML file.

## Initial Setup & Configuration Check

Before using the skill, the agent **must** ensure the OPML feed URL is configured.

1.  **Check for Configuration**: Read the file at `<read-rss-skill>/assets/config.json`.
2.  **Validate**:
    - If the file exists and contains a non-empty `"opml_url"` key, the setup is complete. Proceed to the workflow.
    - If the file does not exist, or the `"opml_url"` key is missing or empty, you **must** ask the user to provide the OPML feed URL before proceeding.

The script will automatically create the necessary caching directories (`assets/items/` and `assets/content/`) on its first run.

## Workflow

The primary logic is handled by the `scripts/rss_fetcher.py` script.

### 1. Fetching all RSS Feeds

To get a list of all available RSS feeds from the configured OPML URL, the agent will execute the following command:

```sh
python <read-rss-skill>/scripts/rss_fetcher.py --opml-url <your-opml-url>
```
(Replace `<your-opml-url>` with the actual URL if it's the first time). The script will print a markdown-formatted list of feeds.

### 2. Fetching and Caching Articles from a Feed

The script uses an intelligent caching mechanism to maintain a complete, up-to-date list of articles for each feed.

#### A. Fetching and Updating the Cache (Standard Operation)

To get all articles for a feed and ensure the local cache is updated with the latest entries, **always use the `--name` parameter**. This is the standard and recommended way to interact with a feed.

This command performs a "fetch and merge" operation:
1.  It fetches the latest articles from the network.
2.  It loads the existing articles from the local cache file (e.g., `assets/items/<feed-title>.jsonl`).
3.  It merges the new and old articles, removing any duplicates based on the article's unique `link`.
4.  It overwrites the cache file with the complete, deduplicated, and sorted list.
5.  Finally, it prints the entire updated list of articles to the console.

```sh
python <read-rss-skill>/scripts/rss_fetcher.py --feed-url "<feed-xml-url>" --name "<feed-title>"
```

#### B. One-Time Fetch without Caching

If you need to quickly see the latest articles from a feed without reading from or writing to the persistent cache, **omit the `--name` parameter**.

This command will simply fetch the latest articles from the network and print them. It will **not** interact with the cache in any way. This is useful for temporary checks where you don't want to update the main article list.

```sh
python <read-rss-skill>/scripts/rss_fetcher.py --feed-url "<feed-xml-url>"
```

#### C. Controlling Output with --head

By default, when fetching articles, the script will only display the **5 most recent** items from the list. You can control this number using the optional `--head` argument.

For example, to see only the latest 3 articles:
```sh
python <read-rss-skill>/scripts/rss_fetcher.py --feed-url "<feed-xml-url>" --name "<feed-title>" --head 3
```
This applies to both standard (cached) and one-time fetches.

### 3. Reading an Article's Content

To read a specific article, the agent will use the `link`, `title`, `author`, and `pubDate` from the article list and run:

```sh
python <read-rss-skill>/scripts/rss_fetcher.py --content-url "<article-link>" --title "<article-title>" --author "<article-author>" --date "<article-pubDate>"
```
This will fetch (or load from cache) the article content and print it as markdown.

## Configuration

The OPML URL is stored in `<read-rss-skill>/assets/config.json`. The agent will handle the creation and updating of this file.
