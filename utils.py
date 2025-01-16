import re
from urllib.parse import urlparse
import copy


def match_code_language(lang_name):
    """
    Match input language name to Notion's supported code block languages.
    Handles common abbreviations and aliases, falling back to 'plain text' if no match found.

    Args:
        lang_name (str): Input language name to match

    Returns:
        str: Matched Notion-supported language name or 'plain text' if no match
    """
    # Normalize input
    if not lang_name:
        return 'plain text'

    lang_name = str(lang_name).lower().strip()

    # Common abbreviations/aliases mapping
    aliases = {
        'js': 'javascript',
        'ts': 'typescript',
        'py': 'python',
        'rb': 'ruby',
        'sh': 'shell',
        'bash': 'shell',
        'zsh': 'shell',
        'cpp': 'c++',
        'csharp': 'c#',
        'jsx': 'javascript',
        'tsx': 'typescript',
        'yml': 'yaml',
        'htm': 'html',
        'markdown': 'markdown',
        'md': 'markdown',
        'vb': 'visual basic',
        'stylus': 'css',
        'sass': 'scss',
        'golang': 'go',
        'plaintext': 'plain text',
        'txt': 'plain text'
    }

    # Notion supported languages
    supported_languages = {
        'abap', 'arduino', 'bash', 'basic', 'c', 'clojure', 'coffeescript',
        'c++', 'c#', 'css', 'dart', 'diff', 'docker', 'elixir', 'elm',
        'erlang', 'flow', 'fortran', 'f#', 'gherkin', 'glsl', 'go',
        'graphql', 'groovy', 'haskell', 'html', 'java', 'javascript',
        'json', 'julia', 'kotlin', 'latex', 'less', 'lisp', 'livescript',
        'lua', 'makefile', 'markdown', 'markup', 'matlab', 'mermaid', 'nix',
        'objective-c', 'ocaml', 'pascal', 'perl', 'php', 'plain text',
        'powershell', 'prolog', 'protobuf', 'python', 'r', 'reason',
        'ruby', 'rust', 'sass', 'scala', 'scheme', 'scss', 'shell', 'sql',
        'swift', 'typescript', 'vb.net', 'verilog', 'vhdl', 'visual basic',
        'webassembly', 'xml', 'yaml', 'java/c/c++/c#'
    }

    # Try to match alias first
    normalized_lang = aliases.get(lang_name, lang_name)

    # Return matched language or fallback to plain text
    return normalized_lang if normalized_lang in supported_languages else 'plain text'


def convert_to_nested_list(flat_list):
    # 存储最终的嵌套结构
    nested_list = []
    # 用于追踪当前层级的节点
    stack = []

    for li in flat_list:
        # 创建一个新的节点
        node = copy.deepcopy(li)

        node_type = node['type']

        # 如果栈不为空，且当前节点的level大于栈顶的节点的level
        while stack and stack[-1]['level'] >= node['level']:
            stack.pop()

        # 如果栈为空，说明当前节点是一个根节点
        if stack:
            # 把当前节点添加为栈顶节点的子节点
            stack[-1][node_type]['children'].append(node)
        else:
            # 当前节点是根节点，直接加入到nested_list
            nested_list.append(node)

        # 把当前节点压入栈中
        stack.append(node)

    return nested_list


def is_valid_url(link_url):
    """
    判断链接是否有效
    :param link_url: str, 待验证的链接
    :return: bool, 链接是否有效
    """
    # 检查 URL 格式
    regex = re.compile(
        r'^(https?:\/\/)?'  # 可选的协议部分（http 或 https）
        r'(www\.)?'  # 可选的 www 部分
        r'([a-zA-Z0-9-_]+\.)+'  # 域名部分
        r'[a-zA-Z]{2,}'  # 顶级域名
        r'(:\d+)?'  # 可选的端口号
        r'(\/.*)?$',  # 可选的路径部分
        re.IGNORECASE
    )
    if not regex.match(link_url):
        return False

    # 尝试解析 URL，验证域名是否有效
    parsed_url = urlparse(link_url if link_url.startswith(('http://', 'https://')) else f'http://{link_url}')
    return bool(parsed_url.netloc) and bool(parsed_url.scheme)
