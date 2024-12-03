from typing import Literal

from pydantic import BaseModel, Field

Author = Literal["ai", "user"]


class Chat(BaseModel):
    order: int = Field(..., example=1, description="Chat Order")
    author: Author = Field(..., example="ai", description="AI or User")
    message: str = Field(..., example="Hello, World!", description="Chat Message")


class ChatCreate(BaseModel):
    message: str = Field(..., example="Hello, World!", description="Chat Message")
