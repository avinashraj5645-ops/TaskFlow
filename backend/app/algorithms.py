"""
Section 2 — Integrated Algorithms Engine.

These are the ONLY sorting/searching primitives used by the /tasks?sort=...
and /tasks/search endpoints in app/routers/tasks.py. No built-in sorted()/
list.sort() is used anywhere in that request path.
"""
from typing import List, Dict, Any, Optional, Tuple

NOT_FOUND = -1  # documented sentinel returned by binary_search / linear_search


# ---------------------------------------------------------------------------
# Task 1 — insertion sort (in place)
# ---------------------------------------------------------------------------
def insertion_sort(records: List[Dict[str, Any]], key: str) -> None:
    """Sorts `records` in place, ascending, by record[key]."""
    for i in range(1, len(records)):
        current = records[i]
        current_val = current[key]
        j = i - 1
        while j >= 0 and records[j][key] > current_val:
            records[j + 1] = records[j]
            j -= 1
        records[j + 1] = current
    # no return value — mutates records directly


# ---------------------------------------------------------------------------
# Task 2 — binary search (requires records already sorted by key)
# ---------------------------------------------------------------------------
def binary_search(sorted_records: List[Dict[str, Any]], target_value: Any, key: str) -> int:
    low, high = 0, len(sorted_records) - 1
    while low <= high:
        mid = (low + high) // 2
        mid_val = sorted_records[mid][key]
        if mid_val == target_value:
            return mid
        elif mid_val < target_value:
            low = mid + 1
        else:
            high = mid - 1
    return NOT_FOUND


# ---------------------------------------------------------------------------
# Task 3 — linear search baseline
# ---------------------------------------------------------------------------
def linear_search(records: List[Dict[str, Any]], target_value: Any, key: str) -> int:
    for i, record in enumerate(records):
        if record[key] == target_value:
            return i
    return NOT_FOUND


# ---------------------------------------------------------------------------
# Task 5 — comparison-counting wrapper functions.
# These REIMPLEMENT the same logic as Tasks 1-3 (same behavior/output shape
# for the sort), but additionally count key-comparisons for benchmarking.
# They do not change the signatures/contracts of insertion_sort / binary_search
# / linear_search above, which remain untouched.
# ---------------------------------------------------------------------------
def insertion_sort_count(records: List[Dict[str, Any]], key: str) -> int:
    """Sorts records in place exactly like insertion_sort; returns comparison count."""
    comparisons = 0
    for i in range(1, len(records)):
        current = records[i]
        current_val = current[key]
        j = i - 1
        while j >= 0:
            comparisons += 1
            if records[j][key] > current_val:
                records[j + 1] = records[j]
                j -= 1
            else:
                break
        records[j + 1] = current
    return comparisons


def binary_search_count(sorted_records: List[Dict[str, Any]], target_value: Any, key: str) -> Dict[str, Any]:
    low, high = 0, len(sorted_records) - 1
    comparisons = 0
    index = NOT_FOUND
    while low <= high:
        mid = (low + high) // 2
        mid_val = sorted_records[mid][key]
        comparisons += 1
        if mid_val == target_value:
            index = mid
            break
        elif mid_val < target_value:
            low = mid + 1
        else:
            high = mid - 1
    return {"index": index, "comparison_count": comparisons}


def linear_search_count(records: List[Dict[str, Any]], target_value: Any, key: str) -> Dict[str, Any]:
    comparisons = 0
    index = NOT_FOUND
    for i, record in enumerate(records):
        comparisons += 1
        if record[key] == target_value:
            index = i
            break
    return {"index": index, "comparison_count": comparisons}


# ---------------------------------------------------------------------------
# Helper used by the /tasks?sort=priority endpoint to make priority a
# comparable rank before insertion_sort runs on it.
# ---------------------------------------------------------------------------
PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}


def with_priority_rank(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for r in records:
        r["priority_rank"] = PRIORITY_RANK.get(r.get("priority"), 2)
    return records
