
import os, fnmatch, gzip
import shutil, datetime


base = '/var/www/core/webChecker/'
file = 'ERROR.txt'

def find_and_delete():
	result = []
	for root, dirs, files in os.walk(base):
		for name in files:
			if fnmatch.fnmatch(name, "*ERROR.tar.gz"):
				result.append(os.path.join(root, name))
	min = result[0]
	for each in result:
		if min > each:
			min = each

	if len(result) > 5:
		os.remove(min)		

def calculate_and_compress():
	try:
		info = os.stat(base + 'ERROR.txt')
		print info.st_size
		size = info.st_size
		if size > 10000000:
			time = datetime.datetime.now().strftime("%b %d %y %H-%M-%S")
			with open(base + 'ERROR.txt', 'rb') as f_in, gzip.open(base + str(time) + ' ERROR.tar.gz', 'wb') as f_out:
	    			shutil.copyfileobj(f_in, f_out)
	    		os.remove(base + 'ERROR.txt')
	except:
		print "File is not exist"
		return

calculate_and_compress()
find_and_delete()