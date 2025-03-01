def calculate_stats(data):
    total = 0
    count = 0
    for value in data:
        total += value
        count += 1
    average = total / count if count != 0 else 0
    
    max_val = data[0]
    for num in data:
        if num > max_val:
            max_val = num
    
    return {
        'sum': total,
        'average': average,
        'max': max_val
    }

def filter_even(numbers):
    even = []
    for n in numbers:
        if n % 2 == 0:
            even.append(n)
    return even
