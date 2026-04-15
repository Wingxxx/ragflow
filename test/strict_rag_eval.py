#!/usr/bin/env python3
"""
Strict Citation 功能测试脚本
验证严格原文引用模式是否正常工作
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_citation_prompt_normal_mode():
    """测试正常模式（非严格引用）"""
    from rag.prompts.generator import citation_prompt

    result = citation_prompt(strict_citation=False)

    assert "DO NOT cite content not from" in result or "STRICT MODE" not in result
    print("[PASS] 正常模式 citation_prompt 生成成功")

def test_citation_prompt_strict_mode():
    """测试严格模式"""
    from rag.prompts.generator import citation_prompt

    result = citation_prompt(strict_citation=True)

    assert "ONLY cite content that exists in" in result
    assert "DO NOT generate any content not present" in result
    assert "根据现有资料无法回答该问题" in result
    print("[PASS] 严格模式 citation_prompt 生成成功")

def test_llm_param_has_strict_citation():
    """测试 LLMParam 是否支持 strict_citation"""
    from agent.component.llm import LLMParam

    param = LLMParam()
    assert hasattr(param, 'strict_citation'), "LLMParam 缺少 strict_citation 属性"
    assert param.strict_citation == False, "strict_citation 默认值应为 False"
    print("[PASS] LLMParam.strict_citation 属性存在且默认值正确")

def test_strict_citation_system_prompt_exists():
    """测试严格引用 Prompt 文件是否存在"""
    from rag.prompts.template import load_prompt

    try:
        content = load_prompt("strict_citation_system")
        assert len(content) > 0, "strict_citation_system prompt 为空"
        print("[PASS] strict_citation_system.md 文件存在且非空")
    except FileNotFoundError:
        print("[FAIL] strict_citation_system.md 文件不存在")
        raise

def test_generator_import():
    """测试 generator 模块是否能正常导入"""
    from rag.prompts.generator import (
        citation_prompt,
        STRICT_CITATION_PROMPT_TEMPLATE,
        CITATION_PROMPT_TEMPLATE
    )

    assert CITATION_PROMPT_TEMPLATE is not None
    assert STRICT_CITATION_PROMPT_TEMPLATE is not None
    print("[PASS] generator 模块导入成功")

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始 Strict Citation 功能测试")
    print("=" * 60)

    tests = [
        test_generator_import,
        test_strict_citation_system_prompt_exists,
        test_citation_prompt_normal_mode,
        test_citation_prompt_strict_mode,
        test_llm_param_has_strict_citation,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            print(f"\n[测试] {test.__name__}")
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("=" * 60)

    return failed == 0

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
