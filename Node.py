# import setting

import re
import requests
import time
sefl_closing = ['area', 'base', 'br', 'col', 'command', 'embed', 'hr',
 				'img', 'img', 'input', 'keygen', 'link', 'meta','param',
 				'source', 'track', 'wbr']
class Node:
	def __init__(self, deep = 0, order = 0, name = "", attribute = None,startAt = -1, endAt = -1):
		self.deep 		= deep
		self.delete 		= 0
		self.attribute 		= attribute
		self.startAt	    	= startAt
		self.order 		= order
		self.endAt 		= endAt
		self.name 		= name
		self.current 		= -1
		self.listChildren 	= []
		self.content		= ""
		self.border	 	= 0
		self.passed 		= 0
		# self.html 		= []

	def render_html(self, html):
		# html la 1 mang ma cac phan tu cua no la 1 dong trong source code HTML
		if self.delete == 1:
			for index in range(self.startAt - 1, self.endAt):
				if index < len(html) and index >= 0:
					html[index] = None
		else:
			for each in self.listChildren:
				html = each.render_html(html)
		return html

	def import_object(self, content):
		# tu du lieu content, content la 1 mang chua 1 dong cua du lieu html da duoc phan tich  , tao ra bien object node 
		self.name = 'root'
		stack 	 = []
		end 	 = 1
		line 	 = 0
		endS	 = 1
		order 	 = 0
		total 	 = 0
		for each in content:
			total += 1
		prevNode = [None]*total*3
		for each in content:
			each = each.strip()
			line += 1
			if '<!--' in each:
				end = 0
			if '-->' in each or '--!>' in each:
				end = 1
				continue
			if end == 1:
				tags = re.findall('</[a-zA-Z0-9]*|<[a-zA-Z0-9]*', each)
				for tag in tags:
					tag = tag[1:len(tag)].lower()
					if tag:	
						if tag in sefl_closing:
							order += 1
							self.listChildren.append(Node(len(stack) + 1, order, tag, each, line, line))
							self.current += 1
							prevNode[order] = self 
						else:
							tagtmp = tag
							if stack:
								if tag == 'script':
									endS = 0
								if tag == '/script':
									endS = 1
								if "/" in tag:
									tags1 = tag[1:]
									if tags1 in stack:
										while 1:
											try:
												if tag == "/" + stack[len(stack) - 1]:

													stack.pop()
													self.endAt = line
													self = prevNode[self.order]
													break
												else:
													stack.pop()
													self.endAt = line -1
													self = prevNode[self.order]
											except:
												break
									continue
							if tag == 'script' and endS == 0:
								order += 1
								stack.append(tagtmp)
								self.listChildren.append(Node(len(stack), order, tag, each))
								self.current += 1
								prevNode[order] = self
								self 	= self.listChildren[self.current]
								self.startAt = line
							elif endS == 0:
								continue
							elif "/" not in tag:
								order += 1
								stack.append(tagtmp)
								self.listChildren.append(Node(len(stack), order, tag, each))
								self.current += 1
								prevNode[order] = self
								self 	= self.listChildren[self.current]
								self.startAt = line
					if tag == 'script':
						break
	

	def boderDiffHTML(self, html):
		if self.border == 1:
			html = html[:(self.startAt-1)] + ['<div style="border: solid red">'] + html[(self.startAt - 1):self.endAt] + ['</div>'] + html[self.endAt:]
		else:
			for each in self.listChildren:
				html = each.boderDiffHTML(html)
		return html 

	def importContent(self, html):
		if self.listChildren:
			for each in self.listChildren:
				each = each.importContent(html)
		else:
			if self.startAt != -1 and self.endAt != -1:
				for index in range(self.startAt - 1, self.endAt):
					if index < len(html) and len(html[index]) > 0 and index >= 0:
						self.content += html[index].strip() + "\n"
					#else:
					#	f = open('INDEXERROR.txt', 'a')
					#	f.write(str(index) + "_" + hostName + "_"+str(len(html)))
					#	f.close()
					#	pass

	def selfPrint(self, f):
		f.write(self.name + "_" + str(self.startAt) + "_" + str(self.endAt))
		if self.listChildren:
			for each in self.listChildren:
				each.selfPrint(f)

	def selfPrint(self, f):
		try:
			f.write("\n" + self.name + "_" + str(self.startAt) + "_" + str(self.endAt))
			f.write("\n" + self.attribute)
		except:
			pass

		if self.listChildren:
			for each in self.listChildren:
				each.selfPrint(f)
