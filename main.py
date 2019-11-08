#Standard Library
import traceback
import sys
import MySQLdb
import time
import psutil
import threading
import os

from threading import Thread
from elasticsearch import helpers
from elasticsearch import Elasticsearch
from datetime import datetime
from pymongo import MongoClient
from urlparse import urlparse

#Custome Library
import worker
import setting
import events
import alert
import error

reload(sys)  
sys.setdefaultencoding('utf8')

def get_help():
	f = open("help.txt", "w")
	f.write("need to restart\n")
	f.close()

def clean_data():
	for proc in psutil.process_iter():
		if proc.as_dict(attrs=['pid', 'name'])['name'] == 'phantomjs':
			proc.kill()

def thread_insert_data_ElasticSearch():
	times = 0
	while 1:
		print str(time.ctime()) + " Checking Data ES"
		
		try:
			if len(setting.ESData) > 0:
				print str(time.ctime()) + " Inserting Data ES"
			while len(setting.ESData) > 0:
				try:
			 		#print setting.ESData
					while len(setting.ESData) > 100:
						tmp = setting.ESData[0:100]
						helpers.bulk(setting.es, tmp)
						for i in range(0,100):
							setting.ESData.pop(0)
					helpers.bulk(setting.es, setting.ESData)

				except:
					times += 1
					if times > 3:
						setting.es = Elasticsearch()
						break
					print traceback.format_exc()
					print "Failed. Trying Again"
					pass
				else:
					del setting.ESData[:]
					print str(time.ctime()) + " Inserted Data ElasticSearch"
					times = 0
			if setting.helpstat == 1:
				f = open("help.txt", "a")
				f.write("Done ES\n")
				f.close()
			time.sleep(60)

		except KeyboardInterrupt:
			print "Cancel Inserting Data ElasticSearch"
			return

		except:
			error.catchError(traceback.format_exc())
			print "Error while inserting ElasticSearch"
			return

def thread_insert_data_MongoDb():
	cnt = 0
	while 1:
		print str(time.ctime()) + " Checking Data MongoDb"
		
		try:
			if len(setting.MongoData) > 0:
				print str(time.ctime()) + " Inserting Data MongoDb"
			while len(setting.MongoData) > 0:
				data = setting.MongoData[0]
				POT = alert.insert_alert(setting.db, data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10])
				if POT == False:
					alert.check_status(setting.db, 'defaced', data[3], data[6])
					sql = "UPDATE webStruct SET isStructed = 0 where webId = '%d'" % data[6]
					setting.MySQLUpdate.append(sql)
				setting.MongoData.pop(0)
				cnt += 1
			if cnt > 0:
				print str(time.ctime()) + " Inserted Data MongoDb"
				cnt = 0
			if setting.helpstat == 1:
				f = open("help.txt", "a")
				f.write("Done Mongo\n")
				f.close()
			time.sleep(60)

		except KeyboardInterrupt:
			print "Cancel Inserting Data MongoDb"
			return

		except:
			error.catchError(traceback.format_exc())
			print "Error while inserting MongoDb"
			setting.client 		= MongoClient()
			setting.db 		= setting.client['webix']
			time.sleep(60)
			pass

def thread_insert_data_MySQL():
	# global actions, MySQLEvent, MySQLQuery, MongoQuery
	# client     	= MongoClient()
	# db          	= client['webix'] 
	openData    	= MySQLdb.connect('localhost','root','vnistadmin','webix')
	MySQLCur    	= openData.cursor()
	cnt 		= 0
	while 1:
		print str(time.ctime()) + " Checking Data MySQL"
		
		try:
			if len(setting.MySQLUpdate) > 0 or len(setting.MySQLEvent) > 0:
				print str(time.ctime()) + " Inserting Data MySQL"
			while len(setting.MySQLUpdate) > 0:
				query = setting.MySQLUpdate[0]
				MySQLCur.execute(query)
				setting.MySQLUpdate.pop(0)
				cnt += 1
			while len(setting.MySQLEvent) > 0:
				data = setting.MySQLEvent[0]
				events.insert_event(data[0], data[1], data[2], MySQLCur,data[3], data[4], data[5], data[6])
				setting.MySQLEvent.pop(0)
				cnt += 1
			openData.commit()
			if cnt > 0:
				print str(time.ctime()) + " Inserted Data MYSQL"
				cnt = 0
			if setting.helpstat == 1:
				f = open("help.txt", "a")
				f.write("Done MySQL\n")
				f.close()
			time.sleep(60)

		except KeyboardInterrupt:
			print "Cancel Inserting Data"
			return

		except:
			error.catchError(traceback.format_exc(), query)
			print "Error while inserting MySQL Data"
			openData    	= MySQLdb.connect('localhost','root','vnistadmin','webix')
			MySQLCur    	= openData.cursor()
			time.sleep(60)
			pass
def force_to_restart():
	while 1:
		while setting.startTime != 0:
			if time.time() - setting.startTime > 150:
				setting.helpstat = 1
				get_help()
				setting.startTime = 0
			time.sleep(50)	
def get_mysql_data():
	connect        	= MySQLdb.connect('localhost','root','vnistadmin','webix')
	cur                 	= connect.cursor()	
	threadMySQL 		= Thread(target = thread_insert_data_MySQL, args = ())
	threadMySQL.start()
	threadMongoDb	= Thread(target = thread_insert_data_MongoDb, args = ())
	threadMongoDb.start()
	threadElasticSearch 	= Thread(target = thread_insert_data_ElasticSearch, args = ())
	threadElasticSearch.start()
	threadRestart 		= Thread(target = force_to_restart, args = ())
	threadRestart.start()
	print threading.enumerate()
	cur.execute("SELECT object, struct, webId FROM webStruct")
	res_obj = cur.fetchall()
	for each in res_obj:
		setting.listObject[each[2]] = each
	while 1:
		setting.date 	= datetime.now()
		setting.exitFlag = 0
		try:
			threadworker    = []

			with connect:
				try:
					cur.execute("SELECT limitTime, isStructed, webId FROM webStruct")
					res_web = cur.fetchall()
					for each in res_web:
						setting.listWebData[each[2]] = each
					cur.execute("SELECT learningTime, id FROM trackWebsite")
					res_id = cur.fetchall()
					for each in res_id:
						setting.listLearnTime[each[1]] = each[0]
					cur.execute("SELECT DISTINCT  name,url,status, ip FROM trackWebsite" )
					result_Host 	= cur.fetchall()
					print "Processing " + str(len(result_Host)) +" website"
					index = 1
					for each in result_Host:
						#print "Index: %d 	- Domain: %s" %( index, each[1])
						index += 1
						hostName            	= each[1]
						temp                	= {}
						temp['status']	= each[2]
						temp['ip']		= each[3]
						temp['url']		= hostName
						res = urlparse(hostName)
						# if "http://" in hostName:
						# 	hostName 	= hostName.replace("http://","")
						# if "https://" in hostName:
						# 	hostName 	= hostName.replace("https://","")
						temp['name']        	= each[0]
						temp['hostName']    	= res.netloc 
						sql = "SELECT userId from trackWebsite WHERE url = '%s'"% (each[1])
						cur.execute(sql)
						res = cur.fetchall()
						temp['userId'] = res
						sql = "SELECT id from trackWebsite WHERE url = '%s'"% (each[1])
						cur.execute(sql)
						res = cur.fetchall()
						temp['id'] = res
						setting.queue.put(temp)
						#print temp
					connect.commit()
				except:
					error.catchError(traceback.format_exc())
					print "QUERYING DATABASE ERROR"
					sys.exit()
			startTime 	= time.time()
			qsize 		= setting.queue.qsize()
			print "Creating 100 Thread"
			for i in range(0,100):
				threadworker.append(worker.worker(i))
				threadworker[i].start()
			while not setting.queue.empty():
				time.sleep(3)
				print "%f s -------- %d s ------ queue size: %d -------- active thread: %d" %(time.time() - startTime, 20*qsize, setting.queue.qsize(), threading.active_count())
				if time.time() - startTime >  20*qsize:
					while not setting.queue.empty():
						setting.queue.get()
					break
				pass 
			setting.exitFlag = 1
			time.sleep(30)
			print "Killing alll"
			setting.startTime = time.time()
			while threading.active_count() > 7:
				for x in threadworker:
					x.join(0.5)
					Thread._Thread__stop(x)
			setting.startTime = 0
			print "All thread are closed!"
			print "active thread: %d" % (threading.active_count())
			print threading.enumerate()
			time.sleep(150)

		except KeyboardInterrupt:	
			print "\nYou press Ctrl + C\nProgram terminated"
			setting.exitFlag = 1
			connect.close()
			for t in threadworker:
				t.join(10)
			Thread._Thread__stop(threadMySQL)
			Thread._Thread__stop(threadMongoDb)
			Thread._Thread__stop(threadElasticSearch)
			Thread._Thread__stop(threadRestart)
			sys.exit()

		except Exception:
			error.catchError(traceback.format_exc())
			connect.close()
			sys.exit()

if __name__ == '__main__':
	clean_data()
	setting.init()
	get_mysql_data()
