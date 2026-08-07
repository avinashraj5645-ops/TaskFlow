"""
Automated checks for the Section 2 algorithms engine.
Run with:  python3 check_algorithms.py
Plain if/else + print — no assert/pytest/unittest.
"""
from app.algorithms import (
    insertion_sort,
    binary_search,
    linear_search,
    insertion_sort_count,
    binary_search_count,
    linear_search_count,
    NOT_FOUND,
)


def check(case_name: str, result, expected) -> None:
    if result == expected:
        print(f"PASS: {case_name}")
    else:
        print(f"FAIL: {case_name} — expected {expected}, got {result}")


def run_checks() -> None:
    # 1. insertion_sort on empty list
    empty: list = []
    try:
        insertion_sort(empty, "x")
        check("insertion_sort empty list stays empty, no error", empty, [])
    except Exception as e:
        check("insertion_sort empty list stays empty, no error", f"raised {e}", [])

    # 2. insertion_sort on single-element list
    single = [{"x": 5}]
    insertion_sort(single, "x")
    check("insertion_sort single-element list unchanged", single, [{"x": 5}])

    # 3. binary_search finds first / last / middle of sorted distinct list
    sorted_list = [{"x": v} for v in [1, 2, 3, 4, 5]]
    check("binary_search finds first index", binary_search(sorted_list, 1, "x"), 0)
    check("binary_search finds last index", binary_search(sorted_list, 5, "x"), 4)
    check("binary_search finds middle index", binary_search(sorted_list, 3, "x"), 2)

    # 4. binary_search returns not-found sentinel when target absent
    check("binary_search returns NOT_FOUND for absent value", binary_search(sorted_list, 99, "x"), NOT_FOUND)

    # 5. insertion_sort_count: sorts correctly (a) and returns int > 0 (b)
    small = [{"x": 3}, {"x": 1}, {"x": 2}]
    count = insertion_sort_count(small, "x")
    check("insertion_sort_count leaves list correctly sorted", small, [{"x": 1}, {"x": 2}, {"x": 3}])
    check("insertion_sort_count returns int > 0 for len>1 list", (type(count) == int and count > 0), True)

    # 6. binary_search_count: known index + comparison_count > 0
    sorted_small = [{"x": v} for v in [10, 20, 30, 40]]
    bres = binary_search_count(sorted_small, 30, "x")
    check("binary_search_count finds correct index", bres["index"], 2)
    check("binary_search_count comparison_count is int > 0", (type(bres["comparison_count"]) == int and bres["comparison_count"] > 0), True)

    # 7. linear_search_count: absent value -> NOT_FOUND, comparisons == len
    lres = linear_search_count(sorted_small, 999, "x")
    check("linear_search_count index is NOT_FOUND for absent value", lres["index"], NOT_FOUND)
    check("linear_search_count comparison_count equals list length", lres["comparison_count"], len(sorted_small))


if __name__ == "__main__":
    run_checks()
