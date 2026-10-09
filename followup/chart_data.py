"""A stable signature for the first-run numbers shown in the figures."""
import hashlib,json
def signature(d):
 models=d['included_first_run_models']
 data=dict(models=models,per_model={m:dict(exp1=d['models'][m]['exp1']['1']['all'],exp2=d['models'][m]['exp2']) for m in models},pooled=dict(exp1=d['pooled']['exp1']['1']['all'],exp2=d['pooled']['exp2']))
 return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()

def png_signature(path):
 data=path.read_bytes();i=8
 while i<len(data):
  size=int.from_bytes(data[i:i+4],'big');kind=data[i+4:i+8];payload=data[i+8:i+8+size]
  if kind==b'tEXt' and payload.startswith(b'ZombieBenchDataSignature\x00'):return payload.split(b'\x00',1)[1].decode()
  i+=size+12
 return None
