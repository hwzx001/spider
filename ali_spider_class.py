from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import csv
import urllib
import re
import math
import requests
import time
import random

class SPIDER():
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        self.driver=webdriver.Chrome(chrome_options=chrome_options)
    def __del__(self):
        self.driver.close()
    def scroll(self):
        # 将滚动条拉到底 加载网页
        for i in range(2, 1000):  # 也可以设置一个较大的数，一下到底
            js = "var q=document.documentElement.scrollTop={}".format(i * 100)  # javascript语句
            self.driver.execute_script(js)
    def crawl(self,url_array):
        #根据url爬取图片集
        s = 0
        for i in url_array:
            urllib.request.urlretrieve(i, '第%d张.jpg' % s)
            s += 1
    def get_detail_page(self,url):
        # 爬取详情页 return : text(str) res(array)
        self.driver.get(url)
        self.scroll()
        data = self.driver.find_element_by_class_name('details-info')
        raw_text = str(data.text).split('\n')
        text=[]
        for item in raw_text:
            text.append(item.strip())
        pic = self.driver.find_element_by_id('J-rich-text-description').find_elements_by_tag_name('img')
        res = []
        for i in pic:
            temp = i.get_attribute('src')
            if temp not in res:
                res.append(temp)
        return text, res
    def download_one_url(self,url):
        #获取单链图片集和简介
        self.driver.get(url)
        self.scroll()
        res = []  # 标题 价格 简介
        res.append(self.get_title())
        res.append(self.get_price_item())
        res.append(self.get_brief_introduction())
        pic = self.get_picurl()
        return res, pic
    def get_title(self):
        # 标题
        title = self.driver.find_element_by_class_name('ma-title').text
        return title
    def get_price_item(self):
        # 价格和起批量
        res = []
        amount = self.driver.find_element_by_class_name('ma-price-wrap').find_elements_by_class_name('ma-ladder-price-item')
        for i in amount:
            res.append(str(i.text).replace('\n',' '))
        return res
    def get_brief_introduction(self):
        intro=self.driver.find_element_by_class_name('ma-brief-list')
        return [intro.text]
    def pic_parse(self,raw_str):
        # 去除尺寸限定
        b = raw_str.split('.')
        b.remove(b[-2])
        c = '.'.join(b)
        return c
    def get_picurl(self):
        #获取图片地址
        lis = self.driver.find_elements_by_class_name('thumb')
        res = []
        lenlis=len(lis)
        if lenlis>=6:
            lenlis=6
        for i in range(lenlis):
            li = lis[i]
            pic = li.find_element_by_tag_name('img').get_attribute('src')
            res.append(self.pic_parse(pic))
        return res
    def validateTitle(self,title):
        rstr = r"[\.\/\\\:\*\?\"\<\>\|-]"  # './ \ : * ? " < > |'
        new_title = re.sub(rstr, "_", title)  # 替换为下划线
        return new_title
    def parse_title(self,title):
        # 获取合法标题
        raw_res = title.split('\n')
        res = []
        for i in range(len(raw_res)):
            if i % 2 == 0:
                res.append(self.validateTitle(raw_res[i]))
        return res
    def get_shop_name(self,url):  # 店铺名
        self.driver.get(url)
        raw_title = self.driver.find_element_by_class_name('cp-name')
        title = raw_title.text
        return self.validateTitle(title)
    def get_page_shop(self,shop_lst):
        # 给定商品链接数组，下载所有商品
        for j in range(len(shop_lst)):
            try:
                url = shop_lst[j]  # 单链地址
                res, pic = self.download_one_url(url)
            except:
                print(shop_lst[j], 'error')
            else:
                raw_name = str(res[0])
                name = self.validateTitle(raw_name)
                if not os.path.exists(name):
                    os.mkdir(name)
                    os.chdir(name)
                    csvfile = open(name + '表格.csv', 'w', encoding='utf-8',newline='')
                    writer = csv.writer(csvfile)
                    writer.writerow([name])
                    writer.writerow(['Price ＆ Amount：'])
                    for item in res[1]:
                        writer.writerow([item])
                    writer.writerow(['Brief Introduction：'])
                    briefintroduction=res[2]
                    for string in briefintroduction:
                        writer.writerow([string])
                    csvfile.close()
                    self.crawl(pic)
                    try:
                        detailtext, detailpic = self.get_detail_page(shop_lst[j])
                        # 详情页结果
                    except:
                        print('获取详情页出错')
                    else:
                        os.mkdir('详情页')
                        os.chdir('详情页')
                        f = open('detail.txt', 'w', encoding='utf-8')
                        for item in detailtext:
                            f.write(item)
                            f.write('\n')
                        f.close()
                        self.crawl(detailpic)
                        os.chdir('..')
                    os.chdir('..')
    def get_all_pages_url(self,class_url):
        # class_url 类地址  获取某个分类的所有分类页面 例如 第1,2,3,……页
        raw_res=[]
        self.driver.get(class_url)
        next_pagination_pages=self.driver.find_element_by_class_name('next-pagination-pages').find_element_by_class_name('next-pagination-list').find_elements_by_tag_name('a')
        for i in next_pagination_pages:
            raw_res.append(i.get_attribute('href'))
        if len(raw_res)<6:
            return raw_res
        else:
            res=[]
            pattern=re.compile(r'-([0-9]+)/')
            end=int(re.findall(pattern,str(raw_res[-1]))[0])
            string_p=raw_res[0]
            for i in range(1,end+1):
                res.append(re.sub(pattern,'-'+ str(i)+'/' , string_p))
            return res
    def get_some_shop_url(self,some_page_url):
        #获取某分类下所有商品链接
        self.driver.get(some_page_url)
        self.scroll()
        lst = self.driver.find_element_by_class_name('component-product-list').find_elements_by_tag_name('a')
        temphref = []
        for m in range(len(lst)):
            goodurl = lst[m].get_attribute('href')
            if goodurl not in temphref :
                temphref.append(goodurl)
        return temphref
    def get_class_shop(self,class_url,class_name):  # #class_url 类首地址  class_name类名
        # 下载某个分类
        os.mkdir(class_name)
        os.chdir(class_name)
        res = self.get_all_pages_url(class_url)
        for i in res:
            url = self.get_some_shop_url(i)
            self.get_page_shop(url)
        os.chdir('..')
        time.sleep(random.randint(1,5))


    def get_all_url(self,shop_url):
        #获取所有分类首页地址
        res=[]
        self.driver.get(shop_url)
        lst=self.driver.find_element_by_class_name('wrap-box').find_elements_by_tag_name('a')
        for i in lst:
            res.append(i.get_attribute('href'))
        return res

    def get_classname_and_classurl(self,shop_url):
        #获取类名相应链接
        self.driver.get(shop_url)
        all_kind = self.driver.find_element_by_class_name('mod-content')
        title=str(all_kind.text).split('\n')
        title_url=self.get_all_url(shop_url)
        if len(title)!=len(title_url):
            return [],[]
        else:
            return title,title_url
    def down_shop(self,shop_url):
        shop_name = self.get_shop_name(shop_url)
        print('已获取公司名称', shop_name)
        os.mkdir(shop_name)
        os.chdir(shop_name)
        title,hreflst=self.get_classname_and_classurl(shop_url)
        if title!=[] and hreflst!=[]:
            for i in range(len(title)):
                classname=title[i]
                print('正在下载', classname, '分类')
                self.get_class_shop(hreflst[i],classname)
                print('写入成功')
        else:
            print('获取店铺信息出错')

if __name__=="__main__":
    spi=SPIDER()
    shop_url='https://cnzg0113.en.alibaba.com/productlist.html?spm=a2700.icbuShop.88.17.6ce879caoa5LbN'
    spi.down_shop(shop_url)