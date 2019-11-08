import MySQLdb
import socket

openData    	= MySQLdb.connect('localhost','root','vnistadmin','webix')
MySQLCur    	= openData.cursor()		
query = "SELECT id, hostName FROM trackWebsite WHERE ip is NULL"
MySQLCur.execute(query)
res= MySQLCur.fetchall()
for each in res:
	try:
		ip = socket.gethostbyname(each[1])
	except:
		print "Failed to get IP of %s" %(each[1])
		pass
	else:
		print ip
		query = "UPDATE trackWebsite SET ip = '%s' WHERE id = %d" %(ip, int(each[0]))
		MySQLCur.execute(query)
openData.commit()