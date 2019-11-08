#!/usr/bin/env/python
# -*- coding: utf-8 -*-

import setting
import deface
import alert
import error

import threading
import socket
import MySQLdb
import time
import traceback
import requests
import urllib3

from datetime import datetime
from threading import Thread
requests.packages.urllib3.disable_warnings()
urllib3.disable_warnings()

class worker(threading.Thread):
	
	def __init__(self, id):
		threading.Thread.__init__(self)
		self.stoprequest = threading.Event()
		self.id 		= id

	def run(self):
		while not setting.exitFlag:
			startThreadTime = time.time()
			setting.threadLock.acquire()
			if not setting.queue.empty():
				data        = setting.queue.get()
				setting.threadLock.release()
				try:
					# print str(time.ctime()) + " : Getting IP of " + data['hostName']
					ipAddress   = socket.gethostbyname(data['hostName'])
					# print str(time.ctime()) + " : IP of " + data['hostName'] + " is "+ str(ipAddress)
				except:
					# print str(time.ctime()) + " : Fail to get IP of " + data['hostName']
					sql = "UPDATE trackWebsite SET status = %d WHERE url = '%s'" % (0,data['url'])
					setting.MySQLUpdate.append(sql)
					pass
				else:
					if ipAddress != '127.0.0.1': 
						# link        = self.modify_link(data['hostName'], data['protocol'])
						# link        = link + ":" + data['port']
						self.check(data['url'],data['name'],str(ipAddress), data['userId'], data['id'], data['status'])			
						print "Thread %d need %f s to finish checking %s" % (self.id, time.time() - startThreadTime, data['url'])

			else:
				setting.threadLock.release()

	def join(self, timeout=None):
		self.stoprequest.set()
		super(worker, self).join(timeout)

	def modify_link(self,link, protocol):
		text 	= protocol + "://" 
		if text not in link:
			link    = text + link
		if link[len(link)-1]!='/':
			link    = link + '/'
		link    	= link[:len(link)-1]
		return link   


	def check(self,url,name, ipAddress, userId, webId, prevStatus):
		sql 		= ""
		statusCode  	= 0
		state       	= 0
		timeAVG     	= 0
		warning     	= ""
		severity 	= 0
		timecheck   	= (time.time())*1000
		flag 		= 1
		fail 		= 0
		lastTime 	= time.time()
		try:
			# print "%d - dong 88: - %s" %(self.id, hostName) 
			for loop in range(2):
				try:
					r = requests.get(url, allow_redirects = True, headers = setting.headers, verify = False, timeout = 20)

				except:
					# print "%d - dong 94: - %s" %(self.id, hostName) 
					if fail == 0:
						fail += 1
					else:
						# print "%s : Fail to check " % datetime.now(), link
						warning     	= "Request Timeout"
						timeAVG     	= 0.0
						statusCode  	= 408
						state 		= 0
						link 		= None
						severity 	= 2
						for web in webId:
							try:
								lastTime = setting.alert408[web[0]]
							except KeyError:
								setting.alert408[web[0]] = time.time()
								continue
					# print "%d - dong 111: - %s" %(self.id, hostName) 
				else:
					# print "%d - dong 113: - %s" %(self.id, hostName) 
					for web in webId:
						try:
							del setting.alert408[web[0]]
							del setting.tmpMongoData[web[0]]
						except KeyError:
							# for web in webId:
							# 	print web[0]
							# print setting.alert408
							continue
					# print "%d - dong 119: - %s" %(self.id, hostName) 
					timeAVG     = r.elapsed.total_seconds()*1000
					if r.status_code == 200:
						state       	= 1

						if timeAVG > 10000:
							warning     	= "Slow Connection"
							severity 	= 1
						else:
							# print "%d - dong 128: - %s" %(self.id, hostName) 
							for web in webId:
								alert.check_status(setting.db, "performance", url, web[0])
							# print "%d - dong 131: - %s" %(self.id, hostName) 
							warning     	= "Normal"
							i 		= 0
							# print str(time.ctime()) + " : Checking deface " + hostName
							# print "%d - dong 135: - %s" %(self.id, hostName) 
							for user in userId:
								deface.check_deface(r.content,url, name, ipAddress, webId[i][0], user[0])
								i += 1
							# print "%d - dong 139: - %s" %(self.id, hostName) 
					elif r.status_code > 399 and r.status_code < 500:
						warning         	= "Client Error"
						timeAVG         	= 0.0
						severity 	= 2
						# print str(time.ctime()) + " : Taking pic " + hostName
						# print "%d - dong 145: - %s" %(self.id, hostName) 
						alert.take_shot( url, name, r.status_code, webId)
						# print "%d - dong 148: - %s" %(self.id, hostName) 
						state = 0
						flag = 0
						# print str(time.ctime()) + " : Done " + hostName
						
					elif r.status_code >= 500:
						warning         	= "Internal Server Error"
						timeAVG         = 0.0
						severity 	= 3
						# print str(time.ctime()) + " : Taking pic " + hostName
						# print "%d - dong 158: - %s" %(self.id, hostName) 
						alert.take_shot(url, name, r.status_code, webId)
						# print "%d - dong 161: - %s" %(self.id, hostName) 
						state = 0
						# print str(time.ctime()) + " : Done " + hostName
						flag = 0
					statusCode  = r.status_code
					break
			i = 0
			# print "%d - dong 168: - %s" %(self.id, hostName) 
			for user in userId:
				action = {
					"_index" 		: "user-%d" % user[0],
					"_type"		: "web-%d" % webId[i][0],
					"_id"			: timecheck,
					"_source" 		:{
						'name' 	: name,
						'ip'		: ipAddress,
						'state'		: state,
						'time_res'	: timeAVG,
						'status_code' : statusCode,
						'warning'	: warning,
						'time'		: timecheck,
						'user_id'	: user[0],
						'web_id'	: webId[i][0]
						}
			 		}
				i += 1
				setting.ESData.append(action)
			# print "%d - dong 189: - %s" %(self.id, hostName) 
			i = 0
			if statusCode == 408 :
				if time.time() - lastTime > 300:
					flag = 0
					state = 0
					print time.time() - lastTime

				else:
					for web in webId:
						try:
							setting.tmpMongoData[web[0]]
							print "Adding more Query of id: %d" % (web[0])
						except KeyError:
							print "Creating TMP Query for 408 Error of %s" %(name)	
							setting.tmpMongoData[web[0]] = []
							continue
					i = 0
					for web in webId:
						tmpMongo = ('performance', severity, ipAddress, name, timeAVG, statusCode, web[0], url, None, None, str(datetime.now().replace(microsecond=0)).replace(' ','T'))
						setting.tmpMongoData[web[0]].append(tmpMongo)
				# print "%d - dong 226: - %s" %(self.id, hostName) 
			# print "%d - dong 232: - %s" %(self.id, hostName) 
			for user in userId:
				tmpSQL = (statusCode, url, timecheck, timeAVG, ipAddress, user[0], webId[i][0])
				setting.MySQLEvent.append(tmpSQL)
				i += 1
			if flag == 0:
				for web in webId:
					try:
						setting.MongoData += setting.tmpMongoData[web[0]]
						del setting.tmpMongoData[web[0]]
					except KeyError:
						continue
					
				for web in webId:
					tmpMongo = ('performance', severity, ipAddress, name, timeAVG, statusCode, web[0], url, None, None, str(datetime.now().replace(microsecond=0)).replace(' ','T'))
					setting.MongoData.append(tmpMongo)
			# print "%d - dong 244: - %s" %(self.id, hostName) 
			if prevStatus != state:
				sql = "UPDATE trackWebsite SET status = %d WHERE url = '%s'" % (state, url)
				setting.MySQLUpdate.append(sql)
			# print "End: %d - dong 248: - %s" %(self.id, hostName) 
		except Exception:
			error.catchError(traceback.format_exc())
			return
