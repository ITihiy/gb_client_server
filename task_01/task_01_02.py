values = ['class', 'function', 'method']

for item in values:
    current = eval(f"b'{item}'")
    print(f'Item: {current} type: {type(current)} length in bytes {len(current)}')
