import uuid
from sqlalchemy.orm import Session

from api.models import problem as problem_model
from api.schemas import problem as problem_schema


# Category #########################################################################################
def get_category(db: Session, category_id: str) -> problem_model.Category:
    return (
        db.query(problem_model.Category)
        .filter(problem_model.Category.id == category_id)
        .first()
    )


def get_category_by_path_id(db: Session, path_id: str) -> problem_model.Category:
    return (
        db.query(problem_model.Category)
        .filter(problem_model.Category.path_id == path_id)
        .first()
    )


def get_category_list(db: Session) -> list[problem_model.Category]:
    return db.query(problem_model.Category).all()


def create_category(
    db: Session, category: problem_schema.CategoryCreate
) -> problem_model.Category:
    db_category = get_category_by_path_id(db, category.path_id)

    if not db_category:
        db_category = problem_model.Category(
            path_id=category.path_id,
            title=category.title,
            description=category.description,
        )
    db_category.title = category.title
    db_category.description = category.description

    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


# Problem ##########################################################################################
def get_problem_list(db: Session, category_path_id: str) -> list[problem_model.Problem]:
    category = get_category_by_path_id(db, category_path_id)

    if not category:
        return None

    return (
        db.query(problem_model.Problem)
        .filter(problem_model.Problem.category_id == category.id)
        .all()
    )


def get_problem(db: Session, problem_id: str) -> problem_model.Problem:
    return (
        db.query(problem_model.Problem)
        .filter(problem_model.Problem.id == problem_id)
        .first()
    )


def get_problem_by_path_id(
    db: Session, category_path_id: str, path_id: str
) -> problem_model.Problem:
    category = get_category_by_path_id(db, category_path_id)
    
    if not category:
        return None
    
    return (
        db.query(problem_model.Problem)
        .filter(
            problem_model.Problem.category_id == category.id,
            problem_model.Problem.path_id == path_id,
        )
        .first()
    )


def create_problem(
    db: Session, problem: problem_schema.ProblemCreate
) -> problem_model.Problem:
    category = get_category_by_path_id(db, problem.category_path_id)

    if not category:
        return None

    db_problem = get_problem_by_path_id(db, problem.category_path_id, problem.path_id)

    if not db_problem:
        db_problem = problem_model.Problem(
            path_id=problem.path_id,
            title=problem.title,
            statement=problem.statement,
            category_id=category.id,
            time_limit=problem.time_limit,
            memory_limit=problem.memory_limit,
        )

    db_problem.title = problem.title
    db_problem.statement = problem.statement
    db_problem.time_limit = problem.time_limit
    db_problem.memory_limit = problem.memory_limit

    db.add(db_problem)
    db.commit()
    db.refresh(db_problem)
    return db_problem


# Testcase #########################################################################################
def get_testcase_list(
    db: Session, problem_id: uuid.UUID
) -> list[problem_model.Testcase]:
    return (
        db.query(problem_model.Testcase)
        .filter(problem_model.Testcase.problem_id == problem_id)
        .all()
    )


def get_testcase_list_by_path_id(
    db: Session, category_path_id: str, problem_path_id: str
) -> list[problem_model.Testcase]:
    problem = get_problem_by_path_id(db, category_path_id, problem_path_id)

    if not problem:
        return []

    return (
        db.query(problem_model.Testcase)
        .filter(problem_model.Testcase.problem_id == problem.id)
        .all()
    )


def get_testcase(db: Session, testcase_id: str) -> problem_model.Testcase:
    return (
        db.query(problem_model.Testcase)
        .filter(problem_model.Testcase.id == testcase_id)
        .first()
    )


def get_testcase_by_name(
    db: Session, problem_id: uuid, name: str
) -> problem_model.Testcase:
    return (
        db.query(problem_model.Testcase)
        .filter(
            problem_model.Testcase.problem_id == problem_id,
            problem_model.Testcase.name == name,
        )
        .first()
    )


def create_testcase(
    db: Session, testcase: problem_schema.TestcaseCreate
) -> problem_model.Testcase:
    problem = get_problem_by_path_id(
        db, testcase.category_path_id, testcase.problem_path_id
    )

    if not problem:
        return None

    db_testcase = get_testcase_by_name(db, problem.id, testcase.name)

    if not db_testcase:
        db_testcase = problem_model.Testcase(
            problem_id=problem.id,
            name=testcase.name,
            input=testcase.input,
            output=testcase.output,
        )

    db_testcase.input = testcase.input
    db_testcase.output = testcase.output

    db.add(db_testcase)
    db.commit()
    db.refresh(db_testcase)
    return db_testcase
