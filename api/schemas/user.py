from typing import Literal
import uuid

from pydantic import BaseModel, Field


class User(BaseModel):
    id: uuid.UUID = Field(..., description="User ID")
    username: str = Field(..., example="sample_user", description="Username")


class UserCreate(BaseModel):
    username: str = Field(..., example="sample_user", description="Username")
    password: str = Field(..., example="sample_password", description="Password")


class UserCreateResponse(BaseModel):
    status: Literal["success", "failed"] = Field(..., example="success")
    message: str = Field(
        ..., example="User created successfully", description="Message"
    )
    user: User | None = Field(default=None, description="User information")


class Message(BaseModel):
    status: Literal["success", "failed"] = Field(
        ..., example="success", description="Status"
    )
    message: str = Field(..., example="Message", description="Message")
