# coding:utf-8
__author__ = 'xxj'

import time
import os
import requests
import Queue
import re
import slider_captcha
import lxml.etree
from openpyxl import load_workbook
# from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from slider_captcha import do_crack
import sys
reload(sys)
sys.setdefaultencoding('utf8')

headers = {
    'accept': '*/*',
    'accept-encoding': 'gzip, deflate, sdch',
    'accept-language': 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
}


class TianyanchaException(Exception):
    def __init__(self, message):
        super(TianyanchaException, self).__init__()
        self.message = message


def selenium_login():
    '''
    登录模块
    :return:
    '''
    # display = Display(visible=0, size=(1000, 800))
    # display.start()
    # time.sleep(3)

    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('no-sandbox')
    # chrome_options.add_argument('--user-agent="Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36"')    # 在windows环境中有无皆可，但是在linux中就要带上，否则403
    browser = webdriver.Chrome(
        executable_path=r'C:\Users\xj.xu\Downloads\chromedriver_win32\chromedriver.exe',
        chrome_options=chrome_options)
    # browser.maximize_window()
    wait = WebDriverWait(browser, 20)
    print '开始登录'
    browser.get('https://www.tianyancha.com/login')
    time.sleep(2)
    js = "window.scrollTo(600,0);"
    browser.execute_script(js)
    time.sleep(1)
    # print browser.page_source
    # browser.save_screenshot('xxj.png')
    login_button = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="title-tab text-center"]/div[@class="title"]')),
                              message='password login ele not exist')
    login_button.click()
    # login_button.send_keys(Keys.ENTER)
    print '点击密码登录栏'
    time.sleep(2)
    tel = wait.until(
        EC.presence_of_element_located((By.XPATH, '//div[@class="modulein modulein1 mobile_box  f-base collapse in"]//div[@class="pb30 position-rel"]/input[@class="input contactphone"]'))
    )
    tel.send_keys('15707974273')
    password = wait.until(
        EC.presence_of_element_located((By.XPATH, '//div[@class="modulein modulein1 mobile_box  f-base collapse in"]//div[@class="input-warp -block"]/input[@class="input contactword input-pwd"]'))
    )
    password.send_keys('abcd1234')
    submit = wait.until(
        EC.element_to_be_clickable((By.XPATH, '//div[@class="modulein modulein1 mobile_box  f-base collapse in"]/div[@class="btn -hg btn-primary -block"]'))
    )
    submit.click()
    print '出现滑块验证码，处理验证码...'
    time.sleep(10)

    do_crack(wait, browser)     # 滑块验证码处理接口
    time.sleep(10)

    cookie_list = browser.get_cookies()
    cookie_dict = {}
    for cookie in cookie_list:
        if cookie.has_key('name') and cookie.has_key('value'):
            cookie_dict[cookie['name']] = cookie['value']
    print '登录后的cookies：', cookie_dict

    abs_path = r'/ftp_samba/112/spider/python/tianyancha/tianyancha_count'  # 断点文件目录
    if not os.path.exists(abs_path):
        print '断点文件目录不存在，所以创建断点文件目录'
        os.mkdir(abs_path)
        abs_path_file = os.path.join(abs_path, 'tianyancha_count')
        with open(abs_path_file, 'w') as file:
            file.write('0')
    abs_path_file = os.path.join(abs_path, 'tianyancha_count')
    print '断点文件路径：', abs_path_file
    with open(abs_path_file, 'r') as file:  # 获取断点
        num = int(file.read())
        print '当前断点值：', num
    save_url = url_list(cookies=cookie_dict)  # url列表的获取接口
    # 每天获取10条数据的操作
    start = 10 * num
    end = 10 * (num + 1)
    for url in save_url[start:end]:  # 导出xlsx文件
        # for url in save_url[0:2]:
        print '----将要导出----', url
        browser.get(url)
        time.sleep(4)
        js = 'document.getElementsByClassName("btn btn-vip -sm float-right")[0].click();'
        browser.execute_script(js)
        time.sleep(2)
        browser.refresh()  # 刷新操作
        time.sleep(4)
    xlsx_download(cookies=cookie_dict)  # 下载xlsx文件
    print '下载xlsx文件完成'
    # time.sleep(20)
    browser.quit()
    xlsx()  # 将xlsx文件合并
    print 'xlsx文件合并完成'
    if num == len(save_url) / 10:
        with open(abs_path_file, 'w') as file:
            file.write('0')
    else:
        with open(abs_path_file, 'w') as file:
            file.write(str(num + 1))


def url_list(cookies):
    '''
    获取具体的url列表
    :return:
    '''
    areas = ['ah', 'bj', 'cq', 'fj', 'gd', 'gs', 'gx', 'gz', 'han', 'heb', 'hen', 'hlj', 'hub', 'hun', 'jl',
             'js', 'jx', 'ln', 'nmg', 'nx', 'qh', 'sc', 'sd', 'sh', 'snx', 'sx', 'tj', 'xj', 'xz', 'yn', 'zj']  # 地区
    reg_times = ['oe01', 'oe015', 'oe510', 'oe1015', 'oe15']  # 注册时间
    # area_url = 'https://{area}.tianyancha.com/search?key=%E7%BD%91%E5%90%A7'
    area_url = 'https://www.tianyancha.com/search?key=%E7%BD%91%E5%90%A7&base={area}'
    # reg_time_url = 'https://{area}.tianyancha.com/search/{reg_time}?key=%E7%BD%91%E5%90%A7'
    reg_time_url = 'https://www.tianyancha.com/search/{reg_time}?key=%E7%BD%91%E5%90%A7&base={area}'
    save_url = []
    for area in areas:
        url = area_url.format(area=area)
        print url
        response = requests.get(url=url, headers=headers, cookies=cookies, timeout=20)
        # response = get(url, 3, cookies)
        xpath_obj = lxml.etree.HTML(response.text)
        total_num = xpath_obj.xpath('//span[@class="tips-num"]/text()')
        if total_num:
            total_num = total_num[0]
            print '该url下的网吧总数：', total_num
        else:
            if xpath_obj.xpath('//div[@class="content"]/div/text()'):
                if xpath_obj.xpath('//div[@class="content"]/div/text()')[0] == u'我们只是确认一下你不是机器人，':  # 验证码
                    raise Exception, '出现验证码'
        total_num = int(total_num)
        if total_num <= 5000:
            save_url.append(url)
        else:
            for reg_time in reg_times:
                url = reg_time_url.format(area=area, reg_time=reg_time)
                print '超过5000的网吧下加上注册时间的url：', url
                save_url.append(url)
    print '所有需要导出url的数量：', len(save_url)
    return save_url


def xlsx_download(cookies):
    '''
    API下载xlsx文件
    :return:
    '''
    file_dir_path = r'/ftp_samba/112/spider/python/tianyancha/tianyancha_xlsx'   # linux(xlsx文件存储的路径 )
    # file_dir_path = os.path.dirname(os.path.abspath(__file__)) + '\\tianyancha_xlsx'  # windows
    if not os.path.exists(file_dir_path):
        os.makedirs(file_dir_path)
    url = 'https://www.tianyancha.com/usercenter/myorder'
    response = requests.get(url, headers=headers, cookies=cookies, timeout=20)
    # response = get(url, 3, cookies)
    xpath_obj = lxml.etree.HTML(response.text)
    # bianhao_list = xpath_obj.xpath('//span[@class="pr20"]/text()')[1:20:2]
    # for bianhao in bianhao_list:
    #     url = 'http://dataservice.tianyancha.com/excel/企业数据服务—天眼查({bianhao}).xlsx'.format(bianhao=bianhao)
    #             'http://dataservice.tianyancha.com/excel/查公司导出数据结果—天眼查(W20012234851548122211357).xlsx'
    #     print url
    download_url_ls = xpath_obj.xpath('//div[@class="float-right"]/a/@href')    # 需要下载的xlsx文件
    for url in download_url_ls[0:10]:
        print url
        search_obj = re.search(r'.*?\((.*?)\).', url, re.S)
        if search_obj:
            bianhao = search_obj.group(1)
            print '下载文件编号为：', bianhao
        else:
            print '提取编号的正则表达式失效'
        response = requests.get(url=url, headers=headers, cookies=cookies, timeout=20)
        # response = get(url, 3, cookies)
        # file_path = r'c:\Users\xj.xu\Desktop\tianyancha' + '\\' + bianhao + '.xlsx'
        file_path = os.path.join(file_dir_path, bianhao + '.xlsx')
        # print file_path
        with open(file_path, 'wb') as file:
            file.write(response.content)


def xlsx():
    '''
    将下载的10个xlsx文件合并
    :return:
    '''
    dest_path = '/ftp_samba/112/spider/python/tianyancha/tianyancha'    # linux（xlsx文件合并后存放的路径）
    # dest_path = '/root/project_test/python/tianyancha'    # 测试环境
    # dest_path = os.path.dirname(os.path.abspath(__file__))  # windows
    if not os.path.exists(dest_path):
        os.makedirs(dest_path)
    date = time.strftime('%Y%m%d')
    dest_file_name = os.path.join(dest_path, 'tianyancha_' + date)
    tmp_file_name = os.path.join(dest_path, 'tianyancha_' + date + '.tmp')
    f = open(tmp_file_name, 'w')
    file_dir_path = '/ftp_samba/112/spider/python/tianyancha/tianyancha_xlsx'  # linux中xlsx文件存储的目录
    # file_dir_path = os.path.dirname(os.path.abspath(__file__)) + '\\tianyancha_xlsx'  # windows
    files = os.listdir(file_dir_path)
    for xlsx_file in [file for file in files if os.path.splitext(file)[1] == '.xlsx']:
        file_path = os.path.join(file_dir_path, xlsx_file)
        # print file_path
        wb = load_workbook(file_path)
        sheet = wb.active
        for rows in list(sheet.rows)[2:]:  # 行
            column_list = []
            for column in rows:  # 列
                if column.value is None:
                    text = ''
                else:
                    text = column.value.replace('\t', '')
                column_list.append(text)
            column_str = '\t'.join(column_list)
            column_str1 = column_str.replace('\t', '')
            if column_str1:
                f.write(column_str)
                f.write('\n')
        os.remove(file_path)
    f.close()
    print '文件全部写入完成'
    os.rename(tmp_file_name, dest_file_name)


def main():
    selenium_login()


if __name__ == '__main__':
    print time.strftime('[%Y-%m-%d %H:%M:%S]'), 'start'
    main()
    # xlsx()
    print time.strftime('[%Y-%m-%d %H:%M:%S]'), 'end'





