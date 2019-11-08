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
		print "Thread-%d: started" % self.id
		while not setting.exitFlag:
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
					sql = "UPDATE trackWebsite SET status = %d WHERE hostName = '%s' AND protocol = '%s' AND port = '%s'" % (0,data['hostName'], data['protocol'], data['port'])
					setting.MySQLUpdate.append(sql)
					pass
				else:
					if ipAddress != '127.0.0.1': 
						link        = self.modify_link(data['hostName'], data['protocol'])
						link        = link + ":" + data['port']
						self.check(link,data['hostName'],str(ipAddress),data['port'], data['userId'], data['id'], data['protocol'], data['status'])
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


	def check(self,link,hostName,ipAddress,port, userId, webId, protocol, prevStatus):
		sql 		= ""
		statusCode  	= 0
		state       	= 0
		timeAVG     	= 0
		warning     	= ""
		severity 	= ""
		timecheck   	= (time.time())*1000
		flag 		= 1
		fail 		= 0
		lastTime 	= time.time()
		try:
			for loop in range(2):
				try:
					# print str(time.ctime()) + " : Requesting to " + hostName
					r = requests.get(link, allow_redirects = True, headers = setting.headers, verify = False, timeout = 20)
					# print str(time.ctime()) + " : Done " + hostName

				except:
					if fail == 0:
						fail += 1
					else:
						print "%s : Fail to check " % datetime.now(), link
						warning     	= "Request Timeout"
						timeAVG     	= 0.0
						statusCode  	= 408
						state 		= 0
						link 		= None
						severity 	= "medium"
						try:
							lastTime = setting.alert408[hostName]
						except KeyError:
							setting.alert408[hostName] = time.time()
				else:
					try:
						del setting.alert408[hostName]
					except KeyError:
						pass

					timeAVG     = r.elapsed.total_seconds()*1000
					if r.status_code == 200:
						state       	= 1

						if timeAVG > 10000:
							warning     	= "Long Initial Connection Time"
							severity 	= "low"
						else:
							for web in webId:
								alert.check_status(setting.db, "performance", hostName, web[0])
							warning     	= "Normal"
							i 		= 0
							# print str(time.ctime()) + " : Checking deface " + hostName
							for user in userId:
								deface.check_deface(r.content,hostName, ipAddress, webId[i][0], user[0], link)
								i += 1
							# print str(time.ctime()) + " : Done " + hostName
						i = 0
						for user in userId:
							action = {
								"_index" 		: "user-%d" % user[0],
								"_type"			: "web-%d" % webId[i][0],
								"_id"			: timecheck,
								"_source" 		:{
									'host_name' 	: hostName,
									'ip'		: ipAddress,
									'port'		: int(port),
									'state'		: state,
									'time_res'	: timeAVG,
									'status_code' 	: r.status_code,
									'warning'	: warning,
									'time'		: timecheck,
									'user_id'	: user[0],
									'web_id'	: webId[i][0]
									}
							}
							i += 1
							setting.ESData.append(action)
					elif r.status_code > 399 and r.status_code < 500:
						warning         	= "Client Error"
						timeAVG         	= 0.0
						severity 	= "medium"
						# print str(time.ctime()) + " : Taking pic " + hostName
						for eachid in webId:
							alert.take_shot(hostName, link, r.status_code, eachid[0])
						state = 0
						flag = 0
						# print str(time.ctime()) + " : Done " + hostName
						
					elif r.status_code >= 500:
						warning         	= "Internal Server Error"
						timeAVG         = 0.0
						severity 	= "high"
						# print str(time.ctime()) + " : Taking pic " + hostName
						for eachid in webId:
							alert.take_shot(hostName, link, r.status_code, eachid[0])
						state = 0
						# print str(time.ctime()) + " : Done " + hostName
						flag = 0
					statusCode  = r.status_code
					break
			i = 0
			if statusCode == 408 :
				if time.time() - lastTime > 600:
					flag = 0
					state = 0
					setting.MySQLEvent += setting.tmpMySQLEvent[hostName]
					del setting.tmpMySQLEvent[hostName]
					for user in userId:
						tmpSQL = (statusCode, hostName, timecheck, timeAVG, ipAddress, user[0], webId[i][0])
						setting.MySQLEvent.append(tmpSQL)
						i += 1

				else:
					try:
						setting.tmpMySQLEvent[hostName]
					except KeyError:
						setting.tmpMySQLEvent[hostName] = []
					for user in userId:
						tmpSQL = (statusCode, hostName, timecheck, timeAVG, ipAddress, user[0], webId[i][0])
						setting.tmpMySQLEvent[hostName].append(tmpSQL)
						i += 1
			else:
				for user in userId:
					tmpSQL = (statusCode, hostName, timecheck, timeAVG, ipAddress, user[0], webId[i][0])
					setting.MySQLEvent.append(tmpSQL)
					i += 1

			if flag == 0:
				for web in webId:
					tmpMongo = ('performance', severity, ipAddress, hostName, timeAVG, statusCode, web[0], link, None, None)
					setting.MongoData.append(tmpMongo)
			
			if prevStatus != state:
				sql = "UPDATE trackWebsite SET status = %d WHERE hostName = '%s' AND protocol = '%s' AND port = '%s'" % (state,hostName, protocol, port)
				setting.MySQLUpdate.append(sql)
		except Exception:
			error.catchError(traceback.format_exc())
			return
