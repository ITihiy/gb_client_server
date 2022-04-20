import json
from datetime import datetime
from random import randint

SIZE = 20
FMT = '%d.%m.%Y'


def write_order_to_json(item, quantity, price, buyer, date):
    order_dict = {
        'item': item,
        'quantity': quantity,
        'price': price,
        'buyer': buyer,
        'date': date,
    }
    with open('data/orders.json', 'r+', encoding='utf-8') as file_in:
        data = json.load(file_in)
        data['orders'].append(order_dict)
        file_in.seek(0)
        json.dump(data, file_in, indent=4)


if __name__ == '__main__':
    for i in range(SIZE):
        write_order_to_json(f'item_{i}', randint(1, 10), randint(10, 100), f'buyer_{i}', datetime.now().strftime(FMT))
