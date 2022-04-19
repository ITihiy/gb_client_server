from chardet import detect


FILE_NAME = 'test_file.txt'


def get_file_encoding(file_name):
    with open(file_name, 'rb') as file_in:
        return detect(file_in.read())['encoding']


with open(FILE_NAME, 'w') as file_out:
    for line in ['сетевое программирование', 'сокет', 'декоратор']:
        file_out.write(f'{line}\n')

encoding = get_file_encoding(FILE_NAME)
print(encoding)

with open(FILE_NAME, 'r', encoding=encoding) as file_in:
    print(file_in.read())
