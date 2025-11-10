"""
测试数据加载工具

用于加载 homework_samples 目录下的测试用例数据
"""

import json
from pathlib import Path
from typing import Any, Dict

# 测试数据目录
FIXTURES_DIR = Path(__file__).parent / "homework_samples"


def load_test_case(filename: str) -> Dict[str, Any]:
    """
    加载测试用例

    Args:
        filename: 测试文件名（如 "scenario_1_single_question.json"）

    Returns:
        Dict[str, Any]: 测试用例数据
    """
    filepath = FIXTURES_DIR / filename
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_all_test_cases() -> Dict[str, Dict[str, Any]]:
    """
    获取所有测试用例

    Returns:
        Dict[str, Dict[str, Any]]: 所有测试用例，key 为场景名
    """
    test_cases = {}
    for json_file in FIXTURES_DIR.glob("scenario_*.json"):
        data = load_test_case(json_file.name)
        scenario = data.get("scenario", json_file.stem)
        test_cases[scenario] = data
    return test_cases


# 场景名称常量
SCENARIO_SINGLE_QUESTION = "scenario_1_single_question.json"
SCENARIO_ALL_WRONG = "scenario_2_all_wrong.json"
SCENARIO_ALL_CORRECT = "scenario_3_all_correct.json"
SCENARIO_PARTIAL_UNANSWERED = "scenario_4_partial_unanswered.json"
SCENARIO_MIXED_TYPES = "scenario_5_mixed_types.json"
