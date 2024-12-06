from fastapi import APIRouter, Depends, HTTPException, status

from api import database
from api.core.config import ADMIN_USERNAME
from api.core.security import get_current_active_user
from api.crud import problem as problem_crud
from api.crud import user as user_crud
from api.schemas import problem as problem_schema

router = APIRouter()


@router.get(
    "/category_list",
    tags=["category"],
    response_model=list[problem_schema.Category],
)
def category_list(db=Depends(database.get_db)) -> list[problem_schema.Category]:
    """
    カテゴリーの一覧を取得する。
    """
    return problem_crud.get_category_list(db)


@router.post(
    "/create_category",
    tags=["category"],
    response_model=problem_schema.CategoryCreateResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Permission denied"},
        status.HTTP_400_BAD_REQUEST: {"description": "Category already exists"},
    },
)
def create_category(
    category: problem_schema.CategoryCreate,
    user=Depends(get_current_active_user),
    db=Depends(database.get_db),
) -> problem_schema.CategoryCreateResponse:
    """
    カテゴリーを作成する。
    🚨**管理者ログインが必須**
    """
    if user != user_crud.get_user_by_username(db, ADMIN_USERNAME):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    created = problem_crud.create_category(db, category)

    return problem_schema.CategoryCreateResponse(
        status="success",
        message="Category created successfully",
        category=problem_schema.Category(
            id=created.id,
            path_id=created.path_id,
            title=created.title,
            description=created.description,
        ),
    )


@router.get(
    "/problem_list",
    tags=["problem"],
    response_model=list[problem_schema.CategoryDetail],
)
def all_problem_list(
    db=Depends(database.get_db),
) -> list[problem_schema.CategoryDetail]:
    """
    カテゴリ内の問題の一覧を取得する。
    """
    categories = problem_crud.get_category_list(db)

    return [
        problem_schema.CategoryDetail(
            id=category.id,
            path_id=category.path_id,
            title=category.title,
            description=category.description,
            problems=[
                problem_schema.ProblemSummary(
                    id=problem.id,
                    path_id=problem.path_id,
                    title=problem.title,
                    level=problem.level,
                    accepted_count=ac_count,
                )
                for (
                    problem,
                    ac_count,
                ) in problem_crud.get_problem_list_with_ac_submissions(
                    db, category.path_id
                )
            ],
        )
        for category in categories
    ]


@router.get(
    "/problem_list/{category_path_id}",
    tags=["problem"],
    response_model=list[problem_schema.ProblemSummary],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Category not found"}},
)
def problem_list(
    category_path_id: str, db=Depends(database.get_db)
) -> list[problem_schema.ProblemSummary]:
    """
    カテゴリ内の問題の一覧を取得する。
    """
    problems = problem_crud.get_problem_list_with_ac_submissions(db, category_path_id)

    return [
        problem_schema.ProblemSummary(
            id=problem.id,
            path_id=problem.path_id,
            title=problem.title,
            level=problem.level,
            accepted_count=ac_count,
        )
        for (problem, ac_count) in problems
    ]


@router.post(
    "/create_problem",
    tags=["problem"],
    response_model=problem_schema.ProblemCreateResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Permission denied"},
    },
)
def create_problem(
    problem: problem_schema.ProblemCreate,
    user=Depends(get_current_active_user),
    db=Depends(database.get_db),
) -> problem_schema.ProblemCreateResponse:
    """
    問題を作成する。
    🚨**管理者ログインが必須**
    """
    if user != user_crud.get_user_by_username(db, ADMIN_USERNAME):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    created = problem_crud.create_problem(db, problem)

    return problem_schema.ProblemCreateResponse(
        status="success",
        message="Problem created successfully",
        problem=problem_schema.Problem(
            id=created.id,
            path_id=created.path_id,
            title=created.title,
            statement=created.statement,
            level=created.level,
            time_limit=created.time_limit,
            memory_limit=created.memory_limit,
            accepted_count=0,
        ),
    )


@router.get(
    "/problem/{category_path_id}/{problem_path_id}",
    tags=["problem"],
    response_model=problem_schema.Problem,
)
def problem(
    category_path_id: str, problem_path_id: str, db=Depends(database.get_db)
) -> problem_schema.Problem:
    """
    問題の詳細を取得する。
    """
    problem, ac_count = problem_crud.get_problem_with_submission_count(
        db, category_path_id, problem_path_id
    )

    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found"
        )

    return problem_schema.Problem(
        id=problem.id,
        path_id=problem.path_id,
        title=problem.title,
        statement=problem.statement,
        level=problem.level,
        time_limit=problem.time_limit,
        memory_limit=problem.memory_limit,
        accepted_count=ac_count,
    )


@router.get(
    "/problem/{category_path_id}/{problem_path_id}/testcases",
    tags=["testcase"],
    response_model=list[problem_schema.Testcase],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Permission denied"},
    },
)
def testcase_list(
    category_path_id: str,
    problem_path_id: str,
    db=Depends(database.get_db),
    user=Depends(get_current_active_user),
) -> list[problem_schema.Testcase]:
    """
    問題のテストケース一覧を取得する。
    🚨**管理者ログインが必須**
    """
    if user != user_crud.get_user_by_username(db, ADMIN_USERNAME):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    testcases = problem_crud.get_testcase_list_by_path_id(
        db, category_path_id, problem_path_id
    )

    return [
        problem_schema.Testcase(
            id=testcase.id,
            problem_id=testcase.problem_id,
            name=testcase.name,
            input=testcase.input,
            output=testcase.output,
        )
        for testcase in testcases
    ]


@router.post(
    "/create_testcase",
    tags=["testcase"],
    response_model=problem_schema.TestcaseCreateResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        status.HTTP_403_FORBIDDEN: {"description": "Permission denied"},
    },
)
def create_testcase(
    testcase: problem_schema.TestcaseCreate,
    user=Depends(get_current_active_user),
    db=Depends(database.get_db),
) -> problem_schema.TestcaseCreateResponse:
    """
    テストケースを作成する。
    🚨**管理者ログインが必須**
    """
    if user != user_crud.get_user_by_username(db, ADMIN_USERNAME):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
        )

    created = problem_crud.create_testcase(db, testcase)

    return problem_schema.TestcaseCreateResponse(
        status="success",
        message="Testcase created successfully",
        testcase=problem_schema.Testcase(
            id=created.id,
            problem_id=created.problem_id,
            name=created.name,
            input=created.input,
            output=created.output,
        ),
    )
