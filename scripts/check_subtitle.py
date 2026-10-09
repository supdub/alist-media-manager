#!/usr/bin/env python3
"""Check subtitle structure and cue times; this does not verify synchronization."""
import argparse,json,os,pathlib,re,urllib.request
from alist import Client
from container_headers import inspect

def seconds(value):
 match=re.fullmatch(r'(\d+):(\d{2}):(\d{2})[.,](\d{1,3})',value.strip())
 if not match or int(match[2])>=60 or int(match[3])>=60:raise ValueError('Invalid cue timestamp')
 return int(match[1])*3600+int(match[2])*60+int(match[3])+int(match[4])/10**len(match[4])

def validate_text(data,extension):
 if data.startswith((b'\xff\xfe',b'\xfe\xff')):text=data.decode('utf-16');encoding='utf-16'
 else:
  try:text=data.decode('utf-8-sig');encoding='utf-8'
  except UnicodeDecodeError:text=data.decode('gb18030');encoding='gb18030'
 cues=[]
 if extension in ['.ass','.ssa']:
  if '[script info]'not in text.lower()or '[events]'not in text.lower():raise ValueError('ASS sections absent')
  events=re.split(r'\[events\]',text,flags=re.I)[1];fmt=re.search(r'^Format\s*:\s*(.+)$',events,re.M|re.I)
  if not fmt:raise ValueError('Event field declaration absent')
  names=[s.strip().lower()for s in fmt[1].split(',')];start=names.index('start');end=names.index('end')
  for line in re.findall(r'^Dialogue\s*:\s*(.*)$',events,re.M|re.I):
   values=line.split(',',len(names)-1)
   if len(values)!=len(names):raise ValueError('Incomplete dialogue fields')
   cues.append((seconds(values[start]),seconds(values[end])))
 elif extension=='.srt':
  pattern=r'(\d+:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d+:\d{2}:\d{2}[.,]\d{3})'
  cues=[(seconds(a),seconds(b))for a,b in re.findall(pattern,text)]
 else:raise ValueError('Unsupported text subtitle extension')
 if not cues:raise ValueError('No caption cues')
 if any(end<start for start,end in cues):raise ValueError('Cue ends before it starts')
 return {'encoding':encoding,'caption_events':len(cues),'first_caption_start_seconds':min(a for a,b in cues),'last_caption_end_seconds':max(b for a,b in cues)}

def check(client,path):
 data=client.call('/api/fs/get',{'path':path,'password':''});extension=pathlib.Path(path).suffix.lower();size=data['size']
 if extension=='.mks':
  tracks=inspect(data['raw_url'],size)
  if not any(t['type']=='subtitle'for t in tracks):raise ValueError('No subtitle track in MKS')
  return {'path':path,'status':'valid','streams':tracks}
 if size<=0 or size>8388608:raise ValueError('Subtitle is empty or exceeds bounded inspection size')
 headers={**(data.get('header')or {}),'Range':f'bytes=0-{size-1}'}
 with urllib.request.urlopen(urllib.request.Request(data['raw_url'],headers=headers),timeout=30)as response:body=response.read(size+1)
 if len(body)!=size:raise OSError('Incomplete subtitle read')
 return {'path':path,'status':'valid',**validate_text(body,extension)}

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--config',default=os.environ.get('ALIST_CONFIG',str(pathlib.Path.home()/'.config/alist/access.json')));parser.add_argument('path');args=parser.parse_args();print(json.dumps(check(Client(args.config),args.path),ensure_ascii=False,indent=2))
