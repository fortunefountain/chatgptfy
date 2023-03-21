import openai
import json
import sys
import argparse
from typing import List, Dict
import os

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
HOME = os.environ.get("HOME")
HISTORY_FILENAME = "{}/.chatgpt/history.json".format(HOME)
openai.api_key = OPENAI_API_KEY

act_as = {
        "Translator": {
            "role": "system",
            "content": """
            I want you to act as an English translator,
             spelling corrector and improver.
             I will speak to you in any language
             and you will detect the language,
             translate it and answer in the corrected
             and improved version of my text, in English.
             I want you to replace my simplified A0-level words
             and sentences with more beautiful and elegant,
             upper level English words and sentences.
             Keep the meaning same,
             but make them more literary.
             I want you to only reply the correction,
             the improvements and nothing else,
             do not write explanations."
            """,
            },
        "LaTeX": {
            "role": "system",
            "content": """
            I want you to act as a LaTeX editor.
            I will speak to you in any language
            and you will detect the language,
            Answer in the corrected
            and improved version of my text in LaTeX form.
            I want you to replace my simplified A0-level words
            and sentences with more beautiful and elegant,
            upper level words and sentences.
            Keep the meaning same,
            but make them more literary.
            I want you to only reply the correction,
            the improvements and nothing else,
            do not write explanations."
            """,
            },
        "Extractor": {
            "role": "system",
            "content": """
            あなたは日本語の文章からキーワードを抽出するアシスタントAIです。userが入力した文章から、検索観点でインデックスするべき重要なキーワードを10個を','区切りで改行なしで出力しなさい。
            """,
            },
        }

def load_history() -> List[Dict[str, str]]:
    try:
        with open(HISTORY_FILENAME, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_history(history: List[Dict[str, str]]) -> None:
    with open(HISTORY_FILENAME, "w") as f:
        json.dump(history, f)


def send_question_to_chatgpt_api(messages: List[Dict[str, str]], max_tokens=150) -> str:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=max_tokens,
        n=1,
        temperature=0.5,
    )

    return response.choices[0].message['content']


def clear_history() -> None:
    with open(HISTORY_FILENAME, "w") as f:
        json.dump([], f)


def main() -> None:
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--clear",
                            help="Clears the question history",
                            action="store_true")
        parser.add_argument("-r", "--role", help="Act as a role", type=str)
        parser.add_argument("-t", "--maxtokens", help="Max tokens to consume.", type=int)
        parser.add_argument("-m", "--message", help="Message to ChatGPT", type=str)
        parser.add_argument("-q", "--quiet", help="Quiet mode", action="store_true")
        args = parser.parse_args()

        if args.clear:
            clear_history()
            print("History cleared.")
            sys.exit()

        act_as.setdefault(args.role, {
                "role": "system",
                "content": f"You are {args.role}.",
            })

        history = load_history()
        question = ""

        if sys.stdin.isatty() and not args.message and not args.quiet:
            print("Enter your question:")
            question = input()
        elif args.message:
            question = args.message
        else:
            question = input()

        messages = [{
            "role": "system",
            "content": "I want yout to act as an ChatGPT assistant.",
        }]
        for entry in history:
            messages.append({"role": "user", "content": f"Q: {entry['question']}"})
            messages.append({"role": "assistant",
                             "content": f"A: {entry['answer']}"})
        messages = [act_as[args.role]]
        messages.append({"role": "user", "content": question})

        answer = send_question_to_chatgpt_api(messages, max_tokens=args.maxtokens)

        history.append({"question": question, "answer": answer})
        save_history(history)

        if sys.stdin.isatty() and not args.quiet:
            print(f"Answer:\n{answer}")
        else:
            print(f"{answer}")
    except KeyboardInterrupt:
        print("bye!")


if __name__ == "__main__":
    main()
