import time

def catchError(Error,sql = None):
	fileError 	= open ('ERROR.txt', 'a')
	print "CATCHING ERROR"
	fileError.write(time.ctime(time.time()) + "\n" + Error )
	if sql != None:
		fileError.write('\n' + sql)
	fileError.close()