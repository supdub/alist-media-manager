"""Read MP4/MKV declared track metadata without decoding media packets."""
import struct
from rangeio import RangeIO
def exact(f,pos,n):
 f.seek(pos);b=f.read(n)
 if len(b)!=n:raise ValueError('Truncated metadata')
 return b
def boxes(f,start,end):
 pos=start;count=0
 while pos+8<=end:
  size,kind=struct.unpack('>I4s',exact(f,pos,8));header=8
  if size==1:size=struct.unpack('>Q',exact(f,pos+8,8))[0];header=16
  if size==0:size=end-pos
  if size<header or pos+size>end:raise ValueError('Invalid MP4 box')
  yield kind,pos+header,pos+size
  pos+=size;count+=1
  if count>20000:raise ValueError('Too many boxes')
def child(f,start,end,kind):return next(((a,b) for k,a,b in boxes(f,start,end) if k==kind),None)
def mp4(f):
 moov=child(f,0,f.size,b'moov')
 if not moov:raise ValueError('No movie metadata')
 streams=[];chapters=set();records=[]
 for k,a,b in boxes(f,*moov):
  if k!=b'trak':continue
  tk=child(f,a,b,b'tkhd');v=exact(f,tk[0],1)[0] if tk else 0
  track_id=int.from_bytes(exact(f,tk[0]+(20 if v else 12),4),'big') if tk else None
  tref=child(f,a,b,b'tref')
  if tref:
   ch=child(f,*tref,b'chap')
   if ch:
    raw=exact(f,ch[0],ch[1]-ch[0]);chapters.update(int.from_bytes(raw[i:i+4],'big') for i in range(0,len(raw),4))
  mdia=child(f,a,b,b'mdia')
  if not mdia:raise ValueError('Missing media metadata')
  h=child(f,*mdia,b'hdlr');m=child(f,*mdia,b'mdhd');mi=child(f,*mdia,b'minf')
  if not h or not m or not mi:raise ValueError('Incomplete track')
  handler=exact(f,h[0]+8,4);mv=exact(f,m[0],1)[0];code=int.from_bytes(exact(f,m[0]+(32 if mv else 20),2),'big');language=''.join(chr(((code>>shift)&31)+96) for shift in [10,5,0]) if code else 'und'
  stbl=child(f,*mi,b'stbl');stsd=child(f,*stbl,b'stsd') if stbl else None
  if not stsd:raise ValueError('No sample description')
  codec=exact(f,stsd[0]+12,4).decode('ascii','replace')
  typ='audio' if handler==b'soun' else 'subtitle' if handler in [b'text',b'sbtl',b'subt',b'clcp'] else 'video' if handler==b'vide' else 'data'
  records.append((track_id,{'type':typ,'codec':codec,'language':language,'title':''}))
 return [r for id,r in records if id not in chapters and r['type'] in ['audio','subtitle']]
def vint(f,pos,identifier=False):
 first=exact(f,pos,1)[0]
 if not first:raise ValueError('Invalid EBML integer')
 length=9-first.bit_length()
 if length>8:raise ValueError('Invalid EBML length')
 raw=exact(f,pos,length);value=int.from_bytes(raw,'big')
 return (value if identifier else value&((1<<(7*length))-1)),length

def elements(f,start,end):
 pos=start;count=0
 while pos<end:
  id,n=vint(f,pos,True);size,m=vint(f,pos+n);data=pos+n+m
  if data+size>end:raise ValueError('Invalid EBML element boundary')
  yield id,data,data+size
  pos=data+size;count+=1
  if count>20000:raise ValueError('Too many EBML elements')
def mkv(f):
 pos=0;seg=None
 for _ in range(8):
  id,n=vint(f,pos,True);size,m=vint(f,pos+n);data=pos+n+m
  if id==0x18538067:seg=(data,f.size if size==(1<<(7*m))-1 else data+size);break
  pos=data+size
 if not seg:raise ValueError('No Matroska segment')
 track=None
 for id,a,b in elements(f,*seg):
  if id==0x1654ae6b:track=(a,b);break
  if id==0x114d9b74:
   for si,sa,sb in elements(f,a,b):
    if si!=0x4dbb:continue
    values={ci:int.from_bytes(exact(f,ca,cb-ca),'big') for ci,ca,cb in elements(f,sa,sb)}
    if values.get(0x53ab)==0x1654ae6b:
     pos=seg[0]+values[0x53ac];ti,n=vint(f,pos,True);size,m=vint(f,pos+n)
     if ti!=0x1654ae6b:raise ValueError('Track seek mismatch')
     track=(pos+n+m,pos+n+m+size);break
   if track:break
  if id==0x1f43b675:break
 if not track:raise ValueError('No track declaration')
 streams=[]
 for id,a,b in elements(f,*track):
  if id!=0xae:continue
  fields={ci:exact(f,ca,cb-ca) for ci,ca,cb in elements(f,a,b) if ci in [0x83,0x86,0x22b59c,0x22b59d,0x536e]}
  typ=int.from_bytes(fields.get(0x83,b''),'big');codec=fields.get(0x86,b'').decode('utf-8','replace')
  if not typ or not codec:raise ValueError('Incomplete track declaration')
  if typ in [2,17]:streams.append({'type':'audio' if typ==2 else 'subtitle','codec':codec,'language':fields.get(0x22b59d,fields.get(0x22b59c,b'eng')).decode('utf-8','replace'),'title':fields.get(0x536e,b'').decode('utf-8','replace')})
 return streams
def inspect(url,size):
 f=RangeIO(url,size,limit=128,chunk=65536);magic=exact(f,0,8)
 if magic[:4]==bytes.fromhex('1a45dfa3'):rows=mkv(f)
 elif magic[4:8] in [b'ftyp',b'moov',b'free',b'wide',b'mdat']:rows=mp4(f)
 else:raise ValueError('Unsupported container signature')
 return rows
