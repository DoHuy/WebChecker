#!/usr/bin/env/python
# -*- coding: utf-8 -*-

import Queue
import threading

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from elasticsearch import Elasticsearch
from pymongo import MongoClient


def init():
	global ESData 		# luu tru du lieu ES performance cua web 
	global MySQLEvent	# luu tru query bang? events trong MYSQL
	global MySQLUpdate	# luu tru query cap nhat du lieu trong MYSQL
	global MongoData	# luu tru du lieu canh bao trong mongo
	global exitFlag	# co`  nho' dung de dung cac thread
	global queue		# hang cho chua danh sach cac website can theo doi
	global es 		# con tro CSDL elastichsearch
	global headers
	global date		# luu tru ngay gio tren server
	global db 		# contro CSDL mongodb
	global startInsert 	# 
	global endInsert	#
	global agentName 	#
	global driver 		#
	global threadLock	# multithread lock
	global listHostIp
	global listObject
	global listLearnTime
	global listWebData
	global helpstat
	global startTime
	global alert408
	global tmpMySQLEvent
	global tmpMongoData
	global tmpElasticSearch


	ESData 	= []
	tmpMySQLEvent = {}
	tmpMongoData = {}
	tmpElasticSearch = {}
	MySQLEvent 	= []
	MySQLUpdate 	= []
	MongoData	= []
	listLearnTime 	= {}
	requestResult 	= {}
	listObject 	= {}
	listWebData 	= {}
	alert408 	= {}
	listHostIp	= {}
	exitFlag 	= 0
	requestResult  = {}
	queue 		= Queue.Queue(0)
	es 		= Elasticsearch()
	helpstat 	= 0
	startTime 	= 0
	dcap 		= dict(DesiredCapabilities.PHANTOMJS)
	driver 		= webdriver.PhantomJS(desired_capabilities=dcap, service_args=['--ignore-ssl-errors=true', '--ssl-protocol=any', '--web-security=false'])
	driver.set_window_size(1280, 720)
	driver.set_page_load_timeout(60)

	headers     	= {
		'X-Real-IP'  : '1.1.1.1',
		'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) coc_coc_browser/50.0.125 Chrome/44.0.2403.125 Safari/537.36'
	}

	client 		= MongoClient()
	db 		= client['webix']

	agentName   	= "VNIST WEBCHECKER"

	threadLock  	= threading.Lock()
