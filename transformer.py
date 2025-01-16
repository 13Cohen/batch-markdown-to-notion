import copy
from urllib.parse import unquote

from markdown_it import MarkdownIt
from markdown_it.token import Token
from notion_client import Client

from utils import match_code_language, convert_to_nested_list, is_valid_url


def create_notion_block(block_type, rich_text_list, chidren_list):
    return {
        "object": "block",
        "type": block_type,
        block_type: {
            "rich_text": rich_text_list,
            "children": chidren_list
        }
    }

def transform_invalid_link_and_image(token):
    token_children = []
    invalid_link_flag = False
    invalid_link_href = ''
    invalid_link_content = ''
    for child in token.children or []:
        if child.type == 'link_open' and not is_valid_url(child.attrs['href']):
            # invalid link url
            invalid_link_flag = True
            invalid_link_href = unquote(child.attrs['href'])
        elif child.type == 'link_close' and invalid_link_flag == True:
            invalid_link_flag = False
            token_children.append(Token(
                type='text',
                tag='',
                nesting=0,
                attrs={},
                map=None,
                level=token.level,
                children=None,
                content=f"[{invalid_link_content}]({invalid_link_href})",
                markup='',
                info='',
                meta={},
                block=token.block,
                hidden=token.hidden
            ))
        elif invalid_link_flag == True and child.type == 'text':
            invalid_link_content += child.content
        elif child.type == 'image' and not child.attrs['src'].startswith('http'):
            # invalid image url
            invalid_img_url = unquote(child.attrs['src'])
            invalid_img_alt = child.attrs['alt']
            invalid_img_caption = child.content
            token_children.append(Token(
                type='text',
                tag='',
                nesting=0,
                attrs={},
                map=None,
                level=token.level,
                children=None,
                content=f"![{invalid_img_caption}]({invalid_img_url})",
                markup='',
                info='',
                meta={},
                block=token.block,
                hidden=token.hidden
            ))
        else:
            token_children.append(child)
    token.children = token_children
    return token

def process_inline_content(token):
    """Process inline content and return rich text array"""

    token = transform_invalid_link_and_image(token)

    rich_texts = []
    chidren_list = []

    stack = []
    for child in token.children or []:
        # print("child",child)

        # image 需要 放在 children 中，不能放在 rich_texts
        if child.type == 'image':
            image_url = child.attrs['src']
            image_alt = child.attrs['alt']
            image_caption = child.content
            text_content = {
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {
                        "url": image_url
                    }
                },
            }
            chidren_list.append(text_content)
            # 直接跳过
            continue

        elif child.type == 'bulleted_list_item' or child.type == 'numbered_list_item':
            chidren_list.append(child)
            # 直接跳过
            continue

        text_content = {
            "type": "text",
            "text": {
                "content": ''
            },
            "annotations": {
                "bold": False,
                "italic": False,
                "code": False,
                "strikethrough": False
            }
        } if len(stack) == 0 else stack[-1]

        if child.type == 'text':
            text_content["text"]["content"] += child.content

        elif child.type == 'html_inline':
            text_content["text"]["content"] += child.content

        elif child.type == 's_open':
            text_content["annotations"]["strikethrough"] = True
            text_content["annotations"]["color"] = "gray"

        elif child.type == 'strong_open':
            text_content["annotations"]["bold"] = True

        elif child.type == 'em_open':
            text_content["annotations"]["italic"] = True

        elif child.type == 'code_inline':
            text_content["text"]["content"] += child.content
            text_content["annotations"]["code"] = True

        elif child.type == 'link_open':
            link_url = child.attrs['href']
            text_content["text"]["link"] = {
                "url": link_url
            }
            text_content["href"] = link_url

        elif child.type == 'hardbreak':
            if rich_texts:
                rich_texts[-1]["text"]["content"] += "\n"

        elif child.type == 'softbreak':
            if rich_texts:
                rich_texts[-1]["text"]["content"] += "\n"

        elif not child.type.endswith('_close'):
            print("Unknown child type:", child.type)
            print(token)
            print(child)

        if child.type.endswith('_open'):
            if len(stack) == 0:
                stack.append(text_content)
            else:
                stack[-1] = text_content
        elif child.type.endswith('_close'):
            if stack:
                rich_texts.append(stack.pop())
        elif len(stack) == 0:
            rich_texts.append(text_content)
        else:
            stack[-1] = text_content

    return rich_texts, chidren_list


def handleHeading(block_data):
    blocks = []
    level = int(block_data[0].tag[-1])
    # 目前只支持 h1 - h3
    level = min(3, level)
    block_type = f"heading_{level}"
    for token in block_data:
        if token.type == 'inline':
            rich_texts, chidren_list = process_inline_content(token)
            current_block = create_notion_block(block_type, rich_texts, chidren_list)
            blocks.append(current_block)
    return blocks


def handleParagraph(block_data):
    # print(block_data)
    blocks = []
    for token in block_data:
        if token.type == 'inline':
            rich_texts, chidren_list = process_inline_content(token)
            current_block = create_notion_block('paragraph', rich_texts, chidren_list)
            blocks.append(current_block)
    return blocks


def handleFence(block_data):
    blocks = []
    for token in block_data:
        code_content = token.content.strip()
        code_lang = token.info.strip()
        # text.content.length should be ≤ `2000`
        if len(code_content) > 2000:
            # 切割 code_content 成多个 item，放到 rich_text
            rich_text_items = []
            for i in range(0, len(code_content), 2000):
                rich_text_items.append({
                    "type": "text",
                    "text": {
                        "content": code_content[i:i + 2000]
                    }
                })
            current_block = {
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": rich_text_items,
                    "language": match_code_language(code_lang)
                }
            }
        else:
            current_block = {
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{
                        "type": "text",
                        "text": {
                            "content": code_content
                        }
                    }],
                    "language": match_code_language(code_lang)
                }
            }
        blocks.append(current_block)
    return blocks


def handleBlockquote(block_data):
    # print(block_data)
    blocks = []
    for token in block_data:
        # print(token)
        if token.type == 'inline':
            rich_texts, chidren_list = process_inline_content(token)
            current_block = create_notion_block('quote', rich_texts, chidren_list)
            blocks.append(current_block)
    return blocks


# 删除 level 属性，删除 空的[type]['children']
def handleNotionErrorKey(nested_list):
    for li in nested_list:
        li_type = li['type']
        if li[li_type].get('children', None):
            if not len(li[li_type]['children']):
                li[li_type].pop('children')
            else:
                handleNotionErrorKey(li[li_type]['children'])

        li.pop('level', None)

    return nested_list


def handleListItem(block_data, list_type):
    # print(block_data)
    blocks = []
    level = 0
    for token in block_data:
        # print(token)
        if token.type == 'list_item_open':
            level = token.level

        # 遇到 inline
        if token.type == 'inline':
            rich_texts, chidren_list = process_inline_content(token)
            current_block = create_notion_block(list_type, rich_texts, chidren_list)
            current_block['level'] = level  # 添加 level 作为层级标记
            blocks.append(current_block)

    # 将平铺的 li 转为嵌套的 li
    nested_list = convert_to_nested_list(copy.deepcopy(blocks))

    # 遍历 nested_list 及其 children, 删除元素的 level 属性，和空的 children 不然 notion API 会报错
    return handleNotionErrorKey(nested_list)


def convert2TodoList(block):
    unchecked_prefix_list = ['[] ', '[ ] ']
    checked_prefix_list = ['[x] ', '[X] ', '[ x ] ', '[ X ] ']

    if block['type'] != 'bulleted_list_item':
        return block
    current_content = block['bulleted_list_item']['rich_text'][0]['text']['content']

    is_to_do = False
    for prefix in unchecked_prefix_list + checked_prefix_list:
        if current_content.startswith(prefix):
            is_to_do = True
            block['type'] = 'to_do'
            block['to_do'] = block['bulleted_list_item']
            del block['bulleted_list_item']
            block['to_do']['checked'] = prefix in checked_prefix_list
            block['to_do']['rich_text'][0]['text']['content'] = current_content.removeprefix(prefix)

    current_item = block['to_do'] if is_to_do else block['bulleted_list_item']
    if 'children' in current_item and len(current_item['children']):
        for child in current_item['children']:
            convert2TodoList(child)

    return block


def handleBulletList(block_data):
    bulletList = handleListItem(copy.deepcopy(block_data), 'bulleted_list_item')

    new_list = []
    for item in bulletList:
        # 遍历 bulletList 及其 children，如果 item 以[]/[ ]/[x]/[X]/[ x ]/[ X ]+空格开头，则将 item 转为 to_do
        new_list.append(convert2TodoList(item))

    return new_list


def handleOrderedList(block_data):
    return handleListItem(copy.deepcopy(block_data), 'numbered_list_item')


def handleDivider(block_data):
    blocks = []
    for token in block_data:
        current_block = {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
        blocks.append(current_block)
    return blocks


def handleTable(tokens):
    notion_table = {
        "object": "block",
        "type": "table",
        "table": {
            "table_width": 0,
            "has_column_header": False,
            "children": []
        }
    }

    current_row = None
    header_processed = False

    for token in tokens:
        if token.type == 'thead_open':
            notion_table["table"]["has_column_header"] = True

        elif token.type in ('td_open', 'th_open'):
            if current_row is None:
                current_row = {
                    "object": "block",
                    "type": "table_row",
                    "table_row": {
                        "cells": []
                    }
                }

        elif token.type == 'inline':
            if current_row is not None:
                # 现在每个单元格包含一个rich text对象数组
                cell = [{
                    "type": "text",
                    "text": {
                        "content": token.content
                    }
                }]
                current_row["table_row"]["cells"].append(cell)

        elif token.type in ('tr_close'):
            if current_row is not None:
                notion_table["table"]["children"].append(current_row)
                # Set table width based on first row
                if not header_processed:
                    notion_table["table"]["table_width"] = len(current_row["table_row"]["cells"])
                    header_processed = True
                current_row = None

    return [notion_table]


def handleHtmlBlock(block_data):
    blocks = []
    for token in block_data:
        current_block = {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{
                    "type": "text",
                    "text": {
                        "content": token.content.strip()
                    }
                }],
                "language": "html"
            }
        }
        blocks.append(current_block)
    return blocks


def markdown_element_to_notion_object(md_text):
    # [xx]::xxx 会被错误识别成 link,在 ]:: 添加一个空格即可
    md_text = md_text.replace(']::', ']:: ')
    md = MarkdownIt("commonmark").enable('table').enable('strikethrough')

    tokens = md.parse(md_text)

    # 遍历预处理 tokens, 通过 type 划分块数据
    block_data_list = []
    temp_list = []
    tag_count = 0
    for token in tokens:
        temp_list.append(token)
        if token.type.endswith('_open'):
            tag_count += 1
        elif token.type.endswith('_close'):
            tag_count -= 1
        if not temp_list[0].type.endswith('_open') or (
                tag_count == 0 and token.type.endswith('_close') and temp_list[0].type.removesuffix(
            '_open') == token.type.removesuffix('_close')):
            # 可以结束temp_list
            block_data_list.append(temp_list)
            temp_list = []

    # 空行
    empty_row = {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": []
        }
    }
    notion_blocks = []
    for block_data in block_data_list:
        token_type = block_data[0].type
        notion_blocks_data = None
        if token_type == 'heading_open':
            notion_blocks_data = handleHeading(block_data)
        elif token_type == 'paragraph_open':
            notion_blocks_data = handleParagraph(block_data)
        elif token_type == 'fence':
            notion_blocks_data = handleFence(block_data)
        elif token_type == 'blockquote_open':
            notion_blocks_data = handleBlockquote(block_data)
        elif token_type == 'bullet_list_open':
            notion_blocks_data = handleBulletList(block_data)
        elif token_type == 'ordered_list_open':
            notion_blocks_data = handleOrderedList(block_data)
        elif token_type == 'hr':
            notion_blocks_data = handleDivider(block_data)
        elif token_type == 'table_open':
            notion_blocks_data = handleTable(block_data)
        elif token_type == 'html_block':
            notion_blocks_data = handleHtmlBlock(block_data)
        else:
            print(f"未处理的 token 类型：{token_type}")
            print(block_data)

        if notion_blocks_data:
            notion_blocks.extend(notion_blocks_data)
            # 除了段落和标题，其他类型都添加空行
            if token_type not in ('paragraph_open', 'heading_open'):
                notion_blocks.append(empty_row)

    return notion_blocks


def test_markdown_transformation():
    """
    Test the markdown transformation with various Markdown elements.
    """
    test_markdown = """以下是一段包含各种 Markdown 格式的示例文本：

# 一级标题

## 二级标题

### 三级标题

**粗体**

*斜体*

这是**粗体**文本，这是*斜体*文本，这是***粗斜体***文本。

这是`行内代码`。

以下是代码块：
```python
def hello_world():
    print("Hello, World!")
    
    print("Hello, World!")
```

> 这是一段引用文本
> 可以有多行

- 这是**无序**列表1
- 无序列表2
  - 二级无序*列表项*
    - 三级无序列表项
    - [ ] 发布新版本
    - [x] 发布新版本

1. 这是有序列表1
    1. 列表项(1.1)
        1. 列表项（1.1.1）
2. 这是有序列表2
    1. 列表项（2.1）
    2. 列表项（2.2）

---

[这是链接](https://example.com)

![一个示例图片](https://www.example.com/image.jpg)

这是~~删除线~~文本

这是表格：

| 列1 | 列2 |
|-----|-----|
| 内容1 | 内容2 |

-----

| Name   | Age |
|--------|-----|
| Alice  | 30  |
| Bob    | 25  |

"""

    result = markdown_element_to_notion_object(test_markdown)

    # 用户输入y 创建一个新页面，
    user_input = input("Press y to create a new page (y/n) : ")
    if user_input.lower() == "y":
        notion = Client(auth="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")
        notion_root_page_id = "1577b80996fa80c48244e3a8bf123f43"
        notion.pages.create(
            parent={"page_id": notion_root_page_id},
            properties={"title": [{"text": {"content": 'new test'}}]},
            children=result
        )


if __name__ == "__main__":
    test_markdown_transformation()
