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

## Output Formatting Requirements

When presenting content retrieved from an RSS source (either a list of articles or the content of a single article), you **must** clearly attribute the source and publication time. This helps the user understand the context of the information.

You can use one of the following formats or a similar one, as long as the information is conveyed clearly:

*   Append the attribution in parentheses: `(Author, YYYYMMDD)`
    *   Example: `(National Data Bureau, 20260315)`
*   Integrate the attribution into a sentence:
    *   Example: `On 20260315, the National Data Bureau released news that...`
    *   Example: `This morning at 9:13 AM, the National Data Bureau published...`

**Core Requirement**: Ensure the user can easily identify the **source** and **time** for each piece of information.

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

### 2. Fetching Articles from Feeds (Looping Workflow)

To ensure comprehensive coverage, the agent should fetch articles from multiple feeds in a loop. After getting the list of all available feeds (Step 1), follow this procedure:

1.  **Select Feeds to Process**:
    *   If the user specifies a particular feed, prioritize that one.
    *   If not, select **5 to 10** different feeds from the list returned in Step 1. The agent should aim for a variety of sources.
    *   **Constraint**: Process a minimum of 1 and a maximum of 15 feeds unless the user gives a different instruction.

2.  **Loop and Fetch for Each Feed**: For each selected feed URL, execute the fetching command. It is highly recommended to use `--head` (e.g., `--head 10`) to keep the output for each feed concise.

**Example Loop**:
```sh
# Fetch top 10 articles from the first feed and update its cache
python <read-rss-skill>/scripts/rss_fetcher.py --feed-url "<feed-xml-url1>" --head 10

# Fetch top 10 articles from the second feed and update its cache
python <read-rss-skill>/scripts/rss_fetcher.py --feed-url "<feed-xml-url2>" --head 10

# Fetch top 10 articles from the third feed and update its cache
python <read-rss-skill>/scripts/rss_fetcher.py --feed-url "<feed-xml-url3>" --head 10

# Fetch top 10 articles from the forth feed and update its cache
python <read-rss-skill>/scripts/rss_fetcher.py --feed-url "<feed-xml-url4>" --head 10

# Fetch top 10 articles from the fifth feed and update its cache
python <read-rss-skill>/scripts/rss_fetcher.py --feed-url "<feed-xml-url5>" --head 10
```
This proactive approach ensures the agent gathers a broader range of information.

#### Command Details: Caching and Output Control

The script uses an intelligent caching mechanism. Here are the details for each command you run inside the loop:

##### A. Fetching and Updating the Cache

To fetch the latest articles from a feed and update the local cache, provide the `--feed-url` but **omit the `--name` parameter**. This is the standard operation inside the loop.

```sh
python <read-rss-skill>/scripts/rss_fetcher.py --feed-url "<feed-xml-url>"
```

##### B. Reading from Cache (No Update)

If you only need to see articles already stored for a feed without fetching new ones, **use the `--name` parameter**. This is faster but will not provide the latest content.

```sh
python <read-rss-skill>/scripts/rss_fetcher.py --feed-url "<feed-xml-url>" --name "<feed-title>"
```

##### C. Controlling Output with --head

By default, the script displays the **5 most recent** items. Use the `--head` argument to control this number. This is essential for the looping workflow to keep the context manageable.

```sh
python <read-rss-skill>/scripts/rss_fetcher.py --feed-url "<feed-xml-url>" --head 3
```

### 3. Reading an Article's Content

To read a specific article, the agent will use the `link`, `title`, `author`, and `pubDate` from the article list and run:

```sh
python <read-rss-skill>/scripts/rss_fetcher.py --content-url "<article-link>" --title "<article-title>" --author "<article-author>" --date "<article-pubDate>"
```
This will fetch (or load from cache) the article content and print it as markdown.

## Configuration

The OPML URL is stored in `<read-rss-skill>/assets/config.json`. The agent will handle the creation and updating of this file.
