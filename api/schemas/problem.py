from typing import Literal
import uuid

from pydantic import BaseModel, Field


class Category(BaseModel):
    id: uuid.UUID = Field(..., description="Category ID")
    path_id: str = Field(..., example="99_category", description="Category Path ID")
    title: str = Field(..., example="サンプルカテゴリ", description="Category Title")
    description: str = Field(
        ..., example="これはサンプルカテゴリです。", description="Category Description"
    )


class CategoryCreate(BaseModel):
    path_id: str = Field(..., example="99_category", description="Category Path ID")
    title: str = Field(..., example="サンプルカテゴリ", description="Category Title")
    description: str = Field(
        ..., example="これはサンプルカテゴリです。", description="Category Description"
    )


class CategoryCreateResponse(BaseModel):
    status: Literal["success", "failed"] = Field(
        ..., example="success", description="Status"
    )
    message: str = Field(
        ..., example="Category created successfully", description="Message"
    )
    category: Category | None = Field(default=None, description="Category information")


class Problem(BaseModel):
    id: uuid.UUID = Field(..., description="Problem ID")
    path_id: str = Field(..., example="problem_a", description="Problem Path ID")
    title: str = Field(..., example="サンプル問題", description="Problem Title")
    statement: str = Field(
        ...,
        example="正整数 $N$ が与えられます。 $N$ を $2$ 倍した値を出力してください。",
        description="Problem Statement",
    )
    time_limit: float = Field(..., example=2.0, description="Time Limit")
    level: int = Field(..., example=1, description="Level")
    memory_limit: int = Field(..., example=256, description="Memory Limit")
    accepted_count: int = Field(..., example=0, description="Accepted Count")


class ProblemSummary(BaseModel):
    id: uuid.UUID = Field(..., description="Problem ID")
    path_id: str = Field(..., example="problem_a", description="Problem Path ID")
    title: str = Field(..., example="サンプル問題", description="Problem Title")
    level: int = Field(..., example=1, description="Level")
    accepted_count: int = Field(..., example=0, description="Accepted Count")


class ProblemCreate(BaseModel):
    path_id: str = Field(..., example="problem_a", description="Problem Path ID")
    title: str = Field(..., example="サンプル問題", description="Problem Title")
    statement: str = Field(
        ...,
        example="正整数 $N$ が与えられます。 $N$ を $2$ 倍した値を出力してください。",
        description="Problem Statement",
    )
    category_path_id: str = Field(
        ..., example="99_category", description="Category Path ID"
    )
    level: int = Field(..., example=1, description="Level")
    time_limit: float = Field(..., example=2.0, description="Time Limit")
    memory_limit: int = Field(..., example=256, description="Memory Limit")


class ProblemCreateResponse(BaseModel):
    status: Literal["success", "failed"] = Field(
        ..., example="success", description="Status"
    )
    message: str = Field(
        ..., example="Problem created successfully", description="Message"
    )
    problem: Problem | None = Field(default=None, description="Problem information")


class Testcase(BaseModel):
    id: uuid.UUID = Field(..., description="Testcase ID")
    problem_id: uuid.UUID = Field(..., description="Problem ID")
    name: str = Field(..., example="00_testcase_01.txt", description="Testcase Name")
    input: str = Field(..., example="10\n", description="Input")
    output: str = Field(..., example="20\n", description="Output")


class TestcaseCreate(BaseModel):
    category_path_id: str = Field(
        ..., example="99_category", description="Category Path ID"
    )
    problem_path_id: str = Field(..., example="problem_X")
    name: str = Field(..., example="sample_testcase")
    input: str = Field(..., example="sample_input")
    output: str = Field(..., example="sample_output")


class TestcaseCreateResponse(BaseModel):
    status: Literal["success", "failed"] = Field(
        ..., example="success", description="Status"
    )
    message: str = Field(
        ..., example="Testcase created successfully", description="Message"
    )
    testcase: Testcase | None = Field(default=None, description="Testcase information")
