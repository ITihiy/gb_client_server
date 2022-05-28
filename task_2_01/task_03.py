import tabulate

from task_2_01.task_02 import host_range_ping


def host_range_ping_tab(address, address_range):
    res = host_range_ping(address, address_range)
    res_dict = {'Reachable': [], 'Unreachable': []}
    for entry in res:
        if entry[1]:
            res_dict['Reachable'].append(entry[0])
        else:
            res_dict['Unreachable'].append(entry[0])
    print(tabulate.tabulate(res_dict, headers='keys'))


if __name__ == '__main__':
    host_range_ping_tab('192.168.1.60', 20)
