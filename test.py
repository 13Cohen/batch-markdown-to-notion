import os

from main import NotionUploader
from dotenv import load_dotenv


def main():
    # 加载 .env.test 文件
    load_dotenv('.env.test')

    auth_token = os.getenv("NOTION_AUTH_TOKEN")
    markdown_root_folder = os.getenv("MARKDOWN_ROOT_FOLDER")
    notion_root_page_id = os.getenv("NOTION_ROOT_PAGE_ID")

    options = {
        "stop_when_error": True,
        "if_add_empty_page": False,
        "if_add_empty_folder": False
    }

    logs_file = "test_logs.json"
    error_file = "test_errors.json"

    # 删除 errors.json
    if os.path.exists(error_file):
        os.remove(error_file)

    # 删除 logs.json
    if os.path.exists(logs_file):
        os.remove(logs_file)

    uploader = NotionUploader(auth_token,options,logs_file,error_file)

    uploader.upload_folder_to_notion(markdown_root_folder, notion_root_page_id)

    # 如果需要重试失败的上传，取消下面的注释
    # uploader.retry_failed_uploads()


if __name__ == "__main__":
    main()