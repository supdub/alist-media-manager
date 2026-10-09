import io,urllib.request
class RangeIO(io.RawIOBase):
 def __init__(self,url,size,limit=8,chunk=1048576,timeout=15):self.url=url;self.size=size;self.pos=0;self.cache={};self.limit=limit;self.chunk=chunk;self.exhausted=False;self.failure=None;self.timeout=timeout
 def readable(self):return True
 def seekable(self):return True
 def seek(self,offset,whence=0):
  self.pos=offset if whence==0 else self.pos+offset if whence==1 else self.size+offset
  return self.pos
 def tell(self):return self.pos
 def read(self,n=-1):
  if self.failure:raise OSError(self.failure)
  if n<0:n=self.chunk
  n=min(n,self.size-self.pos)
  if n<=0:return b''
  result=[]
  while n:
   block=self.pos//self.chunk
   if block not in self.cache:
    if len(self.cache)>=self.limit:
     self.exhausted=True;self.failure='Probe byte budget exceeded'
     raise OSError(self.failure)
    start=block*self.chunk;end=min(start+self.chunk-1,self.size-1)
    req=urllib.request.Request(self.url,headers={'Range':f'bytes={start}-{end}','User-Agent':'Mozilla/5.0'})
    try:
     with urllib.request.urlopen(req,timeout=self.timeout) as r:
      if r.status!=206 and start!=0:raise OSError('Range unsupported')
      self.cache[block]=r.read(end-start+1)
    except Exception as e:
     self.failure=type(e).__name__;raise
   b=self.cache[block];offset=self.pos%self.chunk;piece=b[offset:offset+n]
   if not piece:break
   result.append(piece);self.pos+=len(piece);n-=len(piece)
  return b''.join(result)
