from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import csv
import urllib
import re
import math
import requests

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
        data = self.driver.find_element_by_css_selector(
            '#site_content > div.grid-main > div > div.mod.mod-offerDetailContext2.app-offerDetailContext2.app-type-default.mod-ui-not-show-title > div > div.m-content > div > div > div > div > div.widget-custom.offerdetail_w1190_description')
        text = data.text
        pic = data.find_element_by_xpath('//*[@id="desc-lazyload-container"]').find_elements_by_tag_name('img')
        res = []
        for i in pic:
            temp = i.get_attribute('src')
            if temp not in res:
                res.append(temp)
        return text, res
    def download_one_url(self,url):
        #获取单链图片集和详情页内容
        self.driver.get(url)
        self.scroll()
        res = []  # 标题 价格 起批量 型号 详情
        res.append([self.get_title()])
        res.append(self.get_price())
        res.append(self.get_amout())
        res.append(self.get_size())
        res.append(self.get_detail())
        pic = self.get_picurl()
        return res, pic
    def get_amout(self):
        # 起批量
        res = []
        amount = self.driver.find_elements_by_xpath('//*[@id="mod-detail-price"]/div/table/tbody/tr[2]')
        for i in amount:
            res.append(i.text)
        return res
    def get_title(self):
        # 标题
        title = self.driver.find_element_by_xpath('//*[@id="mod-detail-title"]/h1').text
        return title
    def get_price(self):
        # 价格
        price = self.driver.find_elements_by_xpath('//*[@id="mod-detail-price"]/div/table/tbody/tr[1]')
        res = []
        for i in price:
            res.append(i.text)
        return res
    def get_size(self):
        # 尺码
        res = []
        size = self.driver.find_elements_by_xpath('//*[@id="mod-detail-bd"]/div[2]/div[13]/div/div/div/div[2]/div[2]')
        for item in size:
            res.append(item.text)
        return res
    def get_detail(self):
        # 获取详细信息
        detail = self.driver.find_elements_by_xpath(
            '//*[@id="site_content"]/div[1]/div/div[1]/div/div[2]/div/div/div/div/div[3]')
        res = []
        for item in detail:
            res.append(item.text)
        return res
    def getcsv(self,filename):
        csvfile = open(filename, 'w', newline='', encoding='utf-8')
        writer = csv.writer(csvfile)
        writer.writerow(['Title', self.get_title()])
        price = self.get_price()
        for i in price:
            writer.writerow(i)
        csvfile.close()
    def pic_parse(self,raw_str):
        # 去除尺寸限定
        b = raw_str.split('.')
        b.remove(b[-2])
        c = '.'.join(b)
        return c
    def get_picurl(self):
        #获取图片地址
        lis = self.driver.find_elements_by_css_selector('.vertical-img')
        res = []
        for i in range(6):
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
    def get_all_pages_url(self,class_url, class_number):
        # class_url 类地址 class_number 数目 获取某个分类的所有分类页面 例如 第1,2,3,……页
        if int(class_number) <= 16:
            res = []
            res.append(class_url)
            return res
        else:
            self.driver.get(class_url)
            cata = self.driver.find_element_by_class_name('pagination')
            src = cata.find_elements_by_tag_name('a')
            class_url_res = []
            for i in src:
                temp = i.get_attribute('href')
                if temp != 'javascript:;':
                    class_url_res.append(temp)
            res = []
            pages = int(math.ceil(int(class_number) / 16))  # 每页有16个产品
            temp_url = str(class_url_res[0])
            p = re.compile(r'=[0-9]+#')
            for i in range(1, pages + 1):
                res.append(re.sub(p, '=' + str(i) + '#', temp_url))
            return res
    def get_page_shop(self,shop_lst):
        # 给定商品链接数组，下载所有商品
        for j in range(len(shop_lst)):
            try:
                url = shop_lst[j]  # 单链地址
                res, pic = self.download_one_url(url)
            except:
                print(shop_lst[j], 'error')
            else:
                raw_name = str(res[0][0])
                name = self.validateTitle(raw_name)
                if not os.path.exists(name):
                    os.mkdir(name)
                    os.chdir(name)
                    csvfile = open(name + '表格.csv', 'w', encoding='utf-8')
                    writer = csv.writer(csvfile)
                    for item in res:
                        writer.writerow(item)
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
                        f.write(detailtext)
                        f.close()
                        try:
                            self.crawl(detailpic)
                        except:
                            print("下载详情页图片出错")
                        os.chdir('..')
                    os.chdir('..')
    def get_some_shop_url(self,some_page_url):
        #获取某分类下所有商品链接
        self.driver.get(some_page_url)
        self.scroll()
        lst = self.driver.find_element_by_xpath(
            '//*[@id="search-bar"]/div[2]/div/div/div/ul').find_elements_by_tag_name(
            'a')
        temphref = []
        for m in range(len(lst)):
            goodurl = lst[m].get_attribute('href')
            if goodurl not in temphref and 'page' not in goodurl:
                temphref.append(goodurl)
        return temphref
    def get_class_shop(self,class_url, class_number,class_name):  # #class_url 类地址 class_number 数目 class_name类名
        # 下载某个分类
        os.mkdir(class_name)
        os.chdir(class_name)
        res = self.get_all_pages_url(class_url, class_number)
        for i in res:
            url = self.get_some_shop_url(i)
            self.get_page_shop(url)
        os.chdir('..')
    def get_shop_name(self,url):  # 店铺名
        self.driver.get(url)
        raw_title = self.driver.find_element_by_class_name('company-name')
        title = raw_title.get_attribute('title')
        return self.validateTitle(title)
    def get_all_url(self,hreflst):
        #获取所有分类首页地址
        if len(hreflst) == 0:
            return []
        else:
            res = []
            for i in hreflst:
                temp=i.get_attribute('href')
                if temp not in res and str(temp).count('_')==1:
                    res.append(temp)
            return res
    def get_classname_and_classurl(self,shop_url):
        #获取类名、数量、相应链接
        self.driver.get(shop_url)
        all_kind = self.driver.find_elements_by_xpath(
            '//*[@id="site_content"]/div[1]/div/div[2]/div/div[2]/div[3]/div[2]/div/ul/li[1]/ul')
        if len(all_kind) != 0:
            #获取标题
            raw_title = all_kind[0].text
            title = self.parse_title(raw_title)
            #获取数目
            num_res_session = self.driver.find_elements_by_class_name('wp-category-list-item')
            num_res = []
            for i in range(len(title) ):
                num_res.append(
                    num_res_session[i].find_element_by_class_name('wp-category-title-text').find_element_by_class_name(
                        'wp-category-count').text[1:-1])
            #获取链接
            href = all_kind[0].find_elements_by_tag_name('a')
            hreflst = self.get_all_url(href)
            return title,num_res,hreflst
        else:
            return [],[],[]
    def down_shop(self,shop_url):
        shop_name = self.get_shop_name(shop_url)
        print('已获取公司名称', shop_name)
        os.mkdir(shop_name)
        os.chdir(shop_name)
        title, num_res, hreflst=self.get_classname_and_classurl(shop_url)
        print(title,num_res,hreflst)
        if title!=[] and num_res!=[] and hreflst!=[]:
            for i in range(len(title)):
                classname=title[i]
                print('正在下载', classname, '分类')
                self.get_class_shop(hreflst[i],num_res[i],classname)
                print('写入成功')
        else:
            print('获取店铺信息出错')

if __name__=="__main__":
    sip=SPIDER()
    shops='https://shop36510729p4205.1688.com/page/offerlist.htm?spm=a261y.7663282.0.0.362945a4mrGh2E'
    sip.down_shop(shops)
    '''
    class_url='https://shop1438188905282.1688.com/page/offerlist_-2.htm?spm=a2615.7691456.autotrace-categoryNavNew.23.7f401800z3gO0y'
    sip.get_class_shop(class_url,32,'newtest')'''