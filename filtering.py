import os
import re

def filter_text(input_dir, output_file, max_chars=2000):
    with open(output_file, 'w', encoding='utf-8') as f_out:
        for root, _, files in os.walk(input_dir):
            for file in files:
                if not file.endswith('.txt'):
                    continue
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f_in:
                    text = f_in.read()
                    # 記事冒頭のみ（最初の段落など）
                    lines = text.split('\n')
                    content_lines = []
                    for line in lines:
                        if line.strip() and not line.startswith('<'):
                            content_lines.append(line)
                    content = '\n'.join(content_lines[:max_chars])  # 先頭2000文字程度
                    if len(content) > 50:  # 短すぎる文を除外
                        f_out.write(content + '\n\n')

filter_text('extracted_text', 'filtered_wiki.txt')