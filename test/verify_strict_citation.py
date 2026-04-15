#!/usr/bin/env python3
"""
Strict Citation 代码修改验证脚本
直接检查文件修改是否正确
"""

import os
import re

def check_file_contains(file_path, patterns, description):
    """检查文件是否包含指定模式"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        failures = []
        for pattern in patterns:
            if isinstance(pattern, tuple):
                name, regex = pattern
                if not re.search(regex, content):
                    failures.append(name)

        if failures:
            print(f"[FAIL] {description}: 缺少 {failures}")
            return False
        else:
            print(f"[PASS] {description}")
            return True
    except Exception as e:
        print(f"[ERROR] {description}: {e}")
        return False

def main():
    base_dir = r"C:\Users\wing\Documents\Wing\emto\2026\2026.4\ragflow\ragflow"

    results = []

    print("=" * 60)
    print("Strict Citation 代码修改验证")
    print("=" * 60)

    # 1. 检查 strict_citation_system.md
    results.append(check_file_contains(
        os.path.join(base_dir, "rag", "prompts", "strict_citation_system.md"),
        [
            ("只引用原文规则", r"ONLY cite content that exists"),
            ("无原文回复无法回答", r"根据现有资料无法回答该问题"),
            ("定量数据必须引用", r"定量数据必须引用|All numbers MUST be cited"),
            ("禁止推断", r"DO NOT generate any content not present"),
        ],
        "strict_citation_system.md 模板检查"
    ))

    # 2. 检查 generator.py
    results.append(check_file_contains(
        os.path.join(base_dir, "rag", "prompts", "generator.py"),
        [
            ("STRICT_CITATION_PROMPT_TEMPLATE 导入", r"STRICT_CITATION_PROMPT_TEMPLATE"),
            ("citation_prompt 支持 strict_citation 参数", r"strict_citation\s*:\s*bool\s*=\s*False"),
        ],
        "generator.py 修改检查"
    ))

    # 3. 检查 llm.py
    results.append(check_file_contains(
        os.path.join(base_dir, "agent", "component", "llm.py"),
        [
            ("strict_citation 字段", r"self\.strict_citation\s*=\s*False"),
            ("引用 strict_citation 参数", r"strict_citation\s*=\s*self\._param\.strict_citation"),
        ],
        "llm.py 修改检查"
    ))

    # 4. 检查 dialog_service.py
    results.append(check_file_contains(
        os.path.join(base_dir, "api", "db", "services", "dialog_service.py"),
        [
            ("调用 citation_prompt 传递 strict_citation", r"citation_prompt\(strict_citation\s*="),
        ],
        "dialog_service.py 修改检查"
    ))

    # 5. 检查前端 schema
    results.append(check_file_contains(
        os.path.join(base_dir, "web", "src", "pages", "next-chats", "chat", "app-settings", "use-chat-setting-schema.tsx"),
        [
            ("strict_citation 字段", r"strict_citation:\s*z\.boolean\(\)"),
        ],
        "use-chat-setting-schema.tsx 修改检查"
    ))

    # 6. 检查前端 chat-settings.tsx
    results.append(check_file_contains(
        os.path.join(base_dir, "web", "src", "pages", "next-chats", "chat", "app-settings", "chat-settings.tsx"),
        [
            ("strict_citation 默认值", r"strict_citation:\s*false"),
        ],
        "chat-settings.tsx 修改检查"
    ))

    # 7. 检查前端 chat-prompt-engine.tsx
    results.append(check_file_contains(
        os.path.join(base_dir, "web", "src", "pages", "next-chats", "chat", "app-settings", "chat-prompt-engine.tsx"),
        [
            ("strictCitation 开关控件", r"prompt_config\.strict_citation"),
        ],
        "chat-prompt-engine.tsx 修改检查"
    ))

    # 8. 检查英文 locale
    results.append(check_file_contains(
        os.path.join(base_dir, "web", "src", "locales", "en.ts"),
        [
            ("strictCitation", r"strictCitation:\s*'Strict citation'"),
            ("strictCitationTip", r"strictCitationTip:"),
        ],
        "en.ts 国际化检查"
    ))

    # 9. 检查中文 locale
    results.append(check_file_contains(
        os.path.join(base_dir, "web", "src", "locales", "zh.ts"),
        [
            ("strictCitation", r"strictCitation:\s*'严格原文引用'"),
            ("strictCitationTip", r"strictCitationTip:"),
        ],
        "zh.ts 国际化检查"
    ))

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"验证完成: {passed}/{total} 项通过")
    print("=" * 60)

    return all(results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
