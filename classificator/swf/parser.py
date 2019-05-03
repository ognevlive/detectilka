import argparse
import hashlib
import pandas as pd
from swf.movie import SWF
from os import listdir, unlink

MAX_TAG = 90

def tagStat(path):

  info = [0] * MAX_TAG

  data = open(path, 'rb')
  swf = SWF(data)

  for tag in swf.tags:
    info[tag.type] = 1

  return info


class metadata():
  fileAttributes = 0
 
  tagCount = 0
  uniqTagCount = 0
  
  fileLength = 0
  frameRate = 0
  frameCount = 0
  frameSizeMin = 0
  frameSizeMax = 0


  def parseHeader(self, header):
    self.frameCount = header.frame_count
    self.frameSizeMin = header.frame_size.xmin * header.frame_size.ymin
    self.frameSizeMax = header.frame_size.xmax * header.frame_size.ymax
    self.fileLength = header.file_length
    if header.frame_rate < 0: self.frameRate = 0
    else: self.frameRate = header.frame_rate


def createCSV(name):
  attr_name = ['useDirectBlit', 'useGPU', 'useNetwork', 'actionscript3', 'hasMetadata']
  col = pd.DataFrame(['file_name', 'hash', 'tagCount', 'uniqTagCount' , 'fileLength', 'frameRate', 'frameCount', 'frameSizeMin', 'frameSizeMax'] + attr_name + [x for x in range(MAX_TAG)] + ['isBad']).transpose()
  col.to_csv(name, header=False)


def parse(path):
  data = open(path, 'rb')
  try:
    swf = SWF(data)
  except:
    return 1

  m = metadata()
  s = set()
  for tag in swf.tags:
    s.add(tag.type)

  m.uniqTagCount = len(s)
  m.tagCount = len(swf.tags)

  header = swf.header  
  m.parseHeader(header)

  attr_list = []
  for tag in swf.tags:
    if tag.name == 'FileAttributes':
      attr_list.append(int(tag.useDirectBlit))
      attr_list.append(int(tag.useGPU))
      attr_list.append(int(tag.useNetwork))
      attr_list.append(int(tag.actionscript3))
      attr_list.append(int(tag.hasMetadata))
      break

  stat = tagStat(folder+file)
  data = open(folder + file, 'rb').read()
  _hash = hashlib.md5(data).hexdigest()

  data = [file, _hash, m.tagCount, m.uniqTagCount, m.fileLength, m.frameRate, m.frameCount, m.frameSizeMin, m.frameSizeMax] + attr_list + stat + ['0']
  return data


def file(path, output):
  createCSV(output)
 
  data = parse(path)
  print (data)
 
  df = pd.DataFrame(data)
  df = df.transpose()
  df.to_csv(output, mode='a', header=False)


def folder(path, output):
  createCSV('%s.csv' % output)

  for file in listdir(path):
    data = parse(path + file)
    df = pd.DataFrame(data)
    df = df.transpose()
    df.to_csv(output, mode='a', header=False)
      

