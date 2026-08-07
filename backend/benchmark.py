"""
Benchmark the Section 2 algorithms engine using the Task 5 counting wrappers
against synthetic task records shaped exactly like real app data (title,
priority, due_date). Sizes: 10, 500, 3000.

Run with:  python3 benchmark.py
Results are also written to benchmark_results.txt (committed alongside the
README, per the submission guidelines).
"""
import copy
import random

from app.algorithms import insertion_sort_count, binary_search_count, linear_search_count, insertion_sort
from seed import synthetic_records

random.seed(7)

SIZES = [10, 500, 3000]


def run_benchmark() -> str:
    lines = []
    for n in SIZES:
        records = synthetic_records(n)

        # --- insertion sort comparisons (sort by title) ---
        sort_copy = copy.deepcopy(records)
        sort_comparisons = insertion_sort_count(sort_copy, "title")

        # --- prepare a sorted-by-title index for binary search ---
        sorted_index = copy.deepcopy(records)
        insertion_sort(sorted_index, "title")
        target = sorted_index[n // 2]["title"]  # guaranteed present

        binary_result = binary_search_count(sorted_index, target, "title")

        # --- linear search over the unsorted records for the same target ---
        linear_result = linear_search_count(records, target, "title")

        lines.append(f"n={n}")
        lines.append(f"  insertion_sort_count comparisons: {sort_comparisons}")
        lines.append(f"  binary_search_count:  index={binary_result['index']}, comparisons={binary_result['comparison_count']}")
        lines.append(f"  linear_search_count:  index={linear_result['index']}, comparisons={linear_result['comparison_count']}")

    return "\n".join(lines)


if __name__ == "__main__":
    output = run_benchmark()
    print(output)
    with open("benchmark_results.txt", "w") as f:
        f.write(output + "\n")
    print("\nSaved to benchmark_results.txt")
