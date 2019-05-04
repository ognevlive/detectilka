import os, sys, re, argparse
import exiftool
import pandas
import xml.etree.ElementTree as ET
import zipfile as zf
from hashlib import md5


class FoldersFiles():
	def __init__(self, paths):
		self.files_list = []
		if paths is None:
			print("[*] Error: Path is None.")
			return
		self.paths = paths
		self.file_number = 0

	def crawle_folders(self):
		for path in self.paths:
			self.file_number += self.find_files(path)

	def find_files(self, path):
		file_number = 0
		for file in os.listdir(path):
			if file == sys.argv[0]:
				continue
			# if file_number == 10:
			# 	break
			new_path = path + '/' + file
			if os.path.isfile(new_path) and os.access(new_path, os.R_OK):
				file_number += 1
				if re.match(r'.*.((docx)|(DOCX))', file):
					self.files_list.append(new_path)
			else:
				file_number += self.find_files(new_path)
		return file_number

class CollectCharacteristics():
	def __init__(self, good_files, bad_files):
		self.database = []
		self.all_tags = []
		self.good_files = good_files
		self.bad_files = bad_files
		self.docMeta = ['File:FileSize','XMP:Creator','XML:Characters','XML:CharactersWithSpaces','XML:Company','XML:CreateDate','XML:LastModifiedBy','XML:LastPrinted','XML:ModifyDate','XML:Pages','XML:RevisionNumber','XMP:Title','XML:TotalEditTime','XML:Words']
		self.incorrect_files = []

	def get_meta(self, file):
		with exiftool.ExifTool() as et:
			metadata = et.get_metadata(file)
		
		character = []
		file_name = metadata['SourceFile']
		for characteristic in self.docMeta:
			try:
				ch = metadata[characteristic]
			except:
				ch = ""
			character.append(ch)
		return character

	def get_tags(self, file, check=0):
		try:
			z = zf.ZipFile(file)
		except zf.BadZipfile as exception:
			raise Exception('BadZipFile')

		f = z.open("word/document.xml")
		tree = ET.parse(f)

		tags = []
		for elem in tree.iter():
			tags.append(elem.tag.split('}')[-1])
		tags = list(set(tags))

		if check == 1:
			have_tags = []
			for tag in self.all_tags:
				if tag in tags:
					have_tags.append(1)
				else:
					have_tags.append(0)
			return have_tags
		else:
			return tags

	def get_characteristics(self, type='folder'):
		self.collect_all_tags()
		i = 1
		files_len = len(self.good_files)
		for file in self.good_files:
			info = []
			meta_info = self.get_meta(file)
			try:
				tags_info = self.get_tags(file, check=1)
			except Exception as ex:
				if type == 'file': return 1
				continue

			info += meta_info
			info += tags_info

			data = open(file, 'rb').read()
			info.append(md5(data).hexdigest())
			info.append(0)

			self.database.append(info)
			i += 1
		print('[!] Success loaded %d good docx files' % i)

		i = 1
		files_len = len(self.bad_files)
		for file in self.bad_files:
			info = []
			meta_info = self.get_meta(file)
			try:
				tags_info = self.get_tags(file, check=1)
			except Exception as ex:
				if type == 'file': return 1
				continue

			info += meta_info
			info += tags_info

			data = open(file, 'rb').read()
			info.append(md5(data).hexdigest())
			info.append(1)

			self.database.append(info)
			i += 1
		print('[!] Success loaded %d malware docx files' % i)
		return 0

	def collect_all_tags(self):
		files = self.good_files + self.bad_files
		files_len = len(files)
		i = 1
		for file in files:
			try:
				tags = self.get_tags(file, check=1)
			except Exception as ex:
				continue
			self.all_tags += tags
			self.all_tags = list(set(self.all_tags))
			i += 1


root_path = 'classificator/docx/'

def run(good, bad, output):
	finder = FoldersFiles([good])
	finder.crawle_folders()
	good_files = finder.files_list


	finder = FoldersFiles([bad])
	finder.crawle_folders()
	bad_files = finder.files_list

	database = []

	collector = CollectCharacteristics(good_files, bad_files)
	collector.get_characteristics()
	database += collector.database

	columns = ['FileSize', 'Creator', 'Characters', 'CharactersWithSpaces', 'Company', 'CreateDate', 'LastModifiedBy', 'LastPrinted', 'ModifyDate', 'Pages', 'RevisionNumber', 'Title', 'TotalEditTime', 'Words'] + collector.all_tags + ['MD5', 'Malicious']
	db = pandas.DataFrame(database, columns = columns)
	db.to_csv(output, encoding = 'utf-8')

	template_db = pandas.DataFrame(columns = columns)
	template_db.to_csv(root_path + 'template.csv', encoding = 'utf-8')


def run_file(file, output):
	path = 'uploads/' + file

	database = []
	collector = CollectCharacteristics([path], [])
	if collector.get_characteristics('file') != 0:
		# Invalid file
		return 1

	database += collector.database

	template_db = pandas.read_csv(root_path + 'template.csv', encoding='utf-8')

	columns = ['FileSize', 'Creator', 'Characters', 'CharactersWithSpaces', 'Company', 'CreateDate', 'LastModifiedBy', 'LastPrinted', 'ModifyDate', 'Pages', 'RevisionNumber', 'Title', 'TotalEditTime', 'Words'] + collector.all_tags + ['MD5', 'Malicious']
	db = pandas.DataFrame(database, columns = columns)

	df = pandas.DataFrame(columns=template_db.columns)

	for col in db.columns:
		if col not in df.columns:
			del db[col]

	for col in df.columns:
		if col.find('Unnamed') != -1:
			continue
		if col not in db.columns:
			db[col] = '0'	
	db.to_csv(output, encoding = 'utf-8')
	return 0