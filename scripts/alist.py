#!/usr/bin/env python3
"""AList JSON API helper. Credentials stay in a local config, never in the skill."""
import argparse,json,os,pathlib,urllib.request,time
class Client:
 def __init__(self,config):
  c=json.loads(pathlib.Path(config).read_text());self.base=c['url'].rstrip('/');self.token=None
  self.token=self.call('/api/auth/login',{'username':c['username'],'password':c['password']})['token']
 def call(self,endpoint,payload):
  req=urllib.request.Request(self.base+endpoint,json.dumps(payload).encode(),{'Content-Type':'application/json',**({'Authorization':self.token} if self.token else {})})
  with urllib.request.urlopen(req,timeout=90) as r: data=json.load(r)
  if data.get('code')!=200: raise RuntimeError(str(data))
  return data.get('data')
 def listing(self,path,refresh=True):
  data=self.call('/api/fs/list',{'path':path,'page':1,'per_page':0,'refresh':refresh,'password':''})
  rows=data.get('content') or []
  if data.get('total',len(rows))!=len(rows): raise RuntimeError('Incomplete listing: '+path)
  return rows
 def crawl(self,path):
  result={};todo=[path]
  while todo:
   p=todo.pop();rows=self.listing(p);result[p]=rows
   todo.extend(p.rstrip('/')+'/'+r['name'] for r in rows if r['is_dir'])
  return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--config',default=os.environ.get('ALIST_CONFIG',str(pathlib.Path.home()/'.config/alist/access.json')));p.add_argument('command',choices=['list','crawl']);p.add_argument('path');a=p.parse_args();c=Client(a.config);print(json.dumps(c.listing(a.path) if a.command=='list' else c.crawl(a.path),ensure_ascii=False,indent=2))
