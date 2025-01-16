import os
import json
import hashlib
import shutil

from dotenv import load_dotenv

from notion_client import Client

from transformer import markdown_element_to_notion_object
from datetime import datetime
from enum import Enum
from rich.console import Console

console = Console(force_terminal=True)


class UploadStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"


class NotionUploader:
    def __init__(self, auth_token, options=None, logs_file="upload_logs.json", error_file="upload_errors.json"):
        self.notion = Client(auth=auth_token)
        self.logs_file = logs_file
        self.error_file = error_file
        self.logs = self.load_logs()
        self.errors = self.load_errors()
        if options is None:
            self.options = {
                "stop_when_error": False,
                "if_add_empty_page": True,
                "if_add_empty_folder": True
            }
        else:
            self.options = options

    def generate_item_hash(self, path, parent_page_id):
        """生成目录或文件的跨平台唯一标识"""
        # 使用路径和父页面ID来生成唯一标识
        content = f"{path}:{parent_page_id}".encode('utf-8')
        return hashlib.sha256(content).hexdigest()

    def load_logs(self):
        """加载上传日志"""
        if os.path.exists(self.logs_file):
            with open(self.logs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def load_errors(self):
        """加载错误日志"""
        if os.path.exists(self.error_file):
            with open(self.error_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_logs(self):
        """保存上传日志"""
        with open(self.logs_file, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, ensure_ascii=False, indent=2)

    def save_errors(self):
        """保存错误日志"""
        with open(self.error_file, 'w', encoding='utf-8') as f:
            json.dump(self.errors, f, ensure_ascii=False, indent=2)

    def add_log_entry(self, item_hash, log_entry):
        """添加日志记录"""
        if item_hash not in self.logs:
            self.logs[item_hash] = {
                "logs": [],
                "latest_status": None
            }

        self.logs[item_hash]["logs"].append(log_entry)
        self.logs[item_hash]["latest_status"] = log_entry["status"]
        self.save_logs()

    def add_error_entry(self, item_hash, error_entry):
        """添加错误记录"""
        if item_hash not in self.errors:
            self.errors[item_hash] = {
                "logs": [],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        self.errors[item_hash]["logs"].append(error_entry)
        self.save_errors()

    def create_log_entry(self, path, parent_page_id, page_id, title, status):
        """创建日志记录"""
        return {
            "path": path,
            "parent_page_id": parent_page_id,
            "page_id": page_id,
            "title": title,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": status.value
        }

    def create_error_entry(self, path, parent_page_id, title, error_msg, notion_objects=None):
        """创建错误记录"""
        return {
            "path": path,
            "parent_page_id": parent_page_id,
            "title": title,
            "error": str(error_msg),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "notion_objects": notion_objects
        }

    def if_continue_when_error(self, stop_when_error):
        if stop_when_error:
            # 等待用户输入，是否继续 y/n
            user_input = input("是否继续上传其他文件?(y/n)")
            if user_input == "y":
                return True
            else:
                exit("上传中止")
        else:
            return True

    def is_empty_folder(self, folder_path):
        # 如果里面没有文件夹,也没有 .md 文件，返回 True
        if not os.listdir(folder_path):
            return True
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                # 递归处理子文件夹
                if not self.is_empty_folder(item_path):
                    return False
            if item.endswith(".md"):
                return False
        return True

    def copy_to_error_folder(self, item_path):
        # 把出错的文件或者文件夹，拷贝到指定的文件夹中
        error_folder = "error_folder"
        if not os.path.exists(error_folder):
            os.makedirs(error_folder)
        shutil.copy(item_path, error_folder)


    def upload_folder_to_notion(self, folder_path, parent_page_id):

        # 如果 if_add_empty_folder = False 且 当前文件夹为空，跳过
        if not self.options["if_add_empty_folder"] and self.is_empty_folder(folder_path):
            console.print(f"【跳过】【空文件夹】{folder_path}", style="blue")
            return

        """上传文件夹到Notion，包含增强的日志功能"""
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            item_hash = self.generate_item_hash(item_path, parent_page_id)

            # 如果 已经上传过 则跳过
            if item_hash in self.logs and self.logs[item_hash]["latest_status"] == UploadStatus.SUCCESS.value:
                if os.path.isdir(item_path):
                    console.print(f"【跳过】【文件夹】{item_path}", style="yellow")
                    # 递归处理子文件夹
                    page_id = self.logs[item_hash]["logs"][-1]["page_id"]
                    self.upload_folder_to_notion(item_path, page_id)
                else:
                    console.print(f"【跳过】【文件】{item_path}", style="yellow")
                continue

            if os.path.isdir(item_path):
                # 如果 if_add_empty_folder = False 且 当前文件夹为空，跳过
                if not self.options["if_add_empty_folder"] and self.is_empty_folder(item_path):
                    console.print(f"【跳过】【空文件夹】{item_path}", style="blue")
                    continue

                try:
                    # 创建进行中状态的日志
                    log_entry = self.create_log_entry(
                        item_path, parent_page_id, None, item, UploadStatus.IN_PROGRESS
                    )
                    self.add_log_entry(item_hash, log_entry)

                    # 在Notion中创建新页面作为文件夹的表示
                    new_page = self.notion.pages.create(
                        parent={"page_id": parent_page_id},
                        properties={"title": [{"text": {"content": item}}]}
                    )

                    # 更新成功状态的日志
                    log_entry = self.create_log_entry(
                        item_path, parent_page_id, new_page["id"], item, UploadStatus.SUCCESS
                    )
                    self.add_log_entry(item_hash, log_entry)
                    console.print(f"【成功】【文件夹】{item_path}", style="green")

                    # 递归处理子文件夹
                    self.upload_folder_to_notion(item_path, new_page["id"])

                except Exception as e:
                    # 记录失败状态
                    log_entry = self.create_log_entry(
                        item_path, parent_page_id, None, item, UploadStatus.FAILED
                    )
                    self.add_log_entry(item_hash, log_entry)

                    # 记录错误详情
                    error_entry = self.create_error_entry(
                        item_path, parent_page_id, item, str(e)
                    )
                    self.add_error_entry(item_hash, error_entry)
                    console.print(f"【错误】【文件夹】{item_path}", style="red")
                    self.copy_to_error_folder(item_path)
                    self.if_continue_when_error(self.options["stop_when_error"])

            elif item.endswith(".md"):
                try:
                    # 记录进行中状态
                    log_entry = self.create_log_entry(
                        item_path, parent_page_id, None, item, UploadStatus.IN_PROGRESS
                    )
                    self.add_log_entry(item_hash, log_entry)

                    # 读取Markdown文件内容
                    with open(item_path, "r", encoding="utf-8") as md_file:
                        md_content = md_file.read()

                    # 如果 if_add_empty_page = False 且 当前文件为空，跳过
                    if not self.options["if_add_empty_page"] and md_content.strip() == "":
                        console.print(f"【跳过】【空文件】{item_path}", style="blue")
                        continue

                    notion_objects = markdown_element_to_notion_object(md_content)

                    if len(notion_objects) <= 100:
                        new_page = self.notion.pages.create(
                            parent={"page_id": parent_page_id},
                            properties={"title": [{"text": {"content": item}}]},
                            children=notion_objects
                        )
                    else:
                        # body.children.length should be ≤ `100`，一次上传不超过100个对象，超过100分批次上传
                        # 将 notion_objects 分为多个列表，每个列表长度不超过 100
                        notion_objects_list = [notion_objects[i:i + 100] for i in range(0, len(notion_objects), 100)]

                        new_page = self.notion.pages.create(
                            parent={"page_id": parent_page_id},
                            properties={"title": [{"text": {"content": item}}]}
                        )
                        for index, notion_objects_item in enumerate(notion_objects_list):
                            self.notion.blocks.children.append(
                                block_id=new_page["id"],
                                children=notion_objects_item
                            )

                    # 更新成功状态
                    log_entry = self.create_log_entry(
                        item_path, parent_page_id, new_page["id"], item, UploadStatus.SUCCESS
                    )
                    self.add_log_entry(item_hash, log_entry)
                    console.print(f"【成功】【文件】{item_path}", style="green")

                except Exception as e:
                    # 记录失败状态
                    log_entry = self.create_log_entry(
                        item_path, parent_page_id, None, item, UploadStatus.FAILED
                    )
                    self.add_log_entry(item_hash, log_entry)

                    # 记录错误详情
                    error_entry = self.create_error_entry(
                        item_path, parent_page_id, item, str(e), notion_objects
                    )
                    self.add_error_entry(item_hash, error_entry)
                    console.print(f"【错误】【文件】{item_path}", style="red")
                    self.copy_to_error_folder(item_path)
                    self.if_continue_when_error(self.options["stop_when_error"])

    def retry_failed_uploads(self):
        """重试失败的上传"""
        failed_items = [
            item_hash for item_hash, data in self.logs.items()
            if data["latest_status"] == UploadStatus.FAILED.value
        ]

        for item_hash in failed_items:
            path = self.logs[item_hash]["logs"][-1]["path"]
            parent_page_id = self.logs[item_hash]["logs"][-1]["parent_page_id"]

            console.print(f"重试上传: {path}", style="yellow")
            if os.path.exists(path):
                self.upload_folder_to_notion(os.path.dirname(path), parent_page_id)


def main():
    # 加载 .env 文件
    load_dotenv()

    auth_token = os.getenv("NOTION_AUTH_TOKEN")
    markdown_root_folder = os.getenv("MARKDOWN_ROOT_FOLDER")
    notion_root_page_id = os.getenv("NOTION_ROOT_PAGE_ID")

    options = {
        "stop_when_error": True,
        "if_add_empty_page": False,
        "if_add_empty_folder": False
    }

    uploader = NotionUploader(auth_token, options)
    uploader.upload_folder_to_notion(markdown_root_folder, notion_root_page_id)

    # 如果需要重试失败的上传，取消下面的注释
    # uploader.retry_failed_uploads()


if __name__ == "__main__":
    main()
