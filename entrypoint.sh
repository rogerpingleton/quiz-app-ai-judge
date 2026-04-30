#!/bin/sh
# Entrypoint for the AI Quiz container.
#
# Defaults (from Dockerfile):
#   QUIZ_FILE=AI_Engineering_Questions.json
#   QUIZ_TOPIC="AI Engineering"
#
# Override either at runtime, e.g.:
#   docker run --rm -it --env-file .env quiz-app
#   docker run --rm -it --env-file .env -e QUIZ_TOPIC="Swift" quiz-app swift_questions.json
set -e

: "${QUIZ_FILE:=AI_Engineering_Questions.json}"
: "${QUIZ_TOPIC:=AI Engineering}"

# A positional arg overrides the questions file.
if [ -n "$1" ]; then
    QUIZ_FILE="$1"
    shift
fi

exec python quiz.py "$QUIZ_FILE" --topic "$QUIZ_TOPIC" "$@"
