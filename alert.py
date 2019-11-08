#!/usr/bin/env/python
# -*- coding: utf-8 -*-

import base64
import traceback
import setting
import error
import os
import time
import re
import psutil


from datetime import datetime

def check_diff(dic1, dic2):
	try:
		if dic1['Name'] != dic2['Name']:
			return 1
		elif dic1['tagName'] != dic2['tagName']:
			return 1
		elif dic1['oldContent'] != dic2['oldContent']:
			return 1
		else:
			return 0
	except UnicodeWarning:
			return 0
def check_status(db, alertType, url, webId):
	try:
		cur   = db.alert.find({
					"_type"            : url,
					"_index"          : setting.agentName,
					"type"              : alertType,
					"web_id"         : webId
			}).sort('update_at', -1)
		try:
			res = list(cur)[0]
			if res['events'][len(res['events']) - 1]['end_at'] == u"thời điểm hiện tại":
				res['events'][len(res['events']) - 1]['end_at'] = str(datetime.now().replace(microsecond=0)).replace(' ','T')
				db.alert.update({
						"_type"     	: url,
						"_index"    	: setting.agentName,
						"type"      	: alertType,
						"web_id"    	: webId,
						"update_at"  	: res['update_at']
					}, {"$set": {
						"events" 	: res['events'], 
						"update_at"	: time.time()
						}}, upsert = False)
		except:
			pass
	except Exception:
		error.catchError(traceback.format_exc())
		return

def update_last_check(db, alertType, url, webId, statusCode):
	try:
		cur   = db.alert.find({
						"_type"	: url,
						"_index"	: setting.agentName,
						"type"		: alertType,
						"status_code" 	: statusCode,
						"web_id"	: webId
			}).sort('update_at', -1)
		try:
			res = list(cur)[0]
			if (time.time() - int(res['insert_time'])) <= 60*60*24:
				db.alert.update({
						"_type"	: url,
						"_index"	: setting.agentName,
						"type"		: alertType,
						"status_code" 	: statusCode,
						"web_id"	: webId,
						"update_at"	: res['update_at']
					}, {"$set": {
						"update_at" 		: time.time()
						}}, upsert = False, multi = False)
		except:
			pass
	except Exception:
		error.catchError(traceback.format_exc())
		return

def take_shot(url, name, statusCode, id):
	try:
		driver 		= setting.webdriver.PhantomJS(service_args=['--ignore-ssl-errors=true', '--ssl-protocol=any', '--web-security=false'])
		driver.set_window_size(1280, 720)
		driver.set_page_load_timeout(150)
		try:
			#setting.threadLock.acquire()
			if isinstance(id, int):
				if not os.path.isfile("/var/www/html/web/app/alert_image/" + name + "_" +str(id)+"_"+ str(statusCode) + "_" +str(setting.date.day)+"-"+str(setting.date.month)+ "-" + str(setting.date.year) +".jpg"):
					driver.get(url)
					#setting.driver.execute_script('document.body.style.background = "white"')
					name = "/var/www/html/web/app/alert_image/" + name + "_" +str(id)+"_"+ str(statusCode) + "_" +str(setting.date.day)+"-"+str(setting.date.month)+ "-" + str(setting.date.year) +".jpg"
					driver.save_screenshot(name)
			else:
				if not os.path.isfile("/var/www/html/web/app/alert_image/" + name + "_" +str(id[0][0])+"_"+ str(statusCode) + "_" +str(setting.date.day)+"-"+str(setting.date.month)+ "-" + str(setting.date.year) +".jpg"):
					driver.get(url)
					for each in id:
						#setting.driver.execute_script('document.body.style.background = "white"')
						name = "/var/www/html/web/app/alert_image/" + name + "_" +str(each[0])+"_"+ str(statusCode) + "_" +str(setting.date.day)+"-"+str(setting.date.month)+ "-" + str(setting.date.year) +".jpg"
						driver.save_screenshot(name)
			driver.close()
			driver.quit()
			#setting.threadLock.release()
			return True
		except Exception:
			driver.close()
			driver.quit()
			#setting.threadLock.release()
			error.catchError(traceback.format_exc())
			return False
	except:
		for proc in psutil.process_iter():
			if proc.as_dict(attrs=['pid', 'name'])['name'] == 'phantomjs':
				proc.kill()
		return False

def describe_referer(alertType, status_code, severity):
	describe    	= "Lỗi không xác định"
	referer     	= "Undefined"
	alertName 	= "Lỗi không xác định"
	if "defaced" in alertType:
		describe    	= "Deface được định nghĩa là tấn công thay đổi nội dung, thông qua một điểm yếu nào đó, hacker sẽ thay đổi nội dung website của nạn nhân. Việc thay đổi nội dung này nhằm một số mục đích: cảnh báo website đang tồn tại lỗ hỏng bảo mật / điểm yếu nghiêm trọng, chứng tỏ năng lực bản thân, dạng này rất dễ gặp như kiểu hacked by…, thù hằn, nội dung thay đổi thường là lăng mạ nạn nhân hoặc nội dung liên quan đến chính trị, tôn giáo."
		referer     	= "www.google.com"
		if severity == 1:
			alertName 	= "Phát hiện thay đổi cấu trúc website"
		elif severity == 2:
			alertName 	= "Phát hiện nội dung bất thường trên website"
		elif severity == 3: 
			alertName 	= "Phát hiện dấu hiệu website bị thay đổi giao diện (deface)"
	elif status_code == 408:
		describe    	= "Lỗi 408 Request Timeout: lỗi này thông báo Server đã ngưng đáp ứng thông tin do quá thời gian quy định. Thông thường lỗi này là do Server xử lý thông tin chậm, đường truyền bị ngẽn hoặc là kích thước file yêu cầu quá lớn."
		referer     	= "https://httpstatuses.com/408"
		alertName 	= "Lỗi 408 Request Timeout"
	elif status_code == 200:
		describe    	= "Thời gian thiết lập kết nối giữa client và server quá dài."
		referer     	= "www.google.com"
		alertName 	= "Long Initial Connection Time"
	elif status_code == 400:
		describe    	= "Lỗi 400 Bad Request: Máy chủ không thể nhận dạng được yêu cầu. Lỗi này thường do trình duyệt xử lý không đúng. Bạn nên thử truy cập Website bằng trình duyệt khác."
		referer     	= "https://httpstatuses.com/400" 	
		alertName 	= "Lỗi 400 Bad Request"
	elif status_code == 401:
		describe    	= "Lỗi 401 Unauthorized: Lỗi cấp quyền truy cập tài liệu. Lỗi này có nghĩa là trình duyệt có thể kết nối đến website, nhưng bạn không có quyền truy cập tài liệu này."
		referer     	= "https://httpstatuses.com/401"
		alertName 	= "Lỗi 401 Unauthorized"
	elif status_code == 403:
		describe    	= "Lỗi 403 Forbidden: Máy chủ hiểu yêu cầu nhưng máy con không được phép nhận thông tin."
		referer     	= "https://httpstatuses.com/403"
		alertName 	= "Lỗi 403 Forbidden"
	elif status_code == 404:
		describe    	= "Lỗi 404 Not Found: Lỗi này có nghĩa là trình duyệt có thể kết nối đến website, nhưng không tìm thấy tài liệu bạn cần. Có thể trang web tạm thời không sẵn sàng hoặc website đã bị thay đổi."
		referer     	= "https://httpstatuses.com/404"
		alertName 	= "Lỗi 404 Not Found"
	elif status_code == 405:
		describe    	= "Lỗi 405 Method Not Allowed: Phương thức yêu cầu đã sử dụng không được chấp nhận ở server này."
		referer     	= "https://httpstatuses.com/405"
		alertName 	= "Lỗi 405 Method Not Allowed"
	elif status_code == 407:
		describe    	= "Lỗi 407 Proxy Authentication Required: Proxy yêu cầu kiểm tra quyền của bạn trước khi cho phép chuyển thông tin qua."
		referer     	= "https://httpstatuse.com/407"
		alertName  	= "Lỗi 407 Proxy Authentication Required"
	elif status_code == 500:
		describe 	= "Lỗi 500 Internal Server Error: Lỗi máy chủ nội bộ."
		referer 		= "https://httpstatuse.com/500"
		alertName 	= "Lỗi 500 Internal Server Error"
	elif status_code == 501:
		describe 	= "Lỗi 501 Not Implemented: Máy chủ không nhận ra và hỗ trợ phương thức truy cập từ gói tin."
		referer 		= "https://httpstatuse.com/501"
		alertName 	= "Lỗi 501 Not Implemented"
	elif status_code == 502:
		describe 	= "Lỗi 502 Bad Gateway: lỗi máy chủ bị nghẽn mạng hoặc do xảy ra sự cố nào đó."
		referer 		= "https://httpstatuse.com/502"
		alertName 	= "Lỗi 502 Bad Gateway"
	elif status_code == 503:
		describe 	= "Lỗi 503 Service Unavailable: Máy chủ dịch vụ tạm thời không hoạt động hoặc không xử lý được yêu cầu từ gói tin."
		referer 		= "https://httpstatuse.com/503"
		alertName 	= "Lỗi 503 Service Unavailable"
	elif status_code == 504:
		describe  	= "Lỗi 504 Gateway timeout: Lỗi cơ sở dữ liệu quá tải hoặc máy chủ  đang có vấn đề với kết nối hoặc một số lý do khác."
		referer 		= "https://httpstatuse.com/504"
		alertName 	= "Lỗi 504 Gateway timeout"
	elif status_code == 505:
		describe 	= "Lỗi 505 HTTP Version Not Supported: Máy chủ không hỗ trợ hoặc từ chối hỗ trợ đối với kiểu phiên bản HTTP trong gói tin."
		referer 		= "https://httpstatuse.com/505"
		alertName 	= "Lỗi 505 HTTP Version Not Supported"
	elif status_code == 507:
		describe 	= "Lỗi 507 Insufficient Storage: Yêu cầu không thể được xử lý bởi vì máy chủ không thể lưu trữ được thông tin cần thiết từ gói tin."
		referer 		= "https://httpstatuse.com/507"
		alertName  	= "Lỗi 507 Insufficient Storage"
	return describe, referer, alertName

def insert_alert(db, alertType, severity, des_ip, hostName, timeResponse, statusCode, webId, url, diff, suspicious, startTime):

	try:
		image_path = ""
		cur   = db.alert.find({
					"_type"     		: url, 
					"_index"    		: setting.agentName,
					"type"      		: alertType,
					"web_id"    		: webId
				}).sort('update_at',-1)
		flag = 0
		try:
			res   = list(cur)[0]
		except:
			flag = 1
		else:
			if (res['status_code'] != statusCode) or (res['type'] == 'defaced' and check_diff(diff, res['deface_at'])):
				if res['events'][len(res["events"]) -1]['end_at'] == u'thời điểm hiện tại':
					res['events'][len(res['events']) - 1]['end_at'] = str(datetime.now().replace(microsecond=0)).replace(' ','T')
					db.alert.update({
							"_type" 		: url,
							"_index"		: setting.agentName,
							"status_code"		: res['status_code'],
							"insert_time"		: res['insert_time'],
							"severity"		: res['severity'],
							"web_id"		: webId,
						},{"$set": {
							"events" 		: res['events'], 
							"update_at"		: time.time()
							}}, upsert = False)
					time.sleep(1)
				cur   = db.alert.find({
						"_type"     		: url, 
						"_index"    		: setting.agentName,
						"type"      		: alertType,
						"status_code"		: statusCode,
						"severity"		: severity,
						"web_id"    		: webId,
						'deface_at'		: diff,
						'dangerous_word'	: suspicious
					}).sort('update_at',-1)
				try:
					res 	= list(cur)[0]
				except: 
					flag 	= 1
			if flag == 0:
				if res['false_positive'] == 1 and res['type'] == "defaced" and not check_diff(res['deface_at'], diff):
					print "Detect FALSE ALERT"
					return False
	 			elif (time.time() - int(res['insert_time'])) > 60*60*24 :
					flag = 1
				elif  res['events'][len(res['events']) - 1]['end_at'] != u"thời điểm hiện tại" and res['false_positive'] == 0:
					temp = {"start_at": startTime, "end_at": "thời điểm hiện tại"}
					res['events'].append(temp)
					db.alert.update({
							"_type"     		: url,
							"_index"    		: setting.agentName,	
							"type"      		: alertType,
							"status_code" 		: statusCode,
							"insert_time" 		: res['insert_time'],
							"severity"		: res['severity'],
							"web_id"    		: webId
						}, {"$set": {
							"events" 		: res['events'], 
							"update_at"		: time.time()
							}}, upsert = False)
				else:
					update_last_check(db, alertType, url,  webId, statusCode)
		if flag == 1:
			if statusCode != 408 and statusCode != 200:
				image_path = hostName + "_" + str(webId)+"_"+ str(statusCode) + "_" +str(setting.date.day)+"-"+str(setting.date.month)+ "-" + str(setting.date.year) +".jpg"
				flag_image = os.path.isfile("/var/www/html/web/app/alert_image/" + hostName + "_" +str(webId)+"_"+ str(statusCode) + "_" +str(setting.date.day)+"-"+str(setting.date.month)+ "-" + str(setting.date.year) +".jpg")
				if flag_image == False:
					flag_image = take_shot(url, hostName, statusCode, int(webId))
					if flag_image == False:
						image_path = ""
			cur   = db.alert.find({
					"_type"    	: url, 
					"_index"    	: setting.agentName,
					"type"      	: alertType,
					"severity"	: severity,
					"web_id"    	: webId
				}).sort('update_at',-1)
			try:
				res   = list(cur)[0]
				if res['events'][len(res['events']) - 1]['end_at'] == u'thời điểm hiện tại':
					res['events'][len(res['events']) - 1]['end_at'] = str(datetime.now().replace(microsecond=0)).replace(' ','T')
					db.alert.update({
						"_type"     		: url,
						"_index"    		: setting.agentName,
						"type"      		: alertType,
						"insert_time" 	: res['insert_time'],
						"severity"		: res['severity'],
						"web_id"    		: webId
					}, {"$set": {
						"events" 		: res['events'], 
						"update_at"		: time.time()
						}}, upsert = False)
				time.sleep(1)
			except:
				pass
			describe, referer, alertName = describe_referer(alertType, statusCode, severity)
			# if severity == 3 and alertType == 'defaced': 
			# 	alertName = "Lỗi DEFACED - Có sự thay đổi trong cấu trúc website"
			# if severity == 4 and alertType == 'defaced':
			# 	alertName = "Lỗi DEFACED - Phát hiện từ nghi vấn trong cấu trúc website"
			alert = {
					'_type'         		: url,
					'_index'        		: setting.agentName,
					'type'          		: alertType,
					'name'          		: alertName,
					'is_alerted'    		: 0,
					'false_positive'	: 0,
					'severity'     	 	: severity,
					'dst_ip'        		: des_ip,
					'time_response' 	: timeResponse,
					'status_code'   	: statusCode,
					'description'   	: describe,
					'reference'     	: referer,
					'web_id'        		: webId,
					'host_name'		: hostName,
					'image_name'	: image_path,
					'events'		: [],
					'insert_time'		: int(time.time()),
					'deface_at'		: diff,
					'dangerous_word'	: suspicious
				}
			temp 			= {}
			temp['start_at'] 	= startTime
			temp['end_at']	= 'thời điểm hiện tại'
			alert['events'].append(temp)
			alert['update_at'] 	= time.time()
			db.alert.insert_one(alert)
		return True
	except Exception:
		error.catchError(traceback.format_exc())
		return

def ip_alert(oldIp, newIp, hostName, webId, db):
	setting.listHostIp[hostName] = 1
	try:
		cur   = db.alert.find({
						"_type"     		: hostName, 
						"_index"    		: setting.agentName,
						"type"      		: "ipchanged",
						"web_id"    		: webId,
						"new_ip"		: newIp
					}).sort('update_at',-1)
		try:
			res = list(cur)[0]
		except:
			alert = {
				'_type' 		: hostName,
				'_index'	: setting.agentName,
				'type'		: "ipchanged",
				'name'		: "Địa chỉ IP đã bị thay đổi",
				'is_alerted'	: 0,
				'false_positive'	: 0,
				'severity'	: 2,
				'old_ip'		: oldIp,
				'web_id'	: webId,
				'events'		: [],
				'insert_time' 	: int(time.time()),
				'new_ip'	: newIp,
				'host_name'	: hostName
			}
			temp = {}
			temp['start_at'] 	= str(datetime.now().replace(microsecond=0)).replace(' ', 'T')
			temp['end_at']		= 'thời điểm hiện tại'
			alert['events'].append(temp)
			alert['update_at']	= time.time()
			setting.db.alert.insert_one(alert)
		else:
			if res['false_positive'] == 1:
				print "DETECTED wrong ip alert"
				if newIp not in oldIp:
					oldIp = oldIp + ';' + newIp
					tmp = "UPDATE  trackWebsite SET ip = '%s' WHERE id = '%d'" % (oldIp, webId)
					setting.MySQLUpdate.append(tmp)
				return True
			else:
				setting.db.alert.update({
						"_type"     		: hostName,
						"_index"    		: setting.agentName,
						"type"      		: "ipchanged",
						"insert_time" 		: res['insert_time'],
						"web_id"    		: webId
					}, {"$set": {
						"update_at"		: time.time()
						}}, upsert = False)


		return False
			
	except Exception:
		error.catchError(traceback.format_exc())
		return
