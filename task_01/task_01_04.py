values = ['разработка', 'администрирование', 'protocol', 'standard']
byte_values = []

for item in values:
    byte_value = item.encode('utf-8')
    print(byte_value)
    byte_values.append(byte_value)

print('*' * 80)

for item in byte_values:
    print(item.decode('utf-8'))
