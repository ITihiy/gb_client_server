import yaml

original_data = {
    'first_key': ['item 1', 'item 2', 'item 3', 'item 4', 'item 5'],
    'second_key': 42,
    'third_key': {
        'euros': '25€',
        'yens': '30¥',
        'pounds': '40£'
    }
}

with open('data/file.yaml', 'w', encoding='utf-8') as file_out:
    yaml.dump(original_data, file_out, default_flow_style=False, allow_unicode=True)

with open('data/file.yaml', 'r', encoding='utf-8') as file_in:
    file_data = yaml.load(file_in, yaml.FullLoader)

print('Data loaded correctly' if original_data == file_data else 'There were errors when loaded from yaml file')
