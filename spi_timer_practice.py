#!/usr/bin/env python3
"""SPI練習アプリ（CLI + GUI）。問題はJSON管理。"""

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


def filter_questions(questions: list[dict], mode: str, category: str, difficulty: str) -> list[dict]:
    filtered = [q for q in questions if q.get("mode") == mode]
    if category != "すべて":
        filtered = [q for q in filtered if q.get("category") == category]
    if difficulty != "すべて":
        filtered = [q for q in filtered if q.get("difficulty") == difficulty]
    return filtered


def ask_question(question: dict, index: int, total: int, mode: str) -> tuple[bool | None, int | None]:
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
        score = len(question["choices"]) - selected
        return None, score

    is_correct = selected == question["answer_index"]
    print("\n✅ 正解！" if is_correct else "\n❌ 不正解。")
    print(f"正解: {question['answer_index'] + 1}. {question['choices'][question['answer_index']]}")
    print(f"解説:\n{question['explanation']}")
    return is_correct, None


def summarize_personality(records: list[tuple[str, int]], max_score: int = 4) -> str:
    if not records:
        return "回答データがないため、傾向を表示できません。"

    grouped: dict[str, list[int]] = defaultdict(list)
    for trait, score in records:
        grouped[trait].append(score)

    lines = ["=== 性格検査サマリー ==="]
    overall = sum(score for _, score in records) / len(records)
    for trait, scores in grouped.items():
        avg = sum(scores) / len(scores)
        ratio = avg / max_score
        if ratio >= 0.85:
            tendency = "高め"
        elif ratio >= 0.60:
            tendency = "標準"
        else:
            tendency = "低め"
        lines.append(f"- {trait}: 平均{avg:.2f}/{max_score:.2f}（{tendency}）")

    lines.append(f"総合平均: {overall:.2f}/{max_score:.2f}")
    lines.append("※この結果は自己傾向の簡易表示であり、適性を断定するものではありません。")
    return "\n".join(lines)


def run_cli() -> None:
    questions = load_questions()

    print("SPI練習アプリ（CLI）")
    mode = choose_from_list("モードを選択してください", ["非言語", "言語", "性格"])

    categories = sorted({q["category"] for q in questions if q.get("mode") == mode})
    category = choose_from_list("出題分野を選択してください", categories, allow_all=True)

    difficulties = sorted({q["difficulty"] for q in questions if q.get("mode") == mode})
    difficulty = choose_from_list("難易度を選択してください", difficulties, allow_all=True)

    pool = filter_questions(questions, mode, category, difficulty)
    if not pool:
        raise QuizError("条件に一致する問題がありません。")

    print(f"\n該当問題数: {len(pool)}問")
    print("出題順: Enterでランダム / 2でID順")
    order_choice = input("番号を選択 > ").strip()
    is_random_order = order_choice != "2"

    default_count = min(20, len(pool))
    raw_count = input(f"何問解きますか？（Enterで{default_count}問） > ").strip()
    if raw_count:
        if not raw_count.isdigit() or int(raw_count) <= 0:
            raise QuizError("問題数は1以上の整数で入力してください。")
        count = min(int(raw_count), len(pool))
    else:
        count = default_count

    selected = random.sample(pool, k=count) if is_random_order else sorted(pool, key=lambda q: q.get("id", ""))[:count]
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
        print(summarize_personality(personality_records, max_score=4))
    else:
        print(f"結果: {count}問中 {correct}問正解")
        print(f"正答率: {correct / count * 100:.1f}%")
    print("====================")


def run_gui() -> None:
    import tkinter as tk
    from tkinter import messagebox, ttk

    questions = load_questions()
    root = tk.Tk()
    root.title("SPI練習アプリ")
    root.geometry("420x860")
    root.minsize(390, 780)
    root.configure(bg="#e9f0ff")

    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("Card.TFrame", background="#ffffff")
    style.configure("Header.TLabel", background="#2f5fff", foreground="#ffffff", font=("Arial", 12, "bold"))
    style.configure("Sub.TLabel", background="#ffffff", foreground="#1f2a44")
    style.configure("Primary.TButton", font=("Arial", 10, "bold"))
    style.configure("Quiz.Horizontal.TProgressbar", troughcolor="#ecf0f8", background="#5d84ff", thickness=10)
    style.configure("TimerGreen.Horizontal.TProgressbar", troughcolor="#ecf0f8", background="#31c46c", thickness=14)
    style.configure("TimerYellow.Horizontal.TProgressbar", troughcolor="#ecf0f8", background="#f4bf2a", thickness=14)
    style.configure("TimerRed.Horizontal.TProgressbar", troughcolor="#ecf0f8", background="#ef5454", thickness=14)

    mode_var = tk.StringVar(value="非言語")
    category_var = tk.StringVar(value="すべて")
    difficulty_var = tk.StringVar(value="すべて")
    count_var = tk.StringVar(value="20")
    random_var = tk.BooleanVar(value=True)

    action_bar = ttk.Frame(root, style="Card.TFrame", padding=10)
    action_bar.pack(side="bottom", fill="x", padx=8, pady=(6, 8))
    next_btn = ttk.Button(action_bar, text="解答する", style="Primary.TButton")
    next_btn.pack(fill="x")

    shell = ttk.Frame(root, style="Card.TFrame", padding=8)
    shell.pack(fill="both", expand=True, padx=8, pady=(8, 0))

    header = ttk.Frame(shell, style="Card.TFrame", padding=10)
    header.pack(fill="x", pady=(0, 6))
    ttk.Label(header, text="SPI Practice", style="Header.TLabel", anchor="center", padding=7).pack(fill="x")
    ttk.Label(header, text="スマホ比率UI / タップ感覚で解答", style="Sub.TLabel").pack(anchor="w", pady=(7, 0))

    control = ttk.Frame(shell, style="Card.TFrame", padding=10)
    control.pack(fill="x", pady=(0, 6))

    ttk.Label(control, text="モード", style="Sub.TLabel").grid(row=0, column=0, sticky="w")
    mode_combo = ttk.Combobox(control, textvariable=mode_var, values=["非言語", "言語", "性格"], state="readonly", width=12)
    mode_combo.grid(row=1, column=0, padx=(0, 6), pady=(2, 0), sticky="w")

    ttk.Label(control, text="分野", style="Sub.TLabel").grid(row=0, column=1, sticky="w")
    category_combo = ttk.Combobox(control, textvariable=category_var, state="readonly", width=14)
    category_combo.grid(row=1, column=1, padx=(0, 6), pady=(2, 0), sticky="w")

    ttk.Label(control, text="難易度", style="Sub.TLabel").grid(row=2, column=0, sticky="w", pady=(8, 0))
    difficulty_combo = ttk.Combobox(control, textvariable=difficulty_var, state="readonly", width=12)
    difficulty_combo.grid(row=3, column=0, padx=(0, 6), pady=(2, 0), sticky="w")

    ttk.Label(control, text="出題数", style="Sub.TLabel").grid(row=2, column=1, sticky="w", pady=(8, 0))
    ttk.Entry(control, textvariable=count_var, width=8).grid(row=3, column=1, padx=(0, 6), pady=(2, 0), sticky="w")

    ttk.Checkbutton(control, text="ランダム出題", variable=random_var).grid(row=4, column=0, columnspan=2, pady=(8, 0), sticky="w")
    start_btn = ttk.Button(control, text="開始", style="Primary.TButton")
    start_btn.grid(row=5, column=1, pady=(8, 0), sticky="e")

    info_bar = ttk.Frame(shell, style="Card.TFrame", padding=10)
    info_bar.pack(fill="x", pady=(0, 6))
    ttk.Label(info_bar, text="進捗", style="Sub.TLabel").pack(anchor="w")
    progress_var = tk.DoubleVar(value=0)
    progress = ttk.Progressbar(info_bar, variable=progress_var, maximum=100, style="Quiz.Horizontal.TProgressbar")
    progress.pack(fill="x", pady=(2, 6))

    ttk.Label(info_bar, text="タイムリミット", style="Sub.TLabel").pack(anchor="w")
    timer_bar_var = tk.DoubleVar(value=100)
    timer_bar = ttk.Progressbar(info_bar, variable=timer_bar_var, maximum=100, style="TimerGreen.Horizontal.TProgressbar")
    timer_bar.pack(fill="x", pady=(2, 4))
    timer_label = ttk.Label(info_bar, text="", style="Sub.TLabel", font=("Arial", 10, "bold"))
    timer_label.pack(anchor="e")

    qa_card = ttk.Frame(shell, style="Card.TFrame", padding=10)
    qa_card.pack(fill="both", expand=True)

    q_title = ttk.Label(qa_card, text="設定を選んで『開始』を押してください", style="Sub.TLabel", font=("Arial", 11, "bold"))
    q_title.pack(anchor="w")

    q_prompt = tk.Text(qa_card, height=8, wrap="word", font=("Arial", 10), bg="#f9fbff", relief="flat")
    q_prompt.pack(fill="x", pady=6)
    q_prompt.configure(state="disabled")

    choice_var = tk.IntVar(value=-1)
    choice_frame = ttk.Frame(qa_card, style="Card.TFrame")
    choice_frame.pack(fill="x")
    choice_buttons: list[ttk.Radiobutton] = []

    feedback = tk.Text(qa_card, height=5, wrap="word", font=("Arial", 10), bg="#f8f8f8", relief="flat")
    feedback.pack(fill="x", pady=8)
    feedback.configure(state="disabled")

    state = {
        "mode": "非言語",
        "quiz": [],
        "index": 0,
        "correct": 0,
        "records": [],
        "timer_id": None,
        "remaining": None,
        "timer_total": None,
    }

    def update_filters(*_: object) -> None:
        mode = mode_var.get()
        cats = ["すべて"] + sorted({q["category"] for q in questions if q["mode"] == mode})
        diffs = ["すべて"] + sorted({q["difficulty"] for q in questions if q["mode"] == mode})
        category_combo["values"] = cats
        difficulty_combo["values"] = diffs
        category_var.set("すべて")
        difficulty_var.set("すべて")

    def write_prompt(text: str) -> None:
        q_prompt.configure(state="normal")
        q_prompt.delete("1.0", "end")
        q_prompt.insert("1.0", text)
        q_prompt.configure(state="disabled")

    def write_feedback(text: str) -> None:
        feedback.configure(state="normal")
        feedback.delete("1.0", "end")
        feedback.insert("1.0", text)
        feedback.configure(state="disabled")

    def clear_choices() -> None:
        for rb in choice_buttons:
            rb.destroy()
        choice_buttons.clear()

    def refresh_progress() -> None:
        total = max(len(state["quiz"]), 1)
        progress_var.set((state["index"] / total) * 100)

    def update_timer_visual() -> None:
        if state["timer_total"] is None or state["remaining"] is None:
            timer_bar_var.set(100)
            timer_bar.configure(style="TimerGreen.Horizontal.TProgressbar")
            timer_label.config(text="制限時間: なし")
            return

        ratio = max(state["remaining"] / state["timer_total"], 0)
        timer_bar_var.set(ratio * 100)
        if ratio > 0.50:
            timer_bar.configure(style="TimerGreen.Horizontal.TProgressbar")
        elif ratio > 0.25:
            timer_bar.configure(style="TimerYellow.Horizontal.TProgressbar")
        else:
            timer_bar.configure(style="TimerRed.Horizontal.TProgressbar")
        timer_label.config(text=f"残り時間: {state['remaining']}秒")

    def show_question() -> None:
        if state["index"] >= len(state["quiz"]):
            finish_quiz()
            return

        q = state["quiz"][state["index"]]
        choice_var.set(-1)
        q_title.config(text=f"問題 {state['index'] + 1}/{len(state['quiz'])} ({q['category']}・{q['difficulty']})")
        write_prompt(q["prompt"])
        write_feedback("")
        clear_choices()
        refresh_progress()

        for i, c in enumerate(q["choices"]):
            rb = ttk.Radiobutton(choice_frame, text=f"{i + 1}. {c}", value=i, variable=choice_var)
            rb.pack(anchor="w", pady=1)
            choice_buttons.append(rb)

        timeout = TIME_LIMITS[state["mode"]]
        if timeout is None:
            state["remaining"] = None
            state["timer_total"] = None
            update_timer_visual()
        else:
            state["remaining"] = timeout
            state["timer_total"] = timeout
            update_timer_visual()
            tick_timer()

    def tick_timer() -> None:
        if state["remaining"] is None:
            return
        if state["remaining"] <= 0:
            handle_timeout()
            return
        state["remaining"] -= 1
        update_timer_visual()
        state["timer_id"] = root.after(1000, tick_timer)

    def stop_timer() -> None:
        if state.get("timer_id") is not None:
            root.after_cancel(state["timer_id"])
            state["timer_id"] = None

    def score_selected_option(selected: int, timed_out: bool = False) -> None:
        q = state["quiz"][state["index"]]
        if state["mode"] == "性格":
            score = len(q["choices"]) - selected
            state["records"].append((q.get("trait", "その他"), score))
            state["index"] += 1
            show_question()
            return

        is_correct = selected == q["answer_index"]
        if is_correct:
            state["correct"] += 1

        prefix = ""
        if timed_out:
            prefix = "⏰ 時間切れ（選択中の回答で判定）\n"

        write_feedback(
            prefix
            + ("✅ 正解！\n" if is_correct else "❌ 不正解。\n")
            + f"正解: {q['answer_index'] + 1}. {q['choices'][q['answer_index']]}\n\n解説:\n{q['explanation']}"
        )
        state["index"] += 1
        next_btn.config(text="次へ")
        refresh_progress()

    def handle_timeout() -> None:
        stop_timer()
        selected = choice_var.get()
        if selected >= 0:
            score_selected_option(selected, timed_out=True)
            return

        q = state["quiz"][state["index"]]
        if state["mode"] == "性格":
            state["index"] += 1
            show_question()
            return
        write_feedback(
            f"⏰ 時間切れです。\n正解: {q['answer_index'] + 1}. {q['choices'][q['answer_index']]}\n\n解説:\n{q['explanation']}"
        )
        state["index"] += 1
        next_btn.config(text="次へ")
        refresh_progress()

    def submit_answer() -> None:
        if next_btn.cget("text") == "次へ":
            next_btn.config(text="解答する")
            show_question()
            return

        if state["index"] >= len(state["quiz"]):
            finish_quiz()
            return

        selected = choice_var.get()
        if selected < 0:
            messagebox.showinfo("未回答", "選択肢を選んでください。")
            return

        stop_timer()
        score_selected_option(selected)

    def finish_quiz() -> None:
        stop_timer()
        total = len(state["quiz"])
        progress_var.set(100)
        timer_bar_var.set(0)
        timer_bar.configure(style="TimerRed.Horizontal.TProgressbar")
        if state["mode"] == "性格":
            summary = summarize_personality(state["records"], max_score=4)
        else:
            summary = f"結果: {total}問中 {state['correct']}問正解\n正答率: {state['correct'] / total * 100:.1f}%"
        q_title.config(text="終了")
        write_prompt("おつかれさまでした。")
        write_feedback(summary)
        timer_label.config(text="")
        next_btn.config(text="解答する")

    def start_quiz() -> None:
        mode = mode_var.get()
        category = category_var.get()
        difficulty = difficulty_var.get()
        pool = filter_questions(questions, mode, category, difficulty)
        if not pool:
            messagebox.showerror("エラー", "条件に一致する問題がありません。")
            return

        raw = count_var.get().strip()
        if raw == "":
            count = min(20, len(pool))
        elif raw.isdigit() and int(raw) > 0:
            count = min(int(raw), len(pool))
        else:
            messagebox.showerror("エラー", "出題数は1以上の整数で入力してください。")
            return

        state["mode"] = mode
        if random_var.get():
            state["quiz"] = random.sample(pool, k=count)
        else:
            state["quiz"] = sorted(pool, key=lambda q: q.get("id", ""))[:count]

        state["index"] = 0
        state["correct"] = 0
        state["records"] = []
        next_btn.config(text="解答する")
        show_question()

    mode_combo.bind("<<ComboboxSelected>>", update_filters)
    start_btn.config(command=start_quiz)
    next_btn.config(command=submit_answer)
    update_filters()
    root.mainloop()


def run() -> None:
    print("起動モードを選択してください")
    print("  1. CLI")
    print("  2. GUI（クリック操作）")
    choice = input("番号を選択 > ").strip()
    if choice == "2":
        run_gui()
    else:
        run_cli()


if __name__ == "__main__":
    try:
        run()
    except QuizError as exc:
        print(f"エラー: {exc}")
