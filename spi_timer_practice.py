#!/usr/bin/env python3
"""SPI練習アプリ（非言語・言語・性格）。問題はJSON管理。"""

from __future__ import annotations

import json
import random
import threading
from collections import defaultdict
from pathlib import Path

QUESTION_FILE = Path(__file__).with_name("questions.json")
TIME_LIMITS = {"非言語": 30, "言語": 40, "性格": None}


class QuizError(Exception):
    """クイズ設定時のエラー。"""


def timed_input(prompt: str, timeout: int | None) -> str | None:
    """指定秒数の入力待ち。timeout=Noneの場合は無制限。"""
    if timeout is None:
        try:
            return input(prompt)
        except EOFError:
            return None

    user_input: list[str | None] = [None]

    def _read() -> None:
        try:
            user_input[0] = input(prompt)
        except EOFError:
            user_input[0] = None

    thread = threading.Thread(target=_read, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        return None
    return user_input[0]


def load_questions() -> list[dict]:
    data = json.loads(QUESTION_FILE.read_text(encoding="utf-8"))
    questions = data.get("questions", [])
    if not questions:
        raise QuizError("questions.json に問題が見つかりません。")
    return questions


def choose_from_list(title: str, options: list[str], allow_all: bool = False) -> str:
    """番号入力で選択させる。allow_all=Trueなら0=すべて。"""
    print(f"\n{title}")
    if allow_all:
        print("  0. すべて")
    for idx, option in enumerate(options, start=1):
        print(f"  {idx}. {option}")

    while True:
        raw = input("番号を選択 > ").strip()
        if not raw.isdigit():
            print("数字で入力してください。")
            continue

        number = int(raw)
        if allow_all and number == 0:
            return "すべて"
        if 1 <= number <= len(options):
            return options[number - 1]
        print("選択範囲外です。")


def filter_questions(
    questions: list[dict], mode: str, category: str, difficulty: str
) -> list[dict]:
    filtered = [q for q in questions if q.get("mode") == mode]
    if category != "すべて":
        filtered = [q for q in filtered if q.get("category") == category]
    if difficulty != "すべて":
        filtered = [q for q in filtered if q.get("difficulty") == difficulty]
    return filtered


def ask_question(question: dict, index: int, total: int, mode: str) -> tuple[bool | None, int | None]:
    """1問出題。認知系は正誤、性格は選択スコアを返す。"""
    print(f"\n--- 問題 {index}/{total} ({question['category']}・{question['difficulty']}) ---")
    print(question["prompt"])
    for i, choice in enumerate(question["choices"], start=1):
        print(f"  {i}. {choice}")

    timeout = TIME_LIMITS[mode]
    if timeout is not None:
        print(f"\n制限時間は{timeout}秒です。")
    answer = timed_input("番号で回答してください > ", timeout)

    if answer is None:
        if mode == "性格":
            print("入力がありませんでした。次へ進みます。")
            return None, None
        print("\n⏰ 時間切れです。")
        print(f"正解: {question['answer_index'] + 1}. {question['choices'][question['answer_index']]}")
        print(f"解説:\n{question['explanation']}")
        return False, None

    if not answer.strip().isdigit():
        print("\n⚠️ 数字で入力してください。")
        if mode != "性格":
            print(f"正解: {question['answer_index'] + 1}. {question['choices'][question['answer_index']]}")
            print(f"解説:\n{question['explanation']}")
            return False, None
        return None, None

    selected = int(answer) - 1
    if selected < 0 or selected >= len(question["choices"]):
        print("\n⚠️ 選択肢の範囲外です。")
        if mode != "性格":
            print(f"正解: {question['answer_index'] + 1}. {question['choices'][question['answer_index']]}")
            print(f"解説:\n{question['explanation']}")
            return False, None
        return None, None

    if mode == "性格":
        score = 4 - selected
        return None, score

    is_correct = selected == question["answer_index"]
    print("\n✅ 正解！" if is_correct else "\n❌ 不正解。")
    print(f"正解: {question['answer_index'] + 1}. {question['choices'][question['answer_index']]}")
    print(f"解説:\n{question['explanation']}")
    return is_correct, None


def summarize_personality(records: list[tuple[str, int]]) -> None:
    if not records:
        print("\n回答データがないため、傾向を表示できません。")
        return

    grouped: dict[str, list[int]] = defaultdict(list)
    for trait, score in records:
        grouped[trait].append(score)

    print("\n=== 性格検査サマリー ===")
    overall = sum(score for _, score in records) / len(records)
    for trait, scores in grouped.items():
        avg = sum(scores) / len(scores)
        if avg >= 3.4:
            tendency = "高め"
        elif avg >= 2.4:
            tendency = "標準"
        else:
            tendency = "低め"
        print(f"- {trait}: 平均{avg:.2f}/4.00（{tendency}）")

    print(f"総合平均: {overall:.2f}/4.00")
    print("※この結果は自己傾向の簡易表示であり、適性を断定するものではありません。")


def run() -> None:
    questions = load_questions()

    print("SPI練習アプリ（JSON版）")
    mode = choose_from_list("モードを選択してください", ["非言語", "言語", "性格"])

    categories = sorted({q["category"] for q in questions if q.get("mode") == mode})
    category = choose_from_list("出題分野を選択してください", categories, allow_all=True)

    difficulties = sorted({q["difficulty"] for q in questions if q.get("mode") == mode})
    difficulty = choose_from_list("難易度を選択してください", difficulties, allow_all=True)

    pool = filter_questions(questions, mode, category, difficulty)
    if not pool:
        raise QuizError("条件に一致する問題がありません。")

    print(f"\n該当問題数: {len(pool)}問")
    default_count = min(20, len(pool))
    raw_count = input(f"何問解きますか？（Enterで{default_count}問） > ").strip()
    if raw_count:
        if not raw_count.isdigit() or int(raw_count) <= 0:
            raise QuizError("問題数は1以上の整数で入力してください。")
        count = min(int(raw_count), len(pool))
    else:
        count = default_count

    selected = random.sample(pool, k=count)
    input("\nEnterで開始 > ")

    correct = 0
    personality_records: list[tuple[str, int]] = []

    for idx, question in enumerate(selected, start=1):
        is_correct, score = ask_question(question, idx, count, mode)
        if is_correct:
            correct += 1
        if mode == "性格" and score is not None:
            personality_records.append((question.get("trait", "その他"), score))

    print("\n====================")
    if mode == "性格":
        summarize_personality(personality_records)
    else:
        print(f"結果: {count}問中 {correct}問正解")
        print(f"正答率: {correct / count * 100:.1f}%")
    print("====================")


if __name__ == "__main__":
    try:
        run()
    except QuizError as exc:
        print(f"エラー: {exc}")
