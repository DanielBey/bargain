#! /usr/bin/
# -*- coding: utf-8 -*-
'''
#=============================================================================
#     FileName: conf.py
#         Desc: 配置文件
#       Author: danielbey
#        Email: zbatbupt@163.com
#      Version: 0.0.1
#   LastChange: 2014-05-22
#=============================================================================
'''
# Web页面的ip
HOST_NAME = '127.0.0.1'

# Web页面的port
PORT_NUMBER = 8888

# Redis的ip
REDIS_IP = '127.0.0.1'

# Redis的port
REDIS_PORT = 6379

# Redis清空的频率
REDIS_FLUSH_FREQUENCE = 10

# 爬虫爬取的频率，默认为每5分钟爬取一次
CRAWLER_FREQUENCE_MINUTES = 5

# 短信通知的频率，默认为每10分钟检查一次，并抓取到符合要求的消息才会发短信
MESSAGE_FREQUENCE_MINUTES = 10

# Web页面筛选的关键词
WEB_FILETER_KEYS = (u'科颜氏', u'防晒')

# 短信通知筛选的关键词
MESSAGE_FILETER_KEYS = (u'科颜氏', u'防晒')

# 发件箱的域名
SEND_MAIL_POSTFIX = "163.com"

# 发件箱的smtp
SEND_MAIL_HOST = "smtp.163.com"

# 发件箱的用户名
SEND_MAIL_USER = ""

# 发件箱的密码
SEND_MAIL_PASSWORD = ""

# 发件箱的用户昵称
SEND_MAIL_USER_NAME = ""

# 139收件箱的用户名，即手机号
RECEIVE_MAIL_USER = ""

# 139收件箱的域名
RECEIVE_MAIL_POSTFIX = "139.com"


