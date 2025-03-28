[English](README.md) | [中文](README_zh_CN.md) 

# Notion Markdown Uploader

A tool for batch uploading local Markdown files to Notion while preserving formatting and supporting recursive folder structure uploads.

## Features

- Recursively upload entire folder structures to Notion
- Preserve Markdown formatting (headings, lists, code blocks, tables, etc.)
- Support for resumable uploads to avoid duplication
- Detailed logging and error handling
- Configurable upload options (whether to upload empty files/folders, stop on error, etc.)

## Supported Markdown Elements

- Headings (H1-H3)
- Paragraph text
- Bold, italic, strikethrough
- Code blocks (with syntax highlighting)
- Quote blocks
- Ordered and unordered lists (with nesting)
- To-do lists ([ ] and [x])
- Horizontal rules
- Links and images
- Tables

## Installation

1. Clone the repository

```bash
git clone https://github.com/13Cohen/batch-markdown-to-notion.git
cd batch-markdown-to-notion
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file with the following content:

```
NOTION_AUTH_TOKEN=your_notion_integration_token
MARKDOWN_ROOT_FOLDER=path/to/your/markdown/folder
NOTION_ROOT_PAGE_ID=your_notion_page_id
```

### Getting a Notion Integration Token

1. Visit [Notion Integrations](https://www.notion.so/my-integrations)
2. Create a new integration
3. Copy the generated token

### Getting a Notion Page ID

The page ID is part of the Notion page URL, for example:
`https://www.notion.so/myworkspace/Page-Name-1577b80996fa80c48244e3a8bf123f43`
where `1577b80996fa80c48244e3a8bf123f43` is the page ID.

## Usage

### Basic Usage

```bash
python main.py
```

### Test Mode

```bash
python test.py
```

## Configuration Options

You can modify the following options in `main.py`:

```python
options = {
    "stop_when_error": True,  # Whether to stop uploading when an error occurs
    "if_add_empty_page": False,  # Whether to upload empty Markdown files
    "if_add_empty_folder": False  # Whether to create empty folders
}
```

## Logging and Error Handling

- Upload logs are saved in `upload_logs.json`
- Error logs are saved in `upload_errors.json`
- Files with errors are copied to the `error_folder` directory

## Resumable Uploads

The tool records uploaded files and folders, automatically skipping them on subsequent runs to implement resumable uploads.

## Retrying Failed Uploads

You can retry failed uploads by uncommenting the following code in `main.py`:

```python
# uploader.retry_failed_uploads()
```

## Notes

- Notion API has rate limits, so uploading a large number of files may take time
- Images need to be web image links; local image paths will be converted to text
- Some complex Markdown formatting may not be fully preserved

## Contributing

Pull requests and issues are welcome to improve this tool.
