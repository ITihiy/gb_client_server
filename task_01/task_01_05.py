import sys
import subprocess

from chardet import detect


PING_COUNT = '4'

urls = ['yandex.ru', 'youtube.com']

count_arg = '-n' if sys.platform.startswith('win') else '-c'

for url in urls:
    args = ['ping', count_arg, PING_COUNT, url]
    ping_result = subprocess.Popen(args, stdout=subprocess.PIPE)
    for result in ping_result.stdout:
        detected_result = detect(result)
        print(result.decode(detected_result['encoding']).encode('utf-8').decode('utf-8'))
