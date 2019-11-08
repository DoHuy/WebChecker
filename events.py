import error
import time
import setting
import traceback

def calculate_duration(time, timeLater):
	duration    	= timeLater - time
	hour        	= int(duration/3600000)
	min        	= int((duration - hour*3600000)/60000)
	second      	= int((duration - min*60000 - hour*3600000)/1000)
	if hour     < 10:
		hour    = "0" + str(hour)
	if min      < 10:
		min     	= "0" + str(min)
	if second   < 10:
		second  = "0" + str(second)
	duration    	= str(hour) + ":" + str(min) + ":" + str(second)
	return duration

def statistics(hostName, statusCode, time, cursor, timeResponse,ipAddress,userId,webId,timeOK = 0):
	try:
		if statusCode < 400:
			timeOK = time

		sql     	= "SELECT timeOK, timeTOTAL, averageTime, times FROM statistic WHERE webId = %d"% (webId)
		cursor.execute(sql)
		result  = cursor.fetchall()

		if len(result) == 0:
			sql = "INSERT INTO statistic (hostName, timeOK, timeTOTAL, averageTime, ip, userId, webId, times) VALUES ('%s','%d', '%d', '%f', '%s', '%d', '%d', 1)"% (hostName, 0, 0, timeResponse, ipAddress, userId, webId)
			cursor.execute(sql)

		else:
			timeOK      	= result[0][0] + timeOK 
			averageTime   = float(result[0][2])  
			timeTOTAL   	= result[0][1] + time
			times 		= int(result[0][3])
			if statusCode <  400:
				averageTime = (result[0][2]*int(times) + timeResponse)/(int(times) + 1)
				times += 1
			sql         	= "UPDATE statistic SET timeOK = %d, timeTOTAL = %d, averageTime = '%f', times = %d WHERE webId = %d" %(timeOK, timeTOTAL, averageTime,times,webId)
			cursor.execute(sql)
	except Exception:
		error.catchError(traceback.format_exc(), sql)
		return

def insert_event(statusCode, hostName, timecheck, cursor, timeResponse, ipAddress, userId, webId):
	try:
		if statusCode < 400:
			status = "OK (%d)"%statusCode
			event  = "Up"
		else:
			status = "FALSE (%d)"%statusCode
			event  = "Down"

		if timeResponse > 10000:
			status = "OK (Slow Connection)"

		sql     	= "SELECT * FROM events WHERE  webId = %d ORDER BY time DESC" % (webId)
		cursor.execute(sql)
		result  = cursor.fetchall()
		if len(result) == 0:
			sql = "INSERT INTO events (event, hostName, reason, time, duration, userId, webId) VALUES ('%s', '%s' , '%s', '%d', '%s', '%d', '%d')"% ("Started",hostName, "OK", timecheck, "0:0:0", userId, webId)
			cursor.execute(sql)

			sql = "INSERT INTO events (event, hostName, reason, time, duration, lastCheck, userId, webId) VALUES ('%s', '%s' , '%s', '%d', '%s', '%d', '%d', '%d')"% (event,hostName, status, timecheck + 1, "0:0:0", timecheck + 1, userId, webId)
			cursor.execute(sql)

			statistics(hostName, statusCode, 0, cursor, timeResponse, ipAddress, userId, webId)
		else:
			triggerEvent    		= result[0][1]
			triggerHostName 	= result[0][2]
			triggerReason   	= result[0][3]
			triggerTime    	 	= result[0][4]
			triggerLast     		= result[0][6]
			statistics(hostName, statusCode, int(timecheck - triggerLast), cursor, timeResponse, ipAddress, userId, webId)
			flag = 1
			if statusCode == 408:
				if time.time() - setting.alert408[webId] < 300:
					flag = 0
				elif status != triggerReason:
					timecheck = timecheck - 12*60*500
			if flag == 1:
				duration        		= calculate_duration(triggerTime, timecheck)
	 			sql = " UPDATE events SET duration = '%s', lastCheck = %d WHERE time = %d AND  webId = %d" % (duration, timecheck,triggerTime,  webId)
				cursor.execute(sql)

				if status != triggerReason:
					sql = "INSERT INTO events (event, hostName, reason, time, duration, lastCheck, userId, webId) VALUES ('%s', '%s' , '%s', '%d', '%s', '%d', '%d', '%d')"% (event,hostName, status, timecheck, "0:0:0", timecheck, userId, webId)
					cursor.execute(sql)
	except Exception:
		error.catchError(traceback.format_exc(), sql)
		return
