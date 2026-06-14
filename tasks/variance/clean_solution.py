def sample_variance(data: list) -> float:
    n = len(data)
    if n < 2:
        return 0.0
    mean = sum(data) / n
    return sum((x - mean) ** 2 for x in data) / (n - 1)
