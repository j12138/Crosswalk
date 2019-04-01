# not necessary

lambdalist = {
    'A': lambda x : x < 0,
    'B': lambda x : x > -4
}

combined_filter = (lambdalist['A'] and lambdalist['B'])
print(combined_filter(1))