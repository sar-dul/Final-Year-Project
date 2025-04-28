def calculate_stats(data):
    total = 0
    count = 0
    for value in data:
        total += value
        count += 1
    average = total / count if count != 0 else 0

print(calculate_stats([1, 2, 3, 4, 5])) 