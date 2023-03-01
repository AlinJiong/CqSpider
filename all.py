import schedule
import requests
import re
import json
import time
from lxml import etree
from urllib.parse import urljoin
import urllib
import pandas as pd
import os
import smtplib
import email.mime.multipart
import email.mime.text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import functools
import traceback


headers = {
    'User-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36 Edg/103.0.1264.62'
}


files_before = []

files_after = []


def send_email(smtpHost, port, sendAddr, password, recipientAddrs, subject='', content='', file_post=[]):
    msg = email.mime.multipart.MIMEMultipart()
    msg['from'] = sendAddr
    # 多个收件人的邮箱应该放在字符串中,用字符分隔, 然后用split()分开,不能放在列表中, 因为要使用encode属性
    msg['to'] = recipientAddrs
    msg['subject'] = subject
    content = content
    txt = email.mime.text.MIMEText(content, 'plain', 'utf-8')
    msg.attach(txt)
    print("准备添加附件...")
    # 添加附件，从本地路径读取。如果添加多个附件，可以定义part_2,part_3等，然后使用part_2.add_header()和msg.attach(part_2)即可。

    for file in file_post:
        part = MIMEApplication(
            open(file, 'rb').read())
        # 给附件重命名,一般和原文件名一样,改错了可能无法打开.
        part.add_header('Content-Disposition', 'attachment',  filename=file)
        msg.attach(part)

    # 需要一个安全的连接，用SSL的方式去登录得用SMTP_SSL，之前用的是SMTP（）.端口号465或587
    smtp = smtplib.SMTP_SSL(smtpHost, port)
    smtp.login(sendAddr, password)  # 发送方的邮箱，和授权码（不是邮箱登录密码）
    # 注意, 这里的收件方可以是多个邮箱,用";"分开, 也可以用其他符号
    smtp.sendmail(sendAddr, recipientAddrs.split(";"), str(msg))
    print("发送成功！")
    smtp.quit()


def post_email(file_post=[]):
    try:
        # 设置好邮箱信息
        # 这是QQ邮箱服务器。如果是腾讯企业邮箱，其服务器为smtp.exmail.qq.com。其他邮箱需要查询服务器地址和端口号。
        smtpHost = 'smtp.qq.com'
        port = 465  # 端口号
        sendAddr = '2208957021@qq.com'  # 发送方地址
        # 手动输入授权码更安全.授权码的获取:打开qq邮箱->设置->账户->开启IMAP/SMTP服务->发送短信->授权码

        password = "muklngjwdibgecjb"
        # 接收方可以是多个账户, 用分号分开,send_email()函数中手动设置
        recipientAddrs = 'alinjiong@qq.com'
        subject = '青年就业见习基地'  # 主题
        content = '附件下载'  # 正文内容
        send_email(smtpHost, port, sendAddr, password,
                   recipientAddrs, subject, content, file_post)  # 调用函数
    except Exception as err:
        print(err)


def send_exceptions(error: str):
    try:
        # 设置好邮箱信息
        # 这是QQ邮箱服务器。如果是腾讯企业邮箱，其服务器为smtp.exmail.qq.com。其他邮箱需要查询服务器地址和端口号。
        smtpHost = 'smtp.qq.com'
        port = 465  # 端口号
        sendAddr = '2208957021@qq.com'  # 发送方地址
        # 手动输入授权码更安全.授权码的获取:打开qq邮箱->设置->账户->开启IMAP/SMTP服务->发送短信->授权码

        password = "muklngjwdibgecjb"
        # 接收方可以是多个账户, 用分号分开,send_email()函数中手动设置
        recipientAddrs = 'alinjiong@qq.com'
        subject = '青年就业基地程序异常'  # 主题
        content = error  # 正文内容
        send_email(smtpHost, port, sendAddr, password,
                   recipientAddrs, subject, content)  # 调用函数
    except Exception as err:
        print(err)


def catch_exceptions_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            error = traceback.format_exc()
            send_exceptions(error)
            return schedule.CancelJob
    return wrapper


def get_file_list():
    current_work_dir = os.getcwd()  # 当前文件所在的目录
    file_list = os.listdir(current_work_dir)  # 获取目录下所有文件
    return file_list


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

    return public_period


@catch_exceptions_decorator
def func1():
    # 渝中区
    # 需解决两个问题，
    # 1、去除重复内容的url，另一个是去除含有补贴的url
    # 2、有时候公示是以文件形式展示的出现的，需要采取两种方式解析页面
    # 3、清退，这个问题可以通过筛选公示名称来解决

    city = '渝中区'

    file_list = get_file_list()

    params = {
        "tenantId": 31,
        "searchWord": "青年就业见习基地",
        "dataTypeId": 2452,
        "orderBy": "time",
        "searchBy": "title",
    }

    params['beginDateTime'], params['endDateTime'] = get_timestamp()

    # params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

    res = requests.post(
        url='http://cqjlp.gov.cn/irs/front/search', json=params)
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


@catch_exceptions_decorator
def func2():
    # 江北区

    city = '江北区'

    file_list = get_file_list()

    params = {
        "tenantId": 4,
        "searchWord": "青年就业见习基地",
        "dataTypeId": 2452,
        "orderBy": "time",
        "searchBy": "title",
    }

    params['beginDateTime'], params['endDateTime'] = get_timestamp()

    # params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

    res = requests.post(
        url='http://cqjlp.gov.cn/irs/front/search', json=params)
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


@catch_exceptions_decorator
def func3():
    # 沙坪坝区

    city = '沙坪坝区'

    file_list = get_file_list()

    params = {
        "tenantId": 17,
        "searchWord": "青年就业见习基地",
        "dataTypeId": 2452,
        "orderBy": "time",
        "searchBy": "title",
    }

    params['beginDateTime'], params['endDateTime'] = get_timestamp()

    # params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

    res = requests.post(
        url='http://cqjlp.gov.cn/irs/front/search', json=params)
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


@catch_exceptions_decorator
def func4():
    # 九龙坡区
    # 获取xlsx链接并下载

    city = '九龙坡区'

    file_list = get_file_list()

    params = {
        "tenantId": 27,
        "searchWord": "青年就业见习基地",
        "dataTypeId": 2452,
        "orderBy": "time",
        "searchBy": "title",
    }

    params['beginDateTime'], params['endDateTime'] = get_timestamp()

    # params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

    res = requests.post(
        url='http://cqjlp.gov.cn/irs/front/search', json=params)
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


@catch_exceptions_decorator
def func5():
    # 南岸区
    # 获取docx链接并下载

    # 难点，剔除取消的公示名单
    # 取消

    city = '南岸区'

    file_list = get_file_list()

    params = {
        "tenantId": 25,
        "searchWord": "青年就业见习基地",
        "dataTypeId": 2452,
        "orderBy": "time",
        "searchBy": "title",
    }

    params['beginDateTime'], params['endDateTime'] = get_timestamp()

    # params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

    res = requests.post(
        url='http://cqjlp.gov.cn/irs/front/search', json=params)
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


@catch_exceptions_decorator
def func6():
    # 渝北区
    # 清退

    city = '渝北区'

    file_list = get_file_list()

    params = {
        "tenantId": 21,
        "searchWord": "青年就业见习基地",
        "dataTypeId": 2452,
        "orderBy": "time",
        "searchBy": "title",
    }

    params['beginDateTime'], params['endDateTime'] = get_timestamp()

    # params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

    res = requests.post(
        url='http://cqjlp.gov.cn/irs/front/search', json=params)
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


@catch_exceptions_decorator
def func7():
    # 北碚区
    # 撤销
    city = '北碚区'

    file_list = get_file_list()

    params = {
        "tenantId": 29,
        "searchWord": "青年就业见习基地",
        "dataTypeId": 2452,
        "orderBy": "time",
        "searchBy": "title",
    }

    params['beginDateTime'], params['endDateTime'] = get_timestamp()

    # params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

    res = requests.post(
        url='http://cqjlp.gov.cn/irs/front/search', json=params)
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


@catch_exceptions_decorator
def func8():
    # 大渡口区
    # 清退

    city = '大渡口区'

    file_list = get_file_list()

    params = {
        "tenantId": 18,
        "searchWord": "青年就业见习基地",
        "dataTypeId": 2452,
        "orderBy": "time",
        "searchBy": "title",
    }

    params['beginDateTime'], params['endDateTime'] = get_timestamp()

    # params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

    res = requests.post(
        url='http://cqjlp.gov.cn/irs/front/search', json=params)
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


@catch_exceptions_decorator
def func9():
    # 巴南区
    # 清退

    city = '巴南区'

    file_list = get_file_list()

    params = {
        "tenantId": 26,
        "searchWord": "青年就业见习基地",
        "dataTypeId": 2452,
        "orderBy": "time",
        "searchBy": "title",
    }

    params['beginDateTime'], params['endDateTime'] = get_timestamp()

    # params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

    res = requests.post(
        url='http://cqjlp.gov.cn/irs/front/search', json=params)
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


@catch_exceptions_decorator
def func10():
    # 长寿区
    # 取消

    # 需解决的问题：公示名称重复，title+time来识别
    # 期间发现的bug，有不可视符 \u200b 出现的可能性较低，暂未单独处理

    city = '长寿区'

    file_list = get_file_list()

    params = {
        "tenantId": 43,
        "searchWord": "青年就业见习基地",
        "dataTypeId": 2452,
        "orderBy": "time",
        "searchBy": "title",
    }

    params['beginDateTime'], params['endDateTime'] = get_timestamp()

    # params['beginDateTime'], params['endDateTime'] = [1661961600000, 1677600000000]

    res = requests.post(
        url='http://cqjlp.gov.cn/irs/front/search', json=params)
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


@catch_exceptions_decorator
def func11():
    # 永川区
    # 取消

    city = '永川区'

    file_list = get_file_list()

    params = {
        "tenantId": 9,
        "searchWord": "青年就业见习基地",
        "dataTypeId": 2452,
        "orderBy": "time",
        "searchBy": "title",
    }

    params['beginDateTime'], params['endDateTime'] = get_timestamp()

    # params['beginDateTime'], params['endDateTime'] = [1659283200000, 1677600000000]

    res = requests.post(
        url='http://cqjlp.gov.cn/irs/front/search', json=params)
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


def record_file_list():
    schedule.clear()
    files_before = get_file_list()


def post_file_list():
    files_after = get_file_list()
    file_post = list(set(files_after).difference(files_before))

    files = []

    for item in file_post:
        if re.search('.*?(csv|docx|xlsx)', item):
            files.append(item)

    post_email(files)


# def tasklist():
#     file_list1 = get_file_list()
#     schedule.clear()
#     schedule.every().day.at("10:00").do(func1)
#     schedule.every().day.at("10:00").do(func2)
#     schedule.every().day.at("10:00").do(func3)
#     schedule.every().day.at("10:00").do(func4)
#     schedule.every().day.at("10:00").do(func5)
#     schedule.every().day.at("10:00").do(func6)
#     schedule.every().day.at("10:00").do(func7)
#     schedule.every().day.at("10:00").do(func8)
#     schedule.every().day.at("10:00").do(func9)
#     schedule.every().day.at("10:00").do(func10)
#     schedule.every().day.at("10:00").do(func11)
#     schedule.run_all()
#     file_list2 = get_file_list()
#     file_post = file_list2 - file_list1
#     post_email(file_post)


if __name__ == "__main__":
    schedule.every().day.at("9:55").do(record_file_list)
    schedule.every().day.at("10:00").do(func1)
    schedule.every().day.at("10:00").do(func2)
    schedule.every().day.at("10:00").do(func3)
    schedule.every().day.at("10:00").do(func4)
    schedule.every().day.at("10:00").do(func5)
    schedule.every().day.at("10:00").do(func6)
    schedule.every().day.at("10:00").do(func7)
    schedule.every().day.at("10:00").do(func8)
    schedule.every().day.at("10:00").do(func9)
    schedule.every().day.at("10:00").do(func10)
    schedule.every().day.at("10:00").do(func11)
    schedule.every().day.at("10:05").do(post_file_list)

    while True:
        schedule.run_pending()
        time.sleep(2)
