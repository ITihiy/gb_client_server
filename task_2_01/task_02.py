import ipaddress

from task_2_01.task_01 import host_ping, print_results


def host_range_ping(address, address_count):
    init_address = ipaddress.ip_address(address)
    last_octet = int(init_address) & 255
    last_address = 255 if last_octet + address_count > 255 else last_octet + address_count
    hosts_to_ping = [str(init_address + i - last_octet) for i in range(last_octet, last_address)]
    return host_ping(hosts_to_ping)


if __name__ == '__main__':
    res = host_range_ping('192.168.1.1', 300)
    print_results(res)
