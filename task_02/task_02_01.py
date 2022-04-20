import csv
import re

from chardet import detect

NUMBER_OF_INFO_FILES = 3
OS_NAME = ('Название ОС', 1)
PRODUCT_CODE = ('Код продукта', 2)
MANUFACTURER = ('Изготовитель системы', 3)
SYSTEM_TYPE = ('Тип системы', 4)
REGEX = re.compile(
    r"^Название ОС:\s+([\w\s.-]+)$[\s\S]+^Код продукта:\s+([\w\s.-]+)$[\s\S]+^Изготовитель системы:\s+([\w\s.-]+)$["
    r"\s\S]+^Тип системы:\s+([\w\s.-]+)$",
    re.MULTILINE)


def get_file_encoding(file_name):
    with open(file_name, 'rb') as file_in:
        return detect(file_in.read())['encoding']


def get_data():
    headers = [OS_NAME[0], PRODUCT_CODE[0], MANUFACTURER[0], SYSTEM_TYPE[0]]
    os_name_list = []
    os_prod_list = []
    os_code_list = []
    os_type_list = []
    main_data = [headers]
    for file in range(1, NUMBER_OF_INFO_FILES + 1):
        encoding = get_file_encoding(f'data/info_{file}.txt')
        with open(f'data/info_{file}.txt', 'r', encoding=encoding) as file_in:
            raw_data = file_in.read()
            result = re.search(REGEX, raw_data)
            os_name_list.append(result.group(OS_NAME[1]))
            os_code_list.append(result.group(PRODUCT_CODE[1]))
            os_prod_list.append(result.group(MANUFACTURER[1]))
            os_type_list.append(result.group(SYSTEM_TYPE[1]))
    for i in range(NUMBER_OF_INFO_FILES):
        main_data.append([os_name_list[i], os_code_list[i], os_prod_list[i], os_type_list[i]])
    return main_data


def write_to_csv():
    data = get_data()
    with open('data/output.csv', 'w', encoding='utf-8') as file_out:
        writer = csv.writer(file_out)
        writer.writerows(data)


if __name__ == '__main__':
    write_to_csv()
