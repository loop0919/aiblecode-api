import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["AC", "WA", "TLE", "MLE", "RE", "CE", "IE"]


class SubmissionDetail(BaseModel):
    id: uuid.UUID = Field(..., description="Submission Detail ID")
    testcase_name: str = Field(..., example="sample_01", description="Testcase Name")
    status: Status = Field(..., example="AC", description="Status")
    time: float = Field(..., example=0.1, description="Time")
    memory: int = Field(..., example=50, description="Memory")


class Submission(BaseModel):
    id: uuid.UUID = Field(..., description="Submission ID")
    created_at: datetime = Field(..., description="Created Datetime")
    username: str = Field(..., example="sample_user", description="Username")
    language: str = Field(..., example="Python", description="Programming Language")
    code: str = Field(..., example="print('Hello, World!')", description="Code")
    statuses: dict[Status | Literal["WJ"], int] = Field(
        ..., example={"AC": 12}, description="Status"
    )
    details: list[SubmissionDetail] = Field(..., description="Submission Details")


class SubmissionSummary(BaseModel):
    id: uuid.UUID = Field(..., description="Submission ID")
    created_at: datetime = Field(..., description="Created Datetime")
    username: str = Field(..., example="sample_user", description="Username")
    language: str = Field(..., example="Python", description="Programming Language")
    statuses: dict[Status | Literal["WJ"], int] = Field(
        ..., example={"WJ": 5, "AC": 10}, description="Statuses"
    )


class SubmissionCreate(BaseModel):
    language: str = Field(..., example="Python", description="Programming Language")
    code: str = Field(..., example="print('Hello, World!')", description="Code")


class SubmissionCreateResponse(BaseModel):
    id: uuid.UUID = Field(..., description="Submission ID")
    created_at: datetime = Field(..., description="Created Datetime")
    message: str = Field(
        ..., example="Submission created successfully", description="Message"
    )


class RunCode(BaseModel):
    language: str = Field(..., example="Python", description="Programming Language")
    code: str = Field(..., example="print('Hello, World!')", description="Code")
    input: str = Field(..., example="sample input", description="Input")


class RunCodeResponse(BaseModel):
    stdout: str = Field(..., example="Hello, World!", description="Output(stdout)")
    stderr: str = Field(..., example="", description="Error Output(stderr)")
