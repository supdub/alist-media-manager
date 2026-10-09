#!/usr/bin/env python3
"""Inspect embedded audio/subtitle streams with bounded HTTP range requests."""
import argparse,json,os,pathlib
from alist import Client
from rangeio import RangeIO
try:
 import av
except ImportError:
 raise SystemExit('PyAV is required for media probes: install the av Python package.')
def probe(config,path):
 client=Client(config);item=client.call('/api/fs/get',{'path':path,'password':''})
 reader=RangeIO(item['raw_url'],item['size'])
 with av.open(reader,options={'probesize':'32768','analyzeduration':'1','fpsprobesize':'0'}) as container:
  streams=[{'type':s.type,'codec':s.codec_context.name,'language':s.metadata.get('language','und'),'title':s.metadata.get('title','')} for s in container.streams if s.type in ['audio','subtitle']]
 if reader.exhausted:raise OSError('Probe byte budget exceeded')
 return {'path':path,'streams':streams,'bytes_fetched_upper_bound':len(reader.cache)*reader.chunk,'burned_in_subtitles':'not determined by stream metadata'}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--config',default=os.environ.get('ALIST_CONFIG',str(pathlib.Path.home()/'.config/alist/access.json')));parser.add_argument('path');args=parser.parse_args()
 try:print(json.dumps(probe(args.config,args.path),ensure_ascii=False,indent=2))
 except Exception as e:raise SystemExit('Media probe failed ('+type(e).__name__+'); keep this file unverified.')
