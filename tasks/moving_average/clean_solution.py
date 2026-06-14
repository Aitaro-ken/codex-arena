def moving_average(data: list, window: int) -> list:
    if not data:
        return []
    result = []
    for i in range(len(data)):
        start = max(0, i - window + 1)
        chunk = data[start : i + 1]
        result.append(sum(chunk) / len(chunk))
    return result
