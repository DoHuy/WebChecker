
import os
import time

while 1:
	try:
		stat = os.stat("help.txt")
	except:
		pass
	else:
		if stat.st_size > 40:
			print str(time.ctime()) + " Prepare to restart webChecker"
			os.system("rm help.txt")
			os.system("service webChecker restart")
			time.sleep(5)
					
	time.sleep(60)
