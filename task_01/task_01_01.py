original_values = ['разработка', 'сокет', 'декоратор']

print('Original values')
print('*' * 80)

for item in original_values:
    print(item, type(item))

print('\n\nUnicode values')
print('*' * 80)

unicode_values = [
    '\u0440\u0430\u0437\u0440\u0430\u0431\u043e\u0442\u043a\u0430',
    '\u0441\u043e\u043a\u0435\u0442',
    '\u0434\u0435\u043a\u043e\u0440\u0430\u0442\u043e\u0440',
]

for item in unicode_values:
    print(item, type(item))
