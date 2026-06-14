def binary_search(arr: list, target: int) -> int:
    lo, hi = 0, len(arr) - 1
    result = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            result = mid
            hi = mid - 1  # keep searching left for earliest occurrence
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return result
