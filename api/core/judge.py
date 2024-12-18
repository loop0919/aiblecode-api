import judge0
import time

# from api.core.config import JUDGE_API_URL

JUDGE_API_URL = "http://localhost:2358"
# CLIENT = judge0.Client(endpoint=JUDGE_API_URL, auth_headers={})
CLIENT = judge0.Flavor.CE

LANG = {
    "Python": 100,
    "Java": 91,
    "C++": 105,
    "Bash": 46,
    "Executable": 44,
}


# compile_submission = judge0.Submission(source_code=code, language=62)
# result = judge0.run(client=JUDGE_API_URL, submissions=compile_submission)

# print(result.language)

# fs = judge0.Filesystem(content=result.post_execution_filesystem)

# in_cases = ["2 3\n", "998 244\n", "114 514\n"]

# for in_case in in_cases:
#     judge_submission = judge0.Submission(
#         source_code="/usr/local/openjdk13/bin/java Main",
#         language=46,
#         additional_files=fs,
#         stdin=in_case,
#     )

# file_system = judge0.Filesystem()

# result = judge0.run(client=JUDGE_API_URL, submissions=judge_submission)

# print(result.stdout)
# print(result.stderr)


def run_code(code: str, language: str, stdin: str):
    submission = judge0.Submission(
        source_code=code,
        language=LANG[language],
        stdin=stdin,
        cpu_time_limit=5.0,
        memory_limit=512 * 1000,
    )

    result = judge0.run(client=CLIENT, submissions=submission)
    print(result.status)
    return result


def compile(code: str, language: str):
    submission = judge0.Submission(
        source_code=code,
        language=LANG[language],
        cpu_time_limit=1.0,
        memory_limit=512 * 1000,
    )

    result = judge0.run(client=CLIENT, submissions=submission)

    fs = judge0.Filesystem(content=result.post_execution_filesystem)

    if language == "Java":
        if any(f.name == "Main.class" for f in fs):
            return fs
        else:
            return result.status
    elif language == "C++":
        if any(f.name == "a.out" for f in fs):
            for f in fs:
                if f.name == "a.out":
                    return f.content
        else:
            print(result.compile_output)
            return result.status


def execute(
    code: str,
    language: str,
    stdin: str,
    output: str,
    time_limit: float = 2.0,
    memory_limit: int = 512,
):
    match language:
        case "Python":
            submission = judge0.Submission(
                source_code=code,
                language=LANG[language],
                stdin=stdin,
                expected_output=output,
                cpu_time_limit=time_limit,
                memory_limit=memory_limit * 1000,
            )

            result = judge0.run(client=CLIENT, submissions=submission)
        case "Java":
            submission = judge0.Submission(
                source_code="/usr/local/openjdk17/bin/java Main",
                language=LANG["Bash"],
                stdin=stdin,
                expected_output=output,
                additional_files=code,
                cpu_time_limit=time_limit,
                memory_limit=memory_limit * 1000,
            )

            result = judge0.run(client=CLIENT, submissions=submission)

        case "C++":
            submission = judge0.Submission(
                source_code=code,
                language=LANG["Executable"],
                stdin=stdin,
                expected_output=output,
                cpu_time_limit=time_limit,
                memory_limit=memory_limit * 1000,
            )

            result = judge0.run(client=CLIENT, submissions=submission)

        case _:
            return None

    time.sleep(5)

    return result


if __name__ == "__main__":
    #     code = """\
    # import java.util.Scanner;

    # public class Main {
    #     public static void main(String[] args) {
    #         Scanner sc = new Scanner(System.in);

    #         int A = sc.nextInt();
    #         int B = sc.nextInt();

    #         System.out.println(A + B);
    #     }
    # }

    # """
    code = """\
#include <bits/stdc++.h>

using namespace std;

int main() {
    int A, B;
    cin >> A >> B;

    cout << A + B << endl;
    return 0;
}

"""

    compiled = compile(code, "C++")
    if isinstance(compiled, judge0.Status):
        print(compiled)
        exit()

    result = execute(compiled, "C++", "2 3\n", "5")
    print(f"{result.status=}")
    print(f"{result.stdout=}, {result.stderr=}")
    print(f"{result.time=}, {result.memory=}")
