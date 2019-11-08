#!/usr/bin/env/python
# -*- coding: utf-8 -*-

import setting
import error

import Node
import cPickle
import base64
import traceback
import re
import alert

from datetime import datetime
hot_word = ["hacked", "god verify", "security is low", "visited", "h4ck3r", "hack"]

def check_deface(newContent, url, name, ipAddress, webId, userId):
	try:
		flag                	= 0
		rawContent  	= base64.b64encode(newContent)

		newContent 	= newContent.strip()
		newContent 	= re.sub('</', '\n</', newContent)
		newContent 	= re.sub('>\s*<', '>\n<', newContent)
		newContent 	= re.sub('><', '>\n<', newContent)
		newContent 	= newContent.split('\n')

		newNode 	= Node.Node()
		newNode.import_object(newContent)
		newNode.importContent(newContent)
		try:
			result = setting.listWebData[webId]
		except:
			newNode = base64.b64encode(cPickle.dumps(newNode))
			update          	= "INSERT INTO webStruct (url, limitTime, isStructed, struct, webId, userId, object) VALUES ('%s' , '%d', '%d', '%s',  '%d', '%d', '%s')"%(url, 1, 0, rawContent, webId, userId, newNode)
			setting.listObject[webId] = (newNode, rawContent, webId)
		else:
			limitTime       	= result[0] 
			isStructed      	= int(result[1])
			struct 		= setting.listObject[webId][1]
			learningTime 	= setting.listLearnTime[webId]	
			if isStructed == 1:
				# confirmstruct 		= base64.b64decode(struct)
				# confirmstruct 		= confirmstruct.strip()
				# confirmstruct 		= re.sub('</', '\n</', confirmstruct)
				# confirmstruct		= re.sub('>\s*<', '>\n<', confirmstruct)
				# confirmstruct 		= re.sub('><', '>\n<', confirmstruct)
				# confirmstruct 		= confirmstruct.split('\n')
				# oldNode 		= Node.Node()
				# oldNode.import_object(confirmstruct, hostName)
				# oldNode.importContent(confirmstruct)
				oldNode 	= cPickle.loads(base64.b64decode(setting.listObject[webId][0]))
				oldNode, tmp    = find_struct(oldNode, newNode, 'C', ipAddress, name, webId, url)
				if tmp == 0:
					alert.check_status(setting.db, 'defaced', url, webId)
				else:
					newContent = oldNode.boderDiffHTML(newContent)
			else:
				oldNode 	= cPickle.loads(base64.b64decode(setting.listObject[webId][0]))
				oldNode, tmp    = find_struct(oldNode, newNode, 'F', ipAddress, name, webId, url)
				
				newContent   	= oldNode.render_html(newContent)
				struct  = ""
				for each in newContent:
					if each != None:
						struct += each + '\n'
				struct 		= base64.b64encode(struct) 
				if limitTime   <= 480*learningTime:
					limitTime       += 1			

				else:
					isStructed  = 1
					if tmp == 0:
						alert.check_status(setting.db, 'defaced', url, webId)
					else:
						newContent = oldNode.boderDiffHTML(newContent)
			
			oldNode 	= base64.b64encode(cPickle.dumps(oldNode))	
			update          	= "UPDATE webStruct SET isStructed = '%d', struct = '%s', limitTime = '%d', object = '%s' WHERE webId = '%d'"%(isStructed, struct, limitTime, oldNode, webId)
			setting.listObject[webId] = (oldNode, struct, webId)

		setting.MySQLUpdate.append(update)
			
	except RuntimeError:
		print "Hitted maximum recursion depth! Cannot save this object"
	except Exception:
		error.catchError(traceback.format_exc())
		return

		
def push_alert_data(Node1, Node2, name, hostName, webId, src_ip, url):
	flag = 0
	word = ""
	if name == "Different at sub Tag":
		diff = {
			"Name" 	: u"Số lượng thẻ con không giống nhau",
			"tagName" 	: Node1.name,
			"startAt" 	: Node1.startAt,
			"endAt"	: Node1.endAt,
			"oldContent"	: unicode("Bao gồm " + str(len(Node1.listChildren)) + " sub Tag", "utf-8"),
			"newContent" 	: unicode("Bao gồm " + str(len(Node2.listChildren)) + " sub Tag", "utf-8")
		}
		severity = 1
		for each in hot_word:
			if flag == 1:
				break
			for node in Node2.listChildren:
				try:	
					if each in node.attribute.lower() or each in node.content.lower():
						print "Level 3 alert"
						word = each
						flag = 1
						severity = 3
						break
				except:
					pass
	elif name == "Different at Attribute":
		diff = {
			"Name" 	: u"Tính chất của thẻ bị thay đổi ",
			"tagName" 	: Node1.name,
			"startAt" 	: Node1.startAt,
			"endAt"	: Node1.endAt,
			"oldContent"	: Node1.attribute,
			"newContent" : Node2.attribute
		}
		severity = 1
		for each in hot_word:
			if each in Node2.attribute.lower():
				word = each
				flag = 1
				severity = 2
	elif name == "Different at content":
		diff = {
			"Name" 	: u"Nội dung của thẻ bị thay đổi",
			"tagName"	: Node1.name,
			"startAt"	: Node1.startAt,
			"endAt"	: Node1.endAt,
			"oldContent"	: Node1.content,
			"newContent"	: Node2.content
		}
		severity = 1
		for each in hot_word:
			if each in Node2.content.lower():
				word = each
				flag = 1
				severity = 2
	else:
		diff = {
			"Name" 	: u"Tên của thẻ bị thay đổi",
			"tagName" 	: Node1.name,
			"startAt" 	: Node1.startAt,
			"endAt"	: Node1.endAt,
			"oldContent"	: Node1.attribute,
			"newContent"	: Node2.attribute
		}
		severity = 1
		for each in hot_word:
			if each in Node2.attribute.lower():
				word = each
				flag = 1
				severity = 2
	setting.threadLock.acquire()
	alert.take_shot(url, name, 0, int(webId))
	setting.threadLock.release()
	if flag == 0 :
		tmpQuery = ('defaced', severity, src_ip, hostName, 0, 0, webId, url, diff, None, str(datetime.now().replace(microsecond=0)).replace(' ','T'))
	else:
		tmpQuery = ('defaced', severity, src_ip, hostName, 0, 0, webId, url, diff, word, str(datetime.now().replace(microsecond=0)).replace(' ','T'))
	setting.MongoData.append(tmpQuery)


def find_struct(Node1, Node2, mode, src_ip, hostName, webId, link):
	Node1.startAt 	= Node2.startAt
	Node1.endAt 		= Node2.endAt
	if Node1.passed == 0:
		if ( Node1.deep == Node2.deep and Node1.name == Node2.name):
				if len(Node1.listChildren) != len(Node2.listChildren):
					if mode == 'F':
						Node1.passed = 1
						Node1.listChildren = Node2.listChildren
						for each in Node1.listChildren:
							each.delete  	= 1
					if mode != 'F' and Node1.delete == 0:
						Node1.border = 1
						push_alert_data(Node1,Node2, "Different at sub Tag", hostName,webId, src_ip, link)
						return	Node1, 1
						
				elif Node1.attribute != Node2.attribute:
					if mode == 'F':
						Node1.passed = 1
						Node1.delete 		= 1
					else:
						Node1.border = 1
						push_alert_data(Node1,Node2, "Different at Attribute", hostName,webId, src_ip, link)
						return	Node1, 1

				elif Node1.content != Node2.content:
					if mode == 'F':
						Node1.passed = 1
						Node1.delete = 1
					else:
						Node1.border = 1
						push_alert_data(Node1,Node2, "Different at content", hostName,webId, src_ip, link)
						return	Node1, 1
						
				else:
					for index in range(len(Node1.listChildren)):
						Node1.listChildren[index], stopCode = find_struct(Node1.listChildren[index], Node2.listChildren[index], mode, src_ip, hostName, webId, link)
						if stopCode == 1:
							return	Node1, 1

		else:
			if mode == 'F':
				Node1.passed = 1
				Node1.delete = 1
			else:
				Node1.border = 1
				push_alert_data(Node1,Node2, "Different at Deep or Name", hostName,webId, src_ip, link)
				return	Node1, 1
				
	return Node1, 0
