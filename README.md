# AI Quiz

A small Python CLI that quizzes you on a topic of your choice and uses the OpenAI API to critique and score your answers.

## Setup

1. Install dependencies:

   ```sh
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and add your OpenAI API key:

   ```sh
   cp .env.example .env
   ```

   ```dotenv
   OPENAI_API_KEY=sk-your-key-here
   OPENAI_MODEL=gpt-4o-mini    # optional, this is the default
   ```

## Question file format

Pass a JSON file with an array of `{question, answer}` objects:

```json
[
  {
    "question": "What is Automatic Reference Counting (ARC)?",
    "answer": "ARC is Swift's compile-time memory management mechanism..."
  },
  {
    "question": "Explain the differences between strong, weak, and unowned references.",
    "answer": "A strong reference (the default) increments the retain count..."
  }
]
```

## Usage

```sh
python quiz.py path/to/questions.json
```

The app will:

1. Ask what topic the questions are about (used as context for the AI judge).
2. Ask how many questions you'd like in this session.
3. Pull random, non-repeating questions from the file.
4. Send each of your answers to the model along with the reference answer and topic. The model returns a critique (what you got right, where you can improve) and a score from 1 to 10.
5. Print a final cumulative grade out of 10 at the end.

Type `pass` instead of an answer to skip a question and draw a different one — passed questions still won't repeat in the same session.

## Notes

- The default model is `gpt-4o-mini`. Override it by setting `OPENAI_MODEL` in `.env` to any chat-capable model your account has access to.
- The grader is instructed to end its reply with `SCORE: X/10`. If for some reason a score can't be parsed, the question is recorded as 5/10 and the session continues.

## Docker usage

```sh
git clone https://github.com/rogerpingleton/quiz-app-ai-judge.git
cd quiz-app-ai-judge
cp .env.example .env             # then edit to add OPENAI_API_KEY

docker build -t quiz-app .
docker run --rm -it --env-file .env quiz-app
```
