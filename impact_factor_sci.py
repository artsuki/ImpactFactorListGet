# !/usr/bin/env python
# -*- coding: utf-8 -*-
# Created by Artsuki

'''
these codes utilized proxy, so it is recommended to use the proxy_pool file to get proxy first
'''

import urllib.request
import urllib.parse
from lxml import etree
import time
import random
import json
from multiprocessing.dummy import Pool as ThreadPool
import pandas as pd


def request_build(url):
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'}
    request = urllib.request.Request(url=url,headers=headers)
    return request

def opener_build():
    ip = random.choice(proxy_pool)
    handler = urllib.request.ProxyHandler({'http':ip})
    opener = urllib.request.build_opener(handler)
    return opener


class JournalList:
    def __init__(self,url):
        self.url = url
        self.journal_list = []
        
    def html_get(self):
        request = request_build(self.url)
        while True:
            opener = opener_build()
            try:
                self.response = opener.open(request,timeout=10.0).read()
            except Exception as e:
                print(f'{self.url} met {e}')
                time.sleep(1)
                continue
            else:
                break
        self.select = etree.HTML(self.response)
        time.sleep(1)
        return
    
    def list_get(self):
        journal_list = self.select.xpath("//div[@class='container']//div[@class='left-side']/div/ul/li/a/@href")
        for journal in journal_list:
            self.journal_list.append('https://www.scijournal.org/' + journal)
        return 


class JournalInfo:
    def __init__(self,url):
        self.url = url
    
    def info_get(self):
        request = request_build(self.url)        
        for i in range(11):
            opener = opener_build()
            try:
                self.response = opener.open(request,timeout=10.0).read()
            except Exception as e:
                print(f'{self.url} met {e}')
                time.sleep(1)
                continue
            else:
                self.select = etree.HTML(self.response)
                return
        self.select = False
        return
    
    def impact_factor(self,if_list):
        impact_factor = {}
        for i in range(len(if_list)):
            if_list[i] = if_list[i].split(" : ")
            if ' Impact Factor' in if_list[i][0]:
                if_list[i][0] = if_list[i][0].replace(' Impact Factor','')
            if ('NA' in if_list[i][1])|(not if_list[i][1]):
                if_list[i][1] = 0.0
            else:
                if_list[i][1] = float(if_list[i][1])
            impact_factor.update({f'{if_list[i][0]}':if_list[i][1]})
        return impact_factor
    
    def info_renew(self):
        if not self.select:
            return {'title':' ', 'abbrev':' ', 'ISSN':' ', 'IF':' ', 'link':' '}
        target = self.select.xpath("//div[@class='container']//div[@class='left-side']/div[@class='text-center']")
        self.title = target[0].xpath("./h2/text()")[0].replace(' Impact Factor', '')
        self.abbrev = target[0].xpath("./p[contains(text(),'Abbrev')]/text()")[0].split(':')[1].strip()
        self.issn = target[0].xpath("./p[contains(text(),'ISSN')]/text()")[0].split(':')[1].strip()
        if_list = target[0].xpath("./div/ul/li/span/text()")
        self.i_factor = self.impact_factor(if_list)
        return {'title':self.title, 'abbrev':self.abbrev, 'ISSN':self.issn, 'IF':self.i_factor, 'link':self.url}
        
      
with open('E:\MyCodes\MyData\proxy_pool.txt','r') as fp:
    proxy_pool = json.load(fp)
    
def journal_list_get(url):
    # 构建页面对象
    journal_list = JournalList(url)
    # 获取网页内容
    journal_list.html_get()
    # 解析网页内容，获得期刊链接列表
    journal_list.list_get()
    print(f'{journal_list.abbrev} parse done')
    return journal_list.journal_list

pool1 = ThreadPool()
terms = pool1.map(journal_list_get,url_list)
pool1.close()
pool1.join()

total_list = []
for i in terms:
    total_list.extend(i)
    
modified_list = []
for i in total_list:
    while '.-' in i:
        i = i.replace('.-','-')
    while '..' in i:
        i = i.replace('..','.')
    modified_list.append(i)
print(len(modified_list))


df = pd.DataFrame(columns=['title','abbrev','ISSN','IF','link'])
df.link = modified_list
df.fillna(value=' ',inplace=True)


def data_update(info):
    link = info['link']
    index = df[df['link']==link].index.values[0]
    df.at[index,'title']=info['title']
    df.at[index,'abbrev']=info['abbrev']
    df.at[index,'ISSN']=info['ISSN']
    df.at[index,'IF']=info['IF']
    return


def journal_info_get(url):
    journal_info = JournalInfo(url)
    journal_info.info_get()
    info = journal_info.info_renew()
    temp_info.append(info)
    data_update(info)
    print(f"{journal_info.abbrev} info get",end='     ')
    return info
    
temp_info = []

unprocessed_list = df[df['title']==' '].link.values.tolist()
print(len(unprocessed_list))

pool2 = ThreadPool(15)
total_info = pool2.map(journal_info_get,unprocessed_list)
print(len(total_info))
pool2.close()
pool2.join()


df.to_csv('IF_sci1.csv',index=False)
