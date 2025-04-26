def filter_even(numbers):
    even = []
    for n in numbers:
        if n % 2 == 0:
            even.append(n)
    return even

