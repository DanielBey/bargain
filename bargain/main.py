#! /usr/bin/env python
# -*- coding: utf-8 -*-


from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from bs4 import BeautifulSoup
from apscheduler.scheduler import Scheduler
from email.mime.text import MIMEText
from confbar import *

import smtplib
import sys
import email
import re
import redis
import requests #requests是python的一个HTTP客户端库，跟urllib，urllib2类似但是API非常简洁
import os


class HttpHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        crawler = Crawler()
        page = crawler.generate_page()
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(page)
        return


class Crawler:

    def __init__(self):
        self.rs = redis.Redis(host=REDIS_IP, port=REDIS_PORT)
        self.http_querys = (
                                {
                                    'host' : 'http://bbs.byr.cn',
                                    'url'  : 'http://bbs.byr.cn/board/Advertising',
                                    'headers' : {
                                        "X-Requested-With" : "XMLHttpRequest",
                                    },
                                    'href' : "^/article/Advertising/\d+$",
                                },
                                #XMLHttpRequest对象可以在不向服务器提交整个页面的情况下，实现局部更新网页。
                                #当页面全部加载完毕后，客户端通过该对象向服务器请求数据，服务器端接受数据并处理后，向客户端反馈数据。
                                
                            )
    #返回当前URL下所有a标签指向的非置顶帖的完整的URL
    def _parse_html_to_urls(self, host, url, headers, href):
        #得到请求对象r
        r = requests.get(url, headers=headers)
        #得到BeautifulSoup对象frs_soup里面是返回网页的内容
        frs_soup = BeautifulSoup(r.text)#BeautifulSoup将 html文档类似 dom文档树一样处理
        frs_attrs = {
            'href' : re.compile(href),
            'title' : None,
            'target' : None,
        }
        frs_res = frs_soup.findAll('a', frs_attrs)#返回所有满足href正则匹配的a标签的列表
        urls = []
        for res in frs_res:
            if res.parent.parent.get('class')!='top':
                res['href'] = host + res['href']
                urls.append(res)
        print urls
        #os.system("pause")
        #返回a标签的列表
        return urls
    
    #urls是该页面下除去置顶的帖子以外剩下的帖子所在的a标签
    def _put_urls_into_redis(self, urls):
        for url in urls:
            title = url.string #利用beautifulsoup中的string属性得到标签中的内容也就是帖子的标题名
            #print title
            #os.system("pause")
            #filter(function, sequence)：对sequence中的item依次执行function(item)，
            #将执行结果为True的item组成一个List/String/Tuple（取决于sequence的类型）返回
            if filter(lambda x: x in title, WEB_FILETER_KEYS):#检查每个关键词是否在title中出现
                #只要有一个关键词出现if就为真
                self.rs.sadd('web_urls', url)#将这个关键词所在的URL放入redis的web_urls键代表的集合中
                #os.system("pause")
            #对于标题中含有短信关键字且不在过期短信集合中的URL放到redis的当前短信urls键代表的集合中
            if filter(lambda x: x in title, MESSAGE_FILETER_KEYS) and not self.rs.sismember('outdated_message_urls', url):
                self.rs.sadd('current_message_urls', url)
                #os.system("pause")
    #每次执行爬虫模块的时候都会检查一下，如果已经爬了10次了，就清空web_urls键代表的集合         
    def _delete_web_urls_if_needed(self):
        if int(self.rs.get('times')) >= REDIS_FLUSH_FREQUENCE: 
            self.rs.delete('web_urls')
            self.rs.delete('times')

    #取出当前短信URL集合中的数据
    def _get_message_urls_from_redis(self):
        ret = self.rs.smembers('current_message_urls')
        urls = ""
        for herf in ret:
            urls += herf + "<br>"
        return len(ret), urls

    def _get_web_urls_from_redis(self):
        ret = self.rs.smembers('web_urls')
        urls = ""
        for herf in ret:
            urls += "<tr><td>" + herf + "</td></tr>"
        return urls

    #将当前短信URL移到过期短信URL当中，并将当前短信URL清空
    def _refresh_message_urls_in_redis(self):
        self.rs.sunionstore('outdated_message_urls', 'current_message_urls', 'outdated_message_urls')
        self.rs.delete('current_message_urls')

    def generate_page(self):
        return '''
                <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Welcome to spider!</title>
                        <link href="//cdnjs.bootcss.com/ajax/libs/twitter-bootstrap/2.3.1/css/bootstrap.min.css" rel="stylesheet">
                        <style>
                            body {
                                width: 35em;
                                margin: 0 auto;
                            }
                            .table-hover tbody tr:hover > td,
                                .table-hover tbody tr:hover > th {
                                background-color: #D2DAFF;
                            }
                            a:visited { color: red; }
                        </style>
                    </head>
                    <body>
                        <h3>信息筛选</h3>
                        <h4 class="text-info">红色链接为您已打开过的链接</h4><hr>
                        <div class="well well-large">
                            <table class="table table-hover">
                                <tbody>
                                    %s
                                </tbody>
                            </table>
                    </body>
                </html>
                ''' % self._get_web_urls_from_redis()

    def send_massage(self):
        msg_num, content = self._get_message_urls_from_redis()
        if msg_num <= 0 :
            print "none messages to send..."
            return
        sub = "抓取到%d条信息" % msg_num
        send_mail_address = SEND_MAIL_USER_NAME + "<" + SEND_MAIL_USER + "@" + SEND_MAIL_POSTFIX + ">"
        msg = MIMEText(content, 'html', 'utf-8')
        msg["Accept-Language"]="zh-CN"
        msg["Accept-Charset"]="ISO-8859-1, utf-8"
        msg['Subject'] = sub
        msg['From'] = send_mail_address
        msg['to'] = to_adress = "139SMSserver<" + RECEIVE_MAIL_USER + "@" + RECEIVE_MAIL_POSTFIX + ">"#139SMSserver是收件人的昵称
        try:
            stp = smtplib.SMTP()
            stp.connect(SEND_MAIL_HOST)#发件箱的smtp
            stp.login(SEND_MAIL_USER, SEND_MAIL_PASSWORD)
            stp.sendmail(send_mail_address, to_adress, msg.as_string())
            print "send message sucessfully..."
            self._refresh_message_urls_in_redis()
        except Exception, e:
            print "fail to send message: "+ str(e)
        finally:
            stp.close()

    def runCrawler(self):
        print "start crawler ..."
        self.rs.incr('times')#将key为times的value +1
        self._delete_web_urls_if_needed()#如果times > 10则清空
        for http_query in self.http_querys :
            urls = self._parse_html_to_urls(http_query['host'], http_query['url'], http_query['headers'], http_query['href'])
            #os.system("pause")
            #print urls
            #os.system("pause")
            #包括将含有网页关键字的url放入redis中网页url键所对应的集合
            #以及将含有短信关键字的url放入redis中短信url键所对应的集合
            self._put_urls_into_redis(urls)
            #os.system("pause")
        print "finish crawler ..."


if __name__ == '__main__':

    crawler = Crawler()
    crawler.runCrawler()
    #os.system("pause")
    sched = Scheduler()
    sched.start()
    sched.add_interval_job(crawler.runCrawler, hours=CRAWLER_FREQUENCE_MINUTES)
    sched.add_interval_job(crawler.send_massage, seconds=MESSAGE_FREQUENCE_MINUTES)


    try:
        print "start server ..."
        #创建并监听HTTP套接字，分配requests到处理器HttpHandler
        server = HTTPServer((HOST_NAME, PORT_NUMBER), HttpHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print "finish server ..."
        server.socket.close()
