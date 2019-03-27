# coding:utf-8
__author__ = 'xxj'


#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by aneasystone on 2018/3/2

from PIL import Image
import time
from numpy import array
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import WebDriverException
import requests, io, re
import easing

def convert_css_to_offset(px):
    ps = px.replace('px', '').split(' ')
    x = -int(ps[0])
    y = -int(ps[1])
    return x, y, x + 10, y + 58


def convert_index_to_offset(index):
    row = int(index / 26)
    col = index % 26
    x = col * 10
    y = row * 58
    return x, y, x + 10, y + 58


def get_slider_offset_from_diff_image(diff):    # diff是滑块图片对象(get_slider_offset_from_diff_image()方法中：对于单张图片而言，通过滑块和透明背景图之间的rgb不同获取到单张图片中滑块的偏移量。)
    '''
    获取图片的偏移量()
    :param diff: 图片对象
    :return:滑块图片的偏移量
    '''
    im = array(diff)    # 可以将图片对象通过array()方法转换为图片对象的宽、高、rgb
    # print im
    width, height = diff.size
    # print '宽和高：', width, height
    diff = []     # 存储图片中每一列中属于滑块图片的j值。然后从diff列表中获取最小j值就是该滑块图片的偏移量
    for i in range(height):    # 高
        for j in range(width):    # 宽
            # black is not only (0,0,0)
            # print 'i;j：', i, j
            # print 'im[i, j, 0]：', im[i, j, 0]    # r
            # print 'im[i, j, 1]：', im[i, j, 1]    # g
            # print 'im[i, j, 2]：', im[i, j, 2]    # b
            if im[i, j, 0] > 15 or im[i, j, 1] > 15 or im[i, j, 2] > 15:    # 获取到的每一个像素点对应颜色的rgb值（删选出属于滑块的像素）   （从左边往右边遍历，获取到第一个满足该条件的像素j值）
                diff.append(j)
                break
    print 'diff的值：', diff
    return min(diff)


def is_similar(image1, image2, x, y):    # 通过两张图片的比对获取背景图片中缺陷位置的偏移量
    '''
    对比RGB值
    '''
    pass

    pixel1 = image1.getpixel((x, y))    # 获取像素点的rgb值
    pixel2 = image2.getpixel((x, y))
    # print 'x,y', x, y
    # print 'pixel1', pixel1
    # print 'pixel2', pixel2
    for i in range(0, 3):
        if abs(pixel1[i] - pixel2[i]) >= 50:    # 当两张图片中的颜色值超过50就认为是准确缺陷的值（这样必须确保干扰凹槽的所有值都是小于50，不然依旧会出现不正确度）
            return False

    return True


def get_diff_location(image1, image2):
    '''
    计算缺口的位置
    '''
    i = 0
    for i in range(0, 260):     # 宽
        for j in range(0, 116):    # 高
            if is_similar(image1, image2, i, j) == False:
                return i


def get_slider_offset(image_url, image_url_bg, css):
    '''
    获取背景图片中滑块凹槽的偏移量
    :param image_url: 完整背景图片url（切割）
    :param image_url_bg: 有凹槽的背景图片url（切割）
    :param css: 每张完整的背景图片的position的值
    :return:
    '''
    image_file = io.BytesIO(requests.get(image_url).content)
    im = Image.open(image_file)     # 完整的图片对象
    image_file_bg = io.BytesIO(requests.get(image_url_bg).content)
    im_bg = Image.open(image_file_bg)       # 有凹槽的图片对象
    # im.show()
    # im_bg.show()

    # 10*58 26/row => background image size = 260*116
    captcha = Image.new('RGB', (260, 116))    # 按照图片大小初始化一个大小一样的新图片对象
    captcha_bg = Image.new('RGB', (260, 116))
    for i, px in enumerate(css):    # 遍历position值（根据position的值，将乱序的背景图片合成为一份完整的背景图片）
        offset = convert_css_to_offset(px)
        region = im.crop(offset)
        region_bg = im_bg.crop(offset)
        offset = convert_index_to_offset(i)
        captcha.paste(region, offset)    # 合成一张完整的背景图片
        captcha_bg.paste(region_bg, offset)    # 合成一张有凹槽的背景图片

    # diff = ImageChops.difference(captcha, captcha_bg)    # 通过该方法将共同部分变成黑色，不同部分还是原来的颜色（然后再通过get_slider_offset_from_diff_image方法获取到偏移量）
    # 上面方法存在一些缺陷：如果在背景图片中存在一些干扰项，就会导致获取下面的偏移量失败（如果干扰项在正确项后面可以破解；如果干扰项在正确项前面就会获取到干扰项的偏移量，导致失败）
    # 1、需要对干扰项再做一层处理（就是需要对有凹槽的背景图片实现去干扰项操作）；2、不用difference()方法，采用其他方法处理。
    # 主要是由于difference()方法太精确，所以会导致获取到的偏移量可能是干扰项的偏移量
    # captcha.show()
    # captcha_bg.show()
    # diff.show()
    captcha.save(r'F:\ENVS\py2\HUAKAI_CAPTCHA\slice\captcha.png')
    captcha_bg.save(r'F:\ENVS\py2\HUAKAI_CAPTCHA\slice\captcha_bg.png')

    num = get_diff_location(captcha, captcha_bg)    # 采用一定粗略的方法可以筛选掉干扰的凹槽，获取准确的凹槽的偏移量（根据实际的图片进行值的规范性）, 提高准确凹槽的偏移量的识别率

    # diff.save(r'F:\ENVS\py2\HUAKAI_CAPTCHA\slice\diff.png')
    # return get_slider_offset_from_diff_image(diff)
    return num


def get_image_css(images):
    css = []
    for image in images:
        style_position = image.get_attribute("style")    # 参数是每张图片的属性
        match = re.match('background-image: url\("(.*?)"\); background-position: (.*?);', style_position)  # background-position: -205px 0px;
        position = match.group(2)  # 获取position的值
        # print position
        css.append(position)
    return css


def fake_drag(browser, knob, offset):
    '''
    模拟人性的滑动行为（防止被识别为机器行为）
    :param browser: 游览器对象
    :param knob: 移动滑块对象
    :param offset: 移动滑块移动的距离
    :return:
    '''
    offsets, tracks = easing.get_tracks(offset, 10, 'ease_out_expo')    # 获取一种人性行为的滑动规则（总体参试一下几种滑动规则，还是ease_out_expo()该方法正确度比较高）
    print 'offsets：', offsets
    print 'tracks：', tracks    # tracks是运动轨迹列表
    ActionChains(browser).click_and_hold(knob).perform()
    for x in tracks:
        ActionChains(browser).move_by_offset(x, 0).perform()
    # ActionChains(browser).pause(0.5).release().perform()
    ActionChains(browser).release().perform()


def slider_picture(browser):
    '''
    获取滑块图片的偏移量
    :param browser:
    :return:
    '''
    slice = browser.find_element_by_class_name("gt_slice")  # 获取滑块对象
    style = slice.get_attribute("style")  # 获取滑块图片的相关属性
    match = re.search('background-image: url\("(.*?)"\);', style)  # 获取到滑块图片的url
    url = match.group(1)
    print '滑块图片url：', url
    image_file = io.BytesIO(requests.get(url).content)
    im = Image.open(image_file)    # 图片对象（open()的参数可以是图片文件路径，也可以是BytesIO对象）   这样可以不用将图片保存下来
    im.save(r'F:\ENVS\py2\HUAKAI_CAPTCHA\slice\slice.png')  # 保存图片
    return get_slider_offset_from_diff_image(im)


def do_crack(wait, browser):
    try:
        slice_offset = slider_picture(browser)    # 获取滑块图片偏移量接口
        print'滑块图片的偏移量：', slice_offset

        images = browser.find_elements_by_class_name("gt_cut_fullbg_slice")    # 完整的背景图片对象列表
        image_style = images[0].get_attribute("style")
        match = re.match('background-image: url\("(.*?)"\); background-position: (.*?);', image_style)
        image_url = match.group(1)  # 获取无缺陷的背景图片url(乱序的背景图片)
        css = get_image_css(images)    # 返回的是每张完整的背景图片的position的值（list）  （完整的背景图片和有缺陷的背景图片的该值是一样的）

        images_bg = browser.find_elements_by_class_name("gt_cut_bg_slice")    # 有缺陷的背景图片对象列表
        image_bg_style = images_bg[0].get_attribute("style")   # 获取图片url（这里所有的图片都是一样的）
        match = re.match('background-image: url\("(.*?)"\); background-position: (.*?);', image_bg_style)
        image_bg_url = match.group(1)  # 获取有缺陷的背景图片url（乱序的背景图片）

        offset = get_slider_offset(image_url, image_bg_url, css)    # 通过两张图片获取背景图片中缺陷的偏移量 （image_url, image_bg_url是两张图片的url， css是position值）
        print '背景图中缺陷位置的偏移量：', offset

        knob = browser.find_element_by_class_name("gt_slider_knob")    # 滑动按钮
        fake_drag(browser, knob, offset - slice_offset)    # 通过获取滑块图片的偏移量和背景图片中凹槽的偏移量；然后进行滑块的滑动

        # 极验滑块验证码接口
        # time.sleep(2)
        # submit = wait.until(
        #     EC.element_to_be_clickable((By.XPATH, '//input[@id="embed-submit"]'))
        # )
        # submit.click()  # 点击登录
        # wait.until_not(EC.presence_of_element_located((By.XPATH, '//input[@id="embed-submit"]')),
        #                message='slider captcha failed, retry again')

        # 天眼查项目中进行滑块验证码是否成功检验
        wait.until(EC.presence_of_element_located((By.XPATH, '//a[@class="title link-white"]')),
                   message='slider captcha failed, retry again....')

    except WebDriverException as e:
        print 'WebDriverException异常：', e
        time.sleep(5)
        return do_crack(wait, browser)


def tianyancha():
    chrome_options = webdriver.ChromeOptions()
    # chrome_options.add_argument('--headless')
    # chrome_options.add_argument('no-sandbox')
    browser = webdriver.Chrome(
        executable_path=r'C:\Users\xj.xu\Downloads\chromedriver_win32\chromedriver.exe',
        chrome_options=chrome_options)
    # browser.maximize_window()
    wait = WebDriverWait(browser, 20)
    print '开始登录'
    browser.get('https://www.tianyancha.com/login')
    time.sleep(2)

    login_button = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@class="title-tab text-center"]/div[@class="title"]')),
                              message='password login ele not exist')
    login_button.click()
    # login_button.send_keys(Keys.ENTER)
    print '点击密码登录栏'
    time.sleep(2)
    tel = wait.until(
        EC.presence_of_element_located((By.XPATH, '//div[@class="modulein modulein1 mobile_box  f-base collapse in"]//div[@class="pb30 position-rel"]/input[@class="input contactphone"]'))
    )
    tel.send_keys('18668045631')
    password = wait.until(
        EC.presence_of_element_located((By.XPATH, '//div[@class="modulein modulein1 mobile_box  f-base collapse in"]//div[@class="input-warp -block"]/input[@class="input contactword input-pwd"]'))
    )
    password.send_keys('abcd1234')
    submit = wait.until(
        EC.element_to_be_clickable((By.XPATH, '//div[@class="modulein modulein1 mobile_box  f-base collapse in"]/div[@class="btn -hg btn-primary -block"]'))
    )
    submit.click()    # 点击登录
    time.sleep(10)

    do_crack(wait, browser)    # do_crack()接口   处理滑块验证码接口

    time.sleep(10)


def jiyan():
    '''
    极验验证码接口（通过极验验证码接口进行测试）
    :return:
    '''
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    browser = webdriver.Chrome(
        executable_path=r'C:\Users\xj.xu\Downloads\chromedriver_win32\chromedriver.exe',
        chrome_options=chrome_options)
    wait = WebDriverWait(browser, 20)
    browser.get('http://127.0.0.1:8000/')
    time.sleep(3)

    do_crack(wait, browser)    # do_crack()接口   处理滑块验证码接口

    time.sleep(2)
    # submit = wait.until(
    #     EC.element_to_be_clickable((By.XPATH, '//input[@id="embed-submit"]'))
    # )
    # submit.click()  # 点击登录


def main():
    tianyancha()
    # jiyan()


if __name__ == '__main__':
    main()
