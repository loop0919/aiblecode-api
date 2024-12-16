import json
import uuid
from typing import Generator, Literal

import google.generativeai as genai
from sqlalchemy.orm import Session

from api.core.config import GEMINI_API_KEY
from api.models import chat as chat_model
from api.models import problem as problem_model
from api.models import submission as submission_model
from api.schemas import chat as chat_schema

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

Status = Literal["AC", "WA", "TLE", "MLE", "RE", "CE", "IE"]


def map_status(status: dict[Status | Literal["WJ"], int]) -> str:
    if status["WJ"] > 0:
        return "ジャッジ中"
    elif status["AC"] == sum(status.values()):
        return "正解"
    elif status["CE"] > 0:
        return "コンパイルエラー"
    elif status["RE"] > 0:
        return "実行時エラー"
    elif status["WA"] > 0:
        return "不正解"
    elif status["TLE"] > 0:
        return "実行時間オーバー"
    elif status["MLE"] > 0:
        return "メモリオーバー"
    else:
        return "内部エラー"


def first_statement(problem: problem_model.Problem) -> str:
    text = rf"""
これから流れるチャットは、以下の問題に対する解答として作成されたコードです。あなたの役割は、これらのコードを講師としてレビューすることです。
ただし、以下の留意事項を守ってください。

- 異常系の処理については言及不要です。
- 正解ではない場合、ヒントを与えるのみに留めてください。
- 正解の場合、良い点と改善点、アドバイスを行ってください。

問題:
\`\`\`
# {problem.title}
{problem.statement}
\`\`\`
"""
    return text


def review_statement(
    submission: submission_model.Submission, status: dict[Status | Literal["WJ"], int]
) -> str:
    text = rf"""
次のコードをレビューしてください。

言語: {submission.language}
ステータス: {map_status(status)}
コード:
\`\`\`
{submission.code}
\`\`\`
"""
    return text


def chat(
    db: Session,
    problem: problem_model.Problem,
    submission: submission_model.Submission,
    status: dict[Status | Literal["WJ"], int],
) -> chat_schema.Chat:
    if status["WJ"] > 0:
        raise ValueError("Submission is not judged yet")

    curr_chat = get_ai_chat(db, submission)
    if curr_chat and curr_chat.message:
        return chat_schema.Chat(
            order=1,
            author="ai",
            message=curr_chat.message,
        )

    chat = model.start_chat(
        history=[
            {"role": "user", "parts": first_statement(problem)},
        ]
    )

    chat_id = create_chat(db, "ai", "", submission).id

    chunk = chat.send_message(review_statement(submission, status))

    create_chat(db, "ai", chunk.text, submission, chat_id)

    db.commit()
    db.flush()

    return chat_schema.Chat(
        order=1,
        author="ai",
        message=chunk.text,
    )


def create_chat(
    db: Session,
    author: str,
    message: str,
    submission: submission_model.Submission,
    id: uuid.UUID | None = None,
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
        .order_by(chat_model.Chat.created_at.desc())
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
