import concurrent.futures
import ipaddress
import platform
import socket
import time
from subprocess import run, DEVNULL


def ping_one_host(url: str, count='2') -> (str, bool):
    try:
        address = ipaddress.ip_address(socket.gethostbyname(url))
    except socket.gaierror:
        return url, False
    parameter_name = '-n' if platform.system().lower() == 'windows' else '-c'
    params = ['ping', parameter_name, count, str(address)]

    # On Windows ping with result 'Destination host unreachable' returns exit code '0'
    if platform.system().lower() == 'windows':
        params.append('-w')
        params.append('1000')
    return url, run(params, stdout=DEVNULL).returncode == 0


def host_ping(hosts_list: list) -> list:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = []
        futures = [executor.submit(ping_one_host, url=current_host) for current_host in hosts_list]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
        return results


def print_results(results: list):
    for entry in sorted(results, key=lambda x: x[0]):
        print(entry[0], 'Узел доступен' if entry[1] else 'Узел недоступен')


if __name__ == '__main__':
    hosts = ['google.com', 'ya.ru', '192.168.1.254', 'abc.def', '8.8.8.8', 'sdf.ghj', 'hjk.rty', '1.1.1.1',
             '172.16.0.5', '10.10.0.11']
    start_time = time.time()
    res = host_ping(hosts)
    print_results(res)
    complete = time.time() - start_time
    print(f'Concurrent took {complete}s')

    print('*' * 80)

    start_time = time.time()
    for host in hosts:
        result = ping_one_host(host)
        print(host, 'Узел доступен' if result[1] else 'Узел недоступен')
    complete = time.time() - start_time
    print(f'Non concurrent took {complete}s')
