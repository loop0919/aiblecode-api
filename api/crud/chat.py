import json
from typing import Generator
import google.generativeai as genai

from api.core.config import GEMINI_API_KEY
from api.models import (
    chat as chat_model,
    problem as problem_model,
    submission as submission_model,
)
from sqlalchemy.orm import Session
from api.schemas import chat as chat_schema

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


def first_statement(problem: problem_model.Problem) -> str:
    text = rf"""
これから流れるチャットは、以下の問題に対する解答として作成されたコードです。あなたの役割は、これらのコードを講師としてレビューすることです。
ただし、異常系の処理については言及不要です。

問題:
\`\`\`
# {problem.title}
{problem.statement}
\`\`\`
"""
    return text


def review_statement(submission: submission_model.Submission) -> str:
    text = rf"""
次のコードをレビューしてください。

言語: {submission.language}
コード:
\`\`\`
{submission.code}
\`\`\`
"""
    return text


def chat(
    db: Session, problem: problem_model.Problem, submission: submission_model.Submission
) -> chat_schema.Chat:
    if chat := get_ai_chat(db, submission):
        return chat_schema.Chat(
            order=1,
            author="ai",
            message=chat.message,
        )

    chat = model.start_chat(
        history=[
            {"role": "user", "parts": first_statement(problem)},
        ]
    )

    create_chat(db, "user", review_statement(submission), submission)
    chunk = chat.send_message(review_statement(submission))

    create_chat(db, "ai", chunk.text, submission)

    return chat_schema.Chat(
        order=1,
        author="ai",
        message=chunk.text,
    )


def create_chat(
    db: Session, author: str, message: str, submission: submission_model.Submission
) -> chat_model.Chat:
    db_chat = chat_model.Chat(
        submission_id=submission.id,
        is_ai=author == "ai",
        message=message,
    )

    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)

    return db_chat


def get_ai_chat(
    db: Session, submission: submission_model.Submission
) -> chat_model.Chat:
    return (
        db.query(chat_model.Chat)
        .filter_by(submission_id=submission.id, is_ai=True)
        .first()
    )


# XXX: コードとして汚いので、リファクタリングが必要
def chat_stream(
    db: Session, problem: problem_model.Problem, submission: submission_model.Submission
) -> Generator[str, None, None]:
    if chat := get_ai_chat(db, submission):
        yield json.dumps(
            {
                "order": 0,
                "author": "ai",
                "message": chat.message,
            },
            ensure_ascii=False,
        )
        return

    chat = model.start_chat(
        history=[
            {"role": "user", "parts": first_statement(problem)},
        ]
    )

    create_chat(db, "user", review_statement(submission), submission)

    yield json.dumps(
        {
            "order": 0,
            "author": "user",
            "message": review_statement(submission),
        },
        ensure_ascii=False,
    )

    text = ""

    for order, chunk in enumerate(
        chat.send_message(review_statement(submission), stream=True), start=1
    ):
        text += chunk.text
        yield json.dumps(
            {
                "order": order,
                "author": "ai",
                "message": chunk.text,
            },
            ensure_ascii=False,
        )
    create_chat(db, "ai", text, submission)
