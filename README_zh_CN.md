# Notion Markdown 上传工具

这是一个将本地 Markdown 文件批量上传到 Notion 的工具。它能够保留 Markdown 的格式，并支持文件夹结构的递归上传。

## 功能特点

- 支持递归上传整个文件夹结构到 Notion
- 保留 Markdown 格式（标题、列表、代码块、表格等）
- 支持断点续传，避免重复上传
- 详细的日志记录和错误处理
- 可配置的上传选项（是否上传空文件/文件夹、遇错是否停止等）

## 支持的 Markdown 元素

- 标题（H1-H3）
- 段落文本
- 粗体、斜体、删除线
- 代码块（支持语法高亮）
- 引用块
- 有序列表和无序列表（支持嵌套）
- 待办事项列表（[ ] 和 [x]）
- 分割线
- 链接和图片
- 表格

## 安装

1. 克隆仓库

```bash
git clone https://github.com/13Cohen/batch-markdown-to-notion.git
cd batch-markdown-to-notion
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

创建 `.env` 文件，包含以下内容：

```
NOTION_AUTH_TOKEN=your_notion_integration_token
MARKDOWN_ROOT_FOLDER=path/to/your/markdown/folder
NOTION_ROOT_PAGE_ID=your_notion_page_id
```

### 获取 Notion 集成令牌

1. 访问 [Notion Integrations](https://www.notion.so/my-integrations)
2. 创建新的集成
3. 复制生成的令牌

### 获取 Notion 页面 ID

页面 ID 是 Notion 页面 URL 中的一部分，例如：
`https://www.notion.so/myworkspace/Page-Name-1577b80996fa80c48244e3a8bf123f43`
其中 `1577b80996fa80c48244e3a8bf123f43` 就是页面 ID。

## 使用方法

### 基本用法

```bash
python main.py
```

### 测试模式

```bash
python test.py
```

## 配置选项

在 `main.py` 中可以修改以下选项：

```python
options = {
    "stop_when_error": True,  # 遇到错误时是否停止上传
    "if_add_empty_page": False,  # 是否上传空的 Markdown 文件
    "if_add_empty_folder": False  # 是否创建空文件夹
}
```

## 日志和错误处理

- 上传日志保存在 `upload_logs.json`
- 错误日志保存在 `upload_errors.json`
- 出错的文件会被复制到 `error_folder` 目录

## 断点续传

工具会记录已上传的文件和文件夹，再次运行时会自动跳过这些内容，实现断点续传。

## 重试失败的上传

可以通过取消注释 `main.py` 中的以下代码来重试失败的上传：

```python
# uploader.retry_failed_uploads()
```

## 注意事项

- Notion API 有速率限制，大量文件上传可能需要较长时间
- 图片需要是网络图片链接，本地图片路径会被转换为文本
- 部分复杂的 Markdown 格式可能无法完全保留

## 贡献

欢迎提交 Pull Request 或创建 Issue 来改进这个工具。
