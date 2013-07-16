#-----------------------------------------------------------------------------------
# MySignature Sublime Text Plugin
# Author: Elad Yarkoni
# Version: 1.0
# Description: Sublime text autocomplete improvements: 
#				- showing javascript methods with parameters
#-----------------------------------------------------------------------------------
import sublime, sublime_plugin, os, re, threading
import codecs
from os.path import basename

#
# Method Class
#
class Method:
	_name = ""
	_signature = ""
	_filename = ""
	def __init__(self, name, signature, filename, hintStr, className):
		self._name = name
		self._filename = filename;
		self._signature = signature
		self._hintStr = hintStr
		self._className = className
	def name(self):
		return self._name
	def signature(self):
		return self._signature
	def filename(self):
		return self._filename
	def hintStr(self):
		return self._hintStr
	def className(self):
		return self._className

#
# MySign Class
#
class MySign:
	_functions = []
	MAX_WORD_SIZE = 100
	MAX_FUNC_SIZE = 50
	def clear(self):
		self._functions = []
	def addFunc(self, name, signature, filename, hintStr, className):
		self._functions.append(Method(name, signature, filename, hintStr, className))
	def get_autocomplete_list(self, word):
		autocomplete_list = []
		for method_obj in self._functions:
			if (word in method_obj.name()) or (word in method_obj.className()):
				method_str_to_append = method_obj.name() + '(' + method_obj.signature()+ ')'
				if method_obj.className() != "":
					method_str_to_append = method_obj.className() + ":" + method_str_to_append
				method_file_location = method_obj.filename();
				method_str_hint = method_obj.name() + '(' + method_obj.hintStr() + ')'
				autocomplete_list.append((method_str_to_append + '\t' + method_file_location,
					method_str_hint)) 
		return autocomplete_list


def is_lua_file(filename):
	return '.lua' in filename

#
# MySign Collector Thread
#
class MySignCollectorThread(threading.Thread):
	
	def __init__(self, collector, open_folder_arr, timeout_seconds):  
		self.collector = collector
		self.timeout = timeout_seconds
		self.open_folder_arr = open_folder_arr
		threading.Thread.__init__(self)

	#
	# Get all method signatures
	#
	def save_method_signature(self, file_name):
		file_lines = codecs.open(file_name,'rU','utf-8')
		for line in file_lines:
			if "function" in line:
				matches = re.search('function\s*(\w+):(\w+)\s*\((.*)\)', line)
				matches2 = re.search('function\s*(\w+)\s*\((.*)\)', line)
				m = None
				if matches != None and (len(matches.group(2)) < self.collector.MAX_FUNC_SIZE and len(matches.group(3)) < self.collector.MAX_FUNC_SIZE):
					m = matches
					signIndex = 3
					className = matches.group(1)
				elif matches2 != None and (len(matches2.group(1)) < self.collector.MAX_FUNC_SIZE and len(matches2.group(2)) < self.collector.MAX_FUNC_SIZE):
					m = matches2
					signIndex = 2
					className = ""
				if m != None:
					paramLists = m.group(signIndex)
					params = paramLists.split(',')
					stHint = ""
					count = 1
					for param in params:
						stHint = stHint + "${" + str(count) + ":" + param + "}"
						if count != len(params):
							stHint += ","
						count = count + 1

					self.collector.addFunc(m.group(signIndex-1), m.group(signIndex), basename(file_name), stHint, className)

	#
	# Get Javascript files paths
	#
	def get_luascript_file(self, dir_name, *args):
		fileList = []
		for file in os.listdir(dir_name):
			dirfile = os.path.join(dir_name, file)
			if os.path.isfile(dirfile):
				fileName, fileExtension = os.path.splitext(dirfile)
				if fileExtension == ".lua":
					fileList.append(dirfile)
			elif os.path.isdir(dirfile):
				fileList += self.get_luascript_file(dirfile, *args)
		return fileList

	def run(self):
		for folder in self.open_folder_arr:
			luafiles = self.get_luascript_file(folder)
			for file_name in luafiles:
				self.save_method_signature(file_name)

	def stop(self):
		if self.isAlive():
			self._Thread__stop()

#
# MySign Collector Class
#
class MySignCollector(MySign, sublime_plugin.EventListener):

	_collector_thread = None

	#
	# Invoked when user save a file
	#
	def on_post_save(self, view):
		self.clear()
		open_folder_arr = view.window().folders()
		if self._collector_thread != None:
			self._collector_thread.stop()
		self._collector_thread = MySignCollectorThread(self, open_folder_arr, 30)
		self._collector_thread.start()
	#
	# Change autocomplete suggestions
	#
	def on_query_completions(self, view, prefix, locations):
		current_file = view.file_name()
		completions = []
		if is_lua_file(current_file):
			return self.get_autocomplete_list(prefix)
			completions.sort()
		return (completions,sublime.INHIBIT_EXPLICIT_COMPLETIONS)