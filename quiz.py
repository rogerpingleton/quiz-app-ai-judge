#!/usr/bin/env python3
"""
AI-judged quiz app.

Reads a JSON file of {question, answer} pairs from a command-line argument,
asks the user a configurable number of randomly-selected questions, and uses
the OpenAI Chat Completions API to critique and score each answer 1–10.

Configuration is read from a .env file in the current directory:
    OPENAI_API_KEY=sk-...
    OPENAI_MODEL=gpt-4o-mini   # optional, defaults to gpt-4o-mini ("GPT Mini")
"""

import argparse
import json
import os
import random
import re
import sys

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


# ---------- helpers ----------------------------------------------------------

def load_questions(path):
    """Load and validate the question bank."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list) or not data:
        raise ValueError("Questions file must contain a non-empty JSON array.")

    for i, item in enumerate(data):
        if not isinstance(item, dict) or "question" not in item or "answer" not in item:
            raise ValueError(
                f"Item {i} is missing required 'question' and/or 'answer' fields."
            )
    return data


def ask_int(prompt, lo, hi):
    """Prompt until the user enters an integer in [lo, hi]."""
    while True:
        raw = input(prompt).strip()
        try:
            n = int(raw)
            if lo <= n <= hi:
                return n
        except ValueError:
            pass
        print(f"  Please enter an integer between {lo} and {hi}.")


def judge_answer(client, model, topic, question, reference_answer, user_answer):
    """Send the answer to the model for critique. Returns the model's text."""
    system_prompt = (
        f"You are an expert tutor evaluating a student's answer on the topic of "
        f"\"{topic}\". Compare the student's answer to the reference answer. "
        "Be encouraging but honest and specific. Your reply must contain three sections, "
        "in this order:\n"
        "  1. What they got right.\n"
        "  2. What they missed, got wrong, or could explain better.\n"
        "  3. A single final line in the EXACT format `SCORE: X/10` where X is an "
        "integer from 1 to 10 reflecting overall correctness and completeness.\n"
        "Do not include the score anywhere except that final line."
    )
    user_prompt = (
        f"Question:\n{question}\n\n"
        f"Reference answer:\n{reference_answer}\n\n"
        f"Student's answer:\n{user_answer if user_answer else '(no answer provided)'}"
    )

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


_SCORE_RE = re.compile(r"SCORE\s*:\s*(\d{1,2})\s*/\s*10", re.IGNORECASE)


def parse_score(text):
    """Pull the integer score out of the model's reply, clamped to [1, 10]."""
    m = _SCORE_RE.search(text)
    if not m:
        # Fallback: any "N/10" near the end of the text.
        m = re.search(r"(\d{1,2})\s*/\s*10", text)
    if not m:
        return None
    return max(1, min(10, int(m.group(1))))


def letter_grade(avg):
    """Map an average score (1–10) to a friendly summary."""
    if avg >= 9:   return "Excellent"
    if avg >= 7.5: return "Strong"
    if avg >= 6:   return "Solid"
    if avg >= 4:   return "Needs work"
    return "Keep studying"


# ---------- main -------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Quiz the user on a topic with AI-graded answers."
    )
    parser.add_argument("questions_file", help="Path to JSON file with question/answer pairs.")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY is not set. Add it to a .env file.", file=sys.stderr)
        sys.exit(1)

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    try:
        questions = load_questions(args.questions_file)
    except FileNotFoundError:
        print(f"Error: file not found: {args.questions_file}", file=sys.stderr)
        sys.exit(1)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error reading questions file: {e}", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    print("=" * 64)
    print(" AI Quiz")
    print("=" * 64)
    topic = input("What topic are these questions about? ").strip() or "general knowledge"
    num_questions = ask_int(
        f"How many questions would you like (1–{len(questions)})? ",
        1, len(questions),
    )

    print(f"\nUsing model: {model}")
    print(f"Topic: {topic}")
    print(f"Questions this session: {num_questions}")
    print("Type 'pass' as your answer to skip a question and draw a different one.")
    print("=" * 64)

    # Pre-shuffle indices so questions never repeat in a session.
    pool = list(range(len(questions)))
    random.shuffle(pool)

    scores = []
    answered = 0

    while answered < num_questions and pool:
        idx = pool.pop()
        q = questions[idx]

        print(f"\n--- Question {answered + 1} of {num_questions} ---")
        print(f"\n{q['question']}\n")

        try:
            user_answer = input("Your answer: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSession interrupted.")
            break

        if user_answer.lower() == "pass":
            if not pool:
                print("No more questions available to switch to. Ending session.")
                break
            print("Skipping — drawing a different question.")
            continue

        print("\nGrading...\n")
        try:
            critique = judge_answer(client, model, topic, q["question"], q["answer"], user_answer)
        except OpenAIError as e:
            print(f"OpenAI API error: {e}", file=sys.stderr)
            print("This question won't count. Drawing another.", file=sys.stderr)
            continue

        print(critique)

        score = parse_score(critique)
        if score is None:
            print("\n(Couldn't parse a score from the response — recording as 5.)")
            score = 5
        scores.append(score)
        answered += 1

    # Final tally
    print("\n" + "=" * 64)
    print(" Session complete")
    print("=" * 64)
    if not scores:
        print("No questions were graded.")
        return

    total = sum(scores)
    max_total = len(scores) * 10
    avg = total / len(scores)
    print(f"Questions graded:  {len(scores)}")
    print(f"Points:            {total} / {max_total}")
    print(f"Average score:     {avg:.1f} / 10")
    print(f"Final grade:       {round(avg)} / 10  ({letter_grade(avg)})")


if __name__ == "__main__":
    main()
