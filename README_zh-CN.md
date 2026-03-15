# RSS 阅读器技能

## 1. 目的

此技能使智能体能够发现、获取和阅读来自在线 RSS 和 OPML 订阅源的内容。它被设计为通过命令行执行来操作。

## 2. 先决条件

执行环境必须支持：
- Python 3.x。
- 能够从 `requirements.txt` 文件安装 Python 包。
- 用于获取远程内容的网络访问权限。

所需的 Python 包在 `scripts/requirements.txt` 中列出。

## 3. 配置

首次使用前，必须设置一个配置文件来指定 RSS 订阅源的来源。

- **需编辑文件：** `assets/config.json`
- **操作：** 在 `opml_url` 字段中提供一个有效的 OPML 文件 URL。

**`config.json` 示例：**
```json
{
  "opml_url": "https://your-opml-provider.com/feeds.opml"
}
```

**注意：** `assets` 目录用于本地配置和缓存，应从版本控制中排除。

## 4. 核心命令

该技能的功能通过 `scripts/rss_fetcher.py` 脚本提供。

### 命令：列出订阅源
**操作：** 从配置的 OPML URL 中发现所有可用的 RSS 订阅源。
**语法：**
```
python scripts/rss_fetcher.py --opml-url <your-opml-url>
```

### 命令：列出订阅源中的文章
**操作：** 从指定的 RSS 订阅源获取最近的文章列表。
**语法：**
```
python scripts/rss_fetcher.py --feed-url "<feed_xml_url>" --name "<feed_name>"
```
- **`<feed_xml_url>`**: 指向订阅源 XML 文件的直接 URL。
- **`<feed_name>`**: 订阅源的唯一名称，用于缓存。

### 命令：阅读文章内容
**操作：** 获取特定文章的全部内容。
**语法：**
```
python scripts/rss_fetcher.py --content-url "<article_url>" --title "<article_title>" --author "<article_author>" --date "<publication_date>"
```
- **`<article_url>`**: 要阅读文章的 URL。
- 其他参数用于创建唯一的缓存条目。
