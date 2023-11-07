import requests
import argparse
import itertools
from concurrent.futures import ThreadPoolExecutor
from colorama import init, Fore, Style

init()

def generate_dictionary(url, random_count=None):
    dictionary = []
    domain = url.split('//')[1].split('/')[0].split(':')[0]

    # 添加常见文件压缩扩展名
    compression_extensions = ['.rar', '.zip', '.tar.gz', '.7z', '.bz2','.bak']

    # 生成组合
    hostname_parts = domain.split('.')
    
    for ext in compression_extensions:
        for i in range(len(hostname_parts)):
            for combination in itertools.combinations(hostname_parts, i+1):
                without_colon = ''.join(combination).replace(':', '')
                
                # 排除带有冒号的组合
                if ':' in combination:
                    continue
                
                abbreviation_count = random_count if random_count else 1
                
                for _ in range(abbreviation_count):
                    # 获取缩写
                    abbreviation = without_colon
                    
                    if random_count is not None and random_count < len(abbreviation):
                        # 随机去掉指定数量的字符
                        indices = random.sample(range(len(abbreviation)), random_count)
                        abbreviation = ''.join([c for i, c in enumerate(abbreviation) if i not in indices])
                    
                    dictionary.append(abbreviation + ext)

    return dictionary


def scan_directory(url, dictionary, num_threads):
    not_found_urls = []
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        with requests.Session() as session:
            for item in dictionary:
                full_url = f'{url}/{item}'
                future = executor.submit(scan_url, session, full_url, not_found_urls)
                futures.append((full_url, future))

        for full_url, future in futures:
            response = future.result()
            if response is not None:
                if response.status_code == 404:
                    not_found_urls.append(full_url)
                else:
                    print(f'{full_url}\t{Fore.BLUE}{response.status_code}{Style.RESET_ALL}')

    return not_found_urls


def scan_url(session, url, not_found_urls):
    try:
        response = session.head(url, timeout=5)
        return response
    except requests.exceptions.RequestException:
        pass


# 解析命令行参数
parser = argparse.ArgumentParser(description='Directory scanning script', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-u', '--url', type=str, help='Target URL')
group.add_argument('-f', '--file', type=str, help='File containing multiple URLs')
parser.add_argument('-t', '--threads', type=int, default=10, help='Number of threads', dest='num_threads')
parser.add_argument('-d', '--random_count', type=int, default=None, help='Random abbreviation count')
args = parser.parse_args()

try:
    if args.url:
        urls = [args.url]
    else:
        with open(args.file, 'r') as file:
            urls = file.read().splitlines()
except FileNotFoundError:
    print(f"Error: File '{args.file}' not found.")
    sys.exit(1)

for url in urls:
    print(f'Scan results for {url}')
    # 判断是否输入的是域名，如果是则补充协议头
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'http://' + url
    dictionary = generate_dictionary(url, args.random_count)
    not_found_urls = scan_directory(url, dictionary, args.num_threads)
    
    print()  # 打印空行分隔不同的扫描结果
    
    print(f'Results for {url}\n')
    for url in not_found_urls:
        print(f'{url}\t{Fore.RED}404{Style.RESET_ALL}')
