#!/usr/bin/env python3
"""Inspect embedded audio/subtitle streams with bounded HTTP range requests."""
import argparse,json,os,pathlib
from alist import Client
from rangeio import RangeIO
from container_headers import inspect
def probe(config,path):
 client=Client(config);item=client.call('/api/fs/get',{'path':path,'password':''})
 streams=inspect(item['raw_url'],item['size'])
 return {'path':path,'streams':streams,'burned_in_subtitles':'not determined by stream metadata'}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--config',default=os.environ.get('ALIST_CONFIG',str(pathlib.Path.home()/'.config/alist/access.json')));parser.add_argument('path');args=parser.parse_args()
 try:print(json.dumps(probe(args.config,args.path),ensure_ascii=False,indent=2))
 except Exception as e:raise SystemExit('Media probe failed ('+type(e).__name__+'); keep this file unverified.')
