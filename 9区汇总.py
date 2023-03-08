# %%
import requests, re, json, time
from lxml import etree
from urllib.parse import urljoin
import urllib
import pandas as pd
import os

# current_work_dir = os.path.dirname(__file__)  # 当前文件所在的目录
current_work_dir = os.getcwd()  # 当前文件所在的目录
print(current_work_dir)
file_list = os.listdir(current_work_dir)  # 获取目录下所有文件
print(file_list)

headers = {
    'User-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62'
}


def trans_time(t: str) -> int:
    "2022-08-01 00:00:00 时间转换成13位时间戳"
    timeArray = time.strptime(t, "%Y-%m-%d %H:%M:%S")
    timestamp = time.mktime(timeArray)
    return int(timestamp * 1000)  # 转换为13位的时间戳


def get_time_str() -> tuple:
    """返回当前月的时间区间('2022-08-01 00:00:00', '2022-09-01 00:00:00')"""
    t = time.localtime()
    if t.tm_mon != 12:
        return (
            "%d-%02d-01 00:00:00" % (t.tm_year, t.tm_mon),
            "%d-%02d-01 00:00:00" % (t.tm_year, t.tm_mon + 1),
        )
    else:
        return (
            "%d-%02d-01 00:00:00" % (t.tm_year, t.tm_mon),
            "%d-%02d-01 00:00:00" % (t.tm_year + 1, 1),
        )


def get_timestamp() -> tuple:
    """
    返回对应的时间戳
    ('2022-08-01 00:00:00', '2022-09-01 00:00:00')
    [1659283200000, 1661961600000]
    """
    _time_str = get_time_str()
    res = []
    for t in _time_str:
        res.append(trans_time(t))
        
    # 时间范围扩大一天，为上个月的最后一天到下个月的第一天
    #  ('2022-07-31 00:00:00', '2022-09-01 00:00:00')
    res[0] -= 86400000
    return res


def get_public_period(txt: str) -> str:
    """获取公示期"""
    html = etree.HTML(txt)

    p1 = html.xpath('//p//span/text()')

    p2 = html.xpath('//p/text()')

    info1 = "".join(p1)
    info2 = "".join(p2)

    info = info1 + info2

    public_period = re.search(r"\d+年\d+月\d+日.*?\d+月\d+日", info)

    if public_period:
        public_period = public_period.group()
    else:
        public_period = ''

    print(public_period)
    
    if len(public_period)>24:
        return ""

    return public_period


# %%
# 渝中区
# 需解决两个问题，
# 1、去除重复内容的url，另一个是去除含有补贴的url
# 2、有时候公示是以文件形式展示的出现的，需要采取两种方式解析页面
# 3、清退，这个问题可以通过筛选公示名称来解决

city = '渝中区'

params = {
    "tenantId": 31,
    "searchWord": "青年就业见习基地",
    "dataTypeId": 2452,
    "orderBy": "time",
    "searchBy": "title",
}

params['beginDateTime'], params['endDateTime'] = get_timestamp()

# params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

res = requests.post(url='http://cqjlp.gov.cn/irs/front/search', json=params)
url_json = json.loads(res.text)
url_list = url_json['data']['middle']['list']

# 利用字典去除重复的url
title_url = {}

for item in url_list:
    url = item['url']
    title = item['title_no_tag']

    if title_url.get(title) == None:
        title_url[title] = url

urls = []
pattern = ".*?青年就业见习基地的?公示"

# 筛选公示
for k, v in title_url.items():
    if re.search(pattern, k) != None:
        urls.append(v)

print(urls)

# urls = [
#     "http://www.cqyz.gov.cn/bm_229/qrlsbj/zwgk_97157/fdzdgknr_97159/zdmsxx_109235/cjjy_109236/jyxxfw/gxbyfw/jyjxbtsl/202301/t20230112_11493802.html?TVS2YU=865C6A0",
#     "http://www.cqyz.gov.cn/bm_229/qrlsbj/zwgk_97157/zfxxgkml/jczwgk/xxgk/gxby_9124/jyjxbtsl_9124/qtxxgk9_9124/202209/t20220908_11091957.html?Z95LDO=8SI76Z"
# ]

for url in urls:
    res = requests.get(url=url, headers=headers, timeout=10)
    res.encoding = 'utf-8'

    if res.status_code == 200:
        public_period = get_public_period(res.text)

        file_url = re.search(r"href=.*?(docx|xlsx)", res.text)

        if file_url:
            href = urljoin(url, file_url.group().split('"')[1])
            file_type = href.split('.')[-1]
            # print(file_type)

            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.' + file_type

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            urllib.request.urlretrieve(href, file_name)

        else:
            html = etree.HTML(res.text)
            all_data = html.xpath('//tbody/tr')
            info = []
            columns = ['单位名称', '单位地址']
            for data in all_data:
                company = ''.join(data.xpath("./td[2]/p/span/text()"))
                address = ''.join(data.xpath("./td[5]//span/text()"))
                #print(company, address)
                info.append([company, address])

            file = pd.DataFrame(columns=columns, data=info[1:])
            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.csv'

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            file.to_csv(file_name, encoding='utf-8')

# %%
# 江北区

city = '江北区'

params = {
    "tenantId": 4,
    "searchWord": "青年就业见习基地",
    "dataTypeId": 2452,
    "orderBy": "time",
    "searchBy": "title",
}

params['beginDateTime'], params['endDateTime'] = get_timestamp()

# params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

res = requests.post(url='http://cqjlp.gov.cn/irs/front/search', json=params)
url_json = json.loads(res.text)
url_list = url_json['data']['middle']['list']

# 利用字典去除重复的url
title_url = {}

for item in url_list:
    url = item['url']
    title = item['title_no_tag']

    if title_url.get(title) == None:
        title_url[title] = url

urls = []
pattern = ".*?就业见习基地的?公示"

# 筛选公示
for k, v in title_url.items():
    if re.search(pattern, k) != None:
        urls.append(v)

print(urls)

for url in urls:
    res = requests.get(url=url, headers=headers, timeout=10)
    res.encoding = 'utf-8'

    if res.status_code == 200:

        public_period = get_public_period(res.text)

        file_url = re.search(r"href=.*?(docx|xlsx)", res.text)

        if file_url:
            href = urljoin(url, file_url.group().split('"')[1])
            file_type = href.split('.')[-1]
            # print(file_type)

            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.' + file_type

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            urllib.request.urlretrieve(href, file_name)

        else:
            html = etree.HTML(res.text)
            all_data = html.xpath('//tbody/tr')
            info = []
            columns = ['单位名称', '单位地址']
            for data in all_data:
                company = "".join(data.xpath("./td[2]//span/text()"))
                address = "".join(data.xpath("./td[5]//span/text()"))
                #print(company, address)
                info.append([company, address])

            file = pd.DataFrame(columns=columns, data=info[1:])
            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.csv'

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            file.to_csv(file_name, encoding='utf-8')

# %%
# 沙坪坝区

city = '沙坪坝区'

params = {
    "tenantId": 17,
    "searchWord": "青年就业见习基地",
    "dataTypeId": 2452,
    "orderBy": "time",
    "searchBy": "title",
}

params['beginDateTime'], params['endDateTime'] = get_timestamp()

# params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

res = requests.post(url='http://cqjlp.gov.cn/irs/front/search', json=params)
url_json = json.loads(res.text)
url_list = url_json['data']['middle']['list']

# 利用字典去除重复的url
title_url = {}

for item in url_list:
    url = item['url']
    title = item['title_no_tag']

    if title_url.get(title) == None:
        title_url[title] = url

urls = []
pattern = ".*?青年就业见习基地的?公示"

# 筛选公示
for k, v in title_url.items():
    if re.search(pattern, k) != None:
        urls.append(v)

print(urls)

for url in urls:
    res = requests.get(url=url, headers=headers, timeout=10)
    res.encoding = 'utf-8'

    if res.status_code == 200:
        public_period = get_public_period(res.text)

        file_url = re.search(r"href=.*?(docx|xlsx)", res.text)

        if file_url:
            href = urljoin(url, file_url.group().split('"')[1])
            file_type = href.split('.')[-1]
            # print(file_type)

            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.' + file_type

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            urllib.request.urlretrieve(href, file_name)

        else:
            html = etree.HTML(res.text)
            all_data = html.xpath('//tbody/tr')
            info = []
            columns = ['单位名称', '单位地址']
            for data in all_data[1:]:
                company = "".join(data.xpath("./td[2]/text()"))
                address = "".join(data.xpath("./td[5]/text()"))
                #print(company, address)
                info.append([company, address])

            file = pd.DataFrame(columns=columns, data=info[1:])
            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.csv'

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            file.to_csv(file_name, encoding='utf-8')

# %%
# 九龙坡区
# 获取xlsx链接并下载

city = '九龙坡区'

params = {
    "tenantId": 27,
    "searchWord": "青年就业见习基地",
    "dataTypeId": 2452,
    "orderBy": "time",
    "searchBy": "title",
}

params['beginDateTime'], params['endDateTime'] = get_timestamp()

# params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

res = requests.post(url='http://cqjlp.gov.cn/irs/front/search', json=params)
url_json = json.loads(res.text)
url_list = url_json['data']['middle']['list']

# 利用字典去除重复的url
title_url = {}

for item in url_list:
    url = item['url']
    title = item['title_no_tag']

    if title_url.get(title) == None:
        title_url[title] = url

urls = []
pattern = ".*?青年就业见习基地的?公示"

# 筛选公示
for k, v in title_url.items():
    if re.search(pattern, k) != None:
        urls.append(v)

print(urls)

for url in urls:
    res = requests.get(url=url, headers=headers, timeout=10)
    res.encoding = 'utf-8'

    if res.status_code == 200:
        public_period = get_public_period(res.text)

        file_url = re.search(r"href=.*?(docx|xlsx)", res.text)

        if file_url:
            href = urljoin(url, file_url.group().split('"')[1])
            file_type = href.split('.')[-1]
            # print(file_type)

            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.' + file_type

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            urllib.request.urlretrieve(href, file_name)

        else:
            html = etree.HTML(res.text)
            all_data = html.xpath('//tbody/tr')
            info = []
            columns = ['单位名称', '单位地址']
            for data in all_data[1:]:
                company = "".join(data.xpath("./td[2]/text()"))
                address = "".join(data.xpath("./td[5]/text()"))
                #print(company, address)
                info.append([company, address])

            file = pd.DataFrame(columns=columns, data=info[1:])
            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.csv'

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            file.to_csv(file_name, encoding='utf-8')

# %%
# 南岸区
# 获取docx链接并下载

# 难点，剔除取消的公示名单
# 取消

city = '南岸区'

params = {
    "tenantId": 25,
    "searchWord": "青年就业见习基地",
    "dataTypeId": 2452,
    "orderBy": "time",
    "searchBy": "title",
}

params['beginDateTime'], params['endDateTime'] = get_timestamp()

# params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

res = requests.post(url='http://cqjlp.gov.cn/irs/front/search', json=params)
url_json = json.loads(res.text)
url_list = url_json['data']['middle']['list']

# 利用字典去除重复的url
title_url = {}

for item in url_list:
    url = item['url']
    title = item['title_no_tag']

    if title_url.get(title) == None:
        title_url[title] = url

urls = []
pattern = ".*?青年就业见习基地的?公示"

# 筛选公示
for k, v in title_url.items():
    if re.search(pattern, k) != None:
        if k.find('取消') != -1:
            continue
        urls.append(v)

print(urls)

for url in urls:
    res = requests.get(url=url, headers=headers, timeout=10)
    res.encoding = 'utf-8'

    if res.status_code == 200:
        public_period = get_public_period(res.text)

        file_url = re.search(r"href=.*?(docx|xlsx)", res.text)

        if file_url:
            href = urljoin(url, file_url.group().split('"')[1])
            file_type = href.split('.')[-1]
            # print(file_type)

            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.' + file_type

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            urllib.request.urlretrieve(href, file_name)

        else:
            html = etree.HTML(res.text)
            all_data = html.xpath('//tbody/tr')
            info = []
            columns = ['单位名称', '单位地址']
            for data in all_data[1:]:
                company = "".join(data.xpath("./td[2]/text()"))
                address = "".join(data.xpath("./td[5]/text()"))
                #print(company, address)
                info.append([company, address])

            file = pd.DataFrame(columns=columns, data=info[1:])
            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.csv'

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            file.to_csv(file_name, encoding='utf-8')

# %%
# 渝北区
# 清退

city = '渝北区'

params = {
    "tenantId": 21,
    "searchWord": "青年就业见习基地",
    "dataTypeId": 2452,
    "orderBy": "time",
    "searchBy": "title",
}

params['beginDateTime'], params['endDateTime'] = get_timestamp()

# params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

res = requests.post(url='http://cqjlp.gov.cn/irs/front/search', json=params)
url_json = json.loads(res.text)
url_list = url_json['data']['middle']['list']

# 利用字典去除重复的url
title_url = {}

for item in url_list:
    url = item['url']
    title = item['title_no_tag']

    if title_url.get(title) == None:
        title_url[title] = url

urls = []
pattern = ".*?青年就业见习基地的?公示"

# 筛选公示
for k, v in title_url.items():
    if re.search(pattern, k) != None:
        if k.find('清退') != -1:
            continue
        urls.append(v)

print(urls)

for url in urls:
    res = requests.get(url=url, headers=headers, timeout=10)
    res.encoding = 'utf-8'

    if res.status_code == 200:
        public_period = get_public_period(res.text)

        file_url = re.search(r"href=.*?(docx|xlsx)", res.text)

        if file_url:
            href = urljoin(url, file_url.group().split('"')[1])
            file_type = href.split('.')[-1]
            # print(file_type)

            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.' + file_type

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            urllib.request.urlretrieve(href, file_name)

        else:
            html = etree.HTML(res.text)
            all_data = html.xpath('//table/tbody/tr')
            info = []
            columns = ['单位名称', '单位地址']
            for data in all_data[1:]:
                company = "".join(data.xpath("./td[2]//span/text()"))
                address = "".join(data.xpath("./td[5]//span/text()"))
                #print(company, address)
                info.append([company, address])

            file = pd.DataFrame(columns=columns, data=info[1:])
            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.csv'

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            file.to_csv(file_name, encoding='utf-8')

# %%
# 北碚区
# 撤销
city = '北碚区'

params = {
    "tenantId": 29,
    "searchWord": "青年就业见习基地",
    "dataTypeId": 2452,
    "orderBy": "time",
    "searchBy": "title",
}

params['beginDateTime'], params['endDateTime'] = get_timestamp()

# params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

res = requests.post(url='http://cqjlp.gov.cn/irs/front/search', json=params)
url_json = json.loads(res.text)
url_list = url_json['data']['middle']['list']

# 利用字典去除重复的url
title_url = {}

for item in url_list:
    url = item['url']
    title = item['title_no_tag']

    if title_url.get(title) == None:
        title_url[title] = url

urls = []
pattern = ".*?青年就业见习基地的?公示"

# 筛选公示
for k, v in title_url.items():
    if re.search(pattern, k) != None:
        if k.find('撤销') != -1:
            continue
        urls.append(v)

print(urls)

for url in urls:
    res = requests.get(url=url, headers=headers, timeout=10)
    res.encoding = 'utf-8'

    if res.status_code == 200:
        public_period = get_public_period(res.text)

        file_url = re.search(r"href=.*?(docx|xlsx)", res.text)

        if file_url:
            href = urljoin(url, file_url.group().split('"')[1])
            file_type = href.split('.')[-1]
            # print(file_type)

            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.' + file_type

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            urllib.request.urlretrieve(href, file_name)

        else:
            html = etree.HTML(res.text)
            all_data = html.xpath('//table/tbody/tr')
            info = []
            columns = ['单位名称', '单位地址']
            for data in all_data[1:]:
                company = "".join(data.xpath("./td[2]//span/text()"))
                address = "".join(data.xpath("./td[5]//span/text()"))
                #print(company, address)
                info.append([company, address])

            file = pd.DataFrame(columns=columns, data=info[1:])
            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.csv'

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            file.to_csv(file_name, encoding='utf-8')

# %%
# 大渡口区
# 清退

city = '大渡口区'

params = {
    "tenantId": 18,
    "searchWord": "青年就业见习基地",
    "dataTypeId": 2452,
    "orderBy": "time",
    "searchBy": "title",
}

params['beginDateTime'], params['endDateTime'] = get_timestamp()

# params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

res = requests.post(url='http://cqjlp.gov.cn/irs/front/search', json=params)
url_json = json.loads(res.text)
url_list = url_json['data']['middle']['list']

# 利用字典去除重复的url
title_url = {}

for item in url_list:
    url = item['url']
    title = item['title_no_tag']

    if title_url.get(title) == None:
        title_url[title] = url

urls = []
pattern = ".*?青年就业见习基地的?公示"

# 筛选公示
for k, v in title_url.items():
    if re.search(pattern, k) != None:
        if k.find('清退') != -1:
            continue
        urls.append(v)

print(urls)

for url in urls:
    res = requests.get(url=url, headers=headers, timeout=10)
    res.encoding = 'utf-8'

    if res.status_code == 200:
        public_period = get_public_period(res.text)

        file_url = re.search(r"href=.\.\/\w+\.docx|href=.\.\/\w+\.xlsx",
                             res.text)

        if file_url:
            url_list = file_url.group().split('.')
            html_href = '.' + ".".join(url_list[1:])

            file_type = url_list[-1]

            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.' + file_type

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            href = urljoin(url, html_href)

            print(href)
            urllib.request.urlretrieve(href, file_name)

        else:
            html = etree.HTML(res.text)
            all_data = html.xpath('//table/tbody/tr')
            info = []
            columns = ['单位名称', '单位地址']
            for data in all_data[1:]:
                company = "".join(data.xpath("./td[2]//span/text()"))
                address = "".join(data.xpath("./td[5]//span/text()"))
                #print(company, address)
                info.append([company, address])

            file = pd.DataFrame(columns=columns, data=info[1:])
            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.csv'

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            file.to_csv(file_name, encoding='utf-8')

# %%
# 巴南区
# 清退

city = '巴南区'

params = {
    "tenantId": 26,
    "searchWord": "青年就业见习基地",
    "dataTypeId": 2452,
    "orderBy": "time",
    "searchBy": "title",
}

params['beginDateTime'], params['endDateTime'] = get_timestamp()

# params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

res = requests.post(url='http://cqjlp.gov.cn/irs/front/search', json=params)
url_json = json.loads(res.text)
url_list = url_json['data']['middle']['list']

# 利用字典去除重复的url
title_url = {}

for item in url_list:
    url = item['url']
    title = item['title_no_tag']

    if title_url.get(title) == None:
        title_url[title] = url

urls = []
pattern = ".*?青年就业见习基地的?公示"

# 筛选公示
for k, v in title_url.items():
    if re.search(pattern, k) != None:
        if k.find('清退') != -1:
            continue
        urls.append(v)

print(urls)

for url in urls:
    res = requests.get(url=url, headers=headers, timeout=10)
    res.encoding = 'utf-8'

    if res.status_code == 200:
        public_period = get_public_period(res.text)

        file_url = re.search(r"href=.*?(docx|xlsx)", res.text)

        if file_url:
            href = urljoin(url, file_url.group().split('"')[1])
            file_type = href.split('.')[-1]
            # print(file_type)

            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.' + file_type

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            urllib.request.urlretrieve(href, file_name)

        else:
            html = etree.HTML(res.text)
            all_data = html.xpath('//tbody/tr')
            info = []
            columns = ['单位名称', '单位地址']
            for data in all_data[3:]:
                company = "".join(data.xpath("./td[2]//span/text()"))
                address = "".join(data.xpath("./td[5]//span/text()"))
                #print(company, address)
                info.append([company, address])

            file = pd.DataFrame(columns=columns, data=info[1:])
            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.csv'

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            file.to_csv(file_name, encoding='utf-8')

# %%
# 长寿区
# 取消

# 需解决的问题：公示名称重复，title+time来识别
# 期间发现的bug，有不可视符 \u200b 出现的可能性较低，暂未单独处理

city = '长寿区'

params = {
    "tenantId": 43,
    "searchWord": "青年就业见习基地",
    "dataTypeId": 2452,
    "orderBy": "time",
    "searchBy": "title",
}

params['beginDateTime'], params['endDateTime'] = get_timestamp()

# params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

res = requests.post(url='http://cqjlp.gov.cn/irs/front/search', json=params)
url_json = json.loads(res.text)
url_list = url_json['data']['middle']['list']

# 利用字典去除重复的url
title_url = {}

for item in url_list:
    url = item['url']
    title = item['title_no_tag']
    _time = item['time'].split()[0]

    if title_url.get(title) == None:
        title_url[title + _time] = url

urls = []
pattern = ".*?青年就业见习基地的?公示"

# 筛选公示
for k, v in title_url.items():
    if re.search(pattern, k) != None:
        if k.find('取消') != -1:
            continue
        urls.append(v)

print(urls)

for url in urls:
    res = requests.get(url=url, headers=headers, timeout=10)
    res.encoding = 'utf-8'

    if res.status_code == 200:
        public_period = get_public_period(res.text)

        file_url = re.search(r"href=.*?(docx|xlsx)", res.text)

        if file_url:
            href = urljoin(url, file_url.group().split('"')[1])
            file_type = href.split('.')[-1]
            # print(file_type)

            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.' + file_type

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            urllib.request.urlretrieve(href, file_name)

        else:
            html = etree.HTML(res.text)
            all_data = html.xpath('//tbody/tr')
            info = []
            columns = ['单位名称', '单位地址']
            for data in all_data[4:]:
                company = "".join(data.xpath("./td[2]//span/text()"))
                address = "".join(data.xpath("./td[5]//span/text()"))
                # print(company, address)
                info.append([company, address])

            file = pd.DataFrame(columns=columns, data=info[1:])
            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.csv'

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            file.to_csv(file_name, encoding='utf-8')

# %%
# 永川区
# 取消

city = '永川区'

params = {
    "tenantId": 9,
    "searchWord": "青年就业见习基地",
    "dataTypeId": 2452,
    "orderBy": "time",
    "searchBy": "title",
}

params['beginDateTime'], params['endDateTime'] = get_timestamp()

# params['beginDateTime'], params['endDateTime'] = [1659283200000, 1677600000000]

res = requests.post(url='http://cqjlp.gov.cn/irs/front/search', json=params)
url_json = json.loads(res.text)
url_list = url_json['data']['middle']['list']

# 利用字典去除重复的url
title_url = {}

for item in url_list:
    url = item['url']
    title = item['title_no_tag']

    if title_url.get(title) == None:
        title_url[title] = url

urls = []
pattern = ".*?青年就业见习基地的?公示"

# 筛选公示
for k, v in title_url.items():
    if re.search(pattern, k) != None:
        if k.find('取消') != -1:
            continue
        urls.append(v)

print(urls)

for url in urls:
    res = requests.get(url=url, headers=headers, timeout=10)
    res.encoding = 'utf-8'

    if res.status_code == 200:
        public_period = get_public_period(res.text)

        file_url = re.search(r"href=.*?(docx|xlsx)", res.text)

        if file_url:
            href = urljoin(url, file_url.group().split('"')[1])
            file_type = href.split('.')[-1]
            # print(file_type)

            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.' + file_type

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            urllib.request.urlretrieve(href, file_name)

        else:
            html = etree.HTML(res.text)
            all_data = html.xpath('//tbody/tr')
            info = []
            columns = ['单位名称', '单位地址']
            for data in all_data[4:]:
                company = "".join(data.xpath("./td[2]//span/text()"))
                address = "".join(data.xpath("./td[5]//span/text()"))
                # print(company, address)
                info.append([company, address])

            file = pd.DataFrame(columns=columns, data=info[1:])
            file_name = city + '青年就业见习基地公示_' + public_period + '_' + '.csv'

            # 保存文件，如果已有，则不保存，减少网络请求数
            if file_name in file_list:
                continue
            print(file_name)

            file.to_csv(file_name, encoding='utf-8')
