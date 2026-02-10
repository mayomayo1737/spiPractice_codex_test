#!/usr/bin/env python3
"""SPIの練習問題を30秒タイマー付きで解くCLIアプリ。"""

from __future__ import annotations

import random
import threading
from dataclasses import dataclass

TIME_LIMIT_SECONDS = 30


@dataclass(frozen=True)
class Question:
    category: str
    prompt: str
    choices: list[str]
    answer_index: int
    explanation: str


QUESTIONS: list[Question] = [
    Question(
        category="推論",
        prompt="A社の売上は昨年比20%増で240万円でした。昨年の売上はいくら？",
        choices=["160万円", "180万円", "200万円", "220万円"],
        answer_index=2,
        explanation="昨年をxとすると、x×1.2=240。よってx=200。",
    ),
    Question(
        category="割合",
        prompt="ある商品を定価の25%引きで販売すると3,000円でした。定価はいくら？",
        choices=["3,600円", "4,000円", "4,200円", "4,500円"],
        answer_index=1,
        explanation="25%引きは定価の75%=0.75倍。3000÷0.75=4000。",
    ),
    Question(
        category="損益算",
        prompt="原価800円の商品に25%の利益を見込んで定価をつけました。定価はいくら？",
        choices=["900円", "960円", "1,000円", "1,100円"],
        answer_index=2,
        explanation="利益25%なので原価の1.25倍。800×1.25=1000。",
    ),
    Question(
        category="集合",
        prompt="クラス40人中、英語が得意25人・数学が得意20人・両方得意10人。どちらも得意でない人数は？",
        choices=["3人", "5人", "7人", "10人"],
        answer_index=1,
        explanation="少なくともどちらか得意=25+20-10=35人。40-35=5人。",
    ),
    Question(
        category="速さ",
        prompt="時速60kmで30分進んだ。進んだ距離は？",
        choices=["15km", "20km", "25km", "30km"],
        answer_index=3,
        explanation="30分=0.5時間。距離=速さ×時間=60×0.5=30km。",
    ),
]


def timed_input(prompt: str, timeout: int) -> str | None:
    """指定秒数以内の入力を受け付ける。時間切れならNone。"""
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


def present_question(question: Question, question_number: int) -> bool:
    print(f"\n--- 問題 {question_number} ({question.category}) ---")
    print(question.prompt)
    for i, choice in enumerate(question.choices, start=1):
        print(f"  {i}. {choice}")

    print(f"\n制限時間は{TIME_LIMIT_SECONDS}秒です。")
    answer = timed_input("番号で回答してください > ", TIME_LIMIT_SECONDS)

    if answer is None:
        print("\n⏰ 時間切れです！")
        print(f"正解: {question.answer_index + 1}. {question.choices[question.answer_index]}")
        print(f"解説: {question.explanation}")
        return False

    if not answer.strip().isdigit():
        print("\n⚠️ 数字で入力してください。")
        print(f"正解: {question.answer_index + 1}. {question.choices[question.answer_index]}")
        print(f"解説: {question.explanation}")
        return False

    selected_index = int(answer) - 1
    is_correct = selected_index == question.answer_index

    if is_correct:
        print("\n✅ 正解！")
    else:
        print("\n❌ 不正解。")

    print(f"正解: {question.answer_index + 1}. {question.choices[question.answer_index]}")
    print(f"解説: {question.explanation}")
    return is_correct


def run_quiz(total_questions: int = 5) -> None:
    print("SPI練習（30秒タイマー・解説付き）を開始します。")
    print("Enterでスタート...")
    input()

    selected = random.sample(QUESTIONS, k=min(total_questions, len(QUESTIONS)))
    score = 0

    for i, question in enumerate(selected, start=1):
        if present_question(question, i):
            score += 1

    print("\n====================")
    print(f"結果: {len(selected)}問中 {score}問正解")
    print("====================")


if __name__ == "__main__":
    run_quiz()
