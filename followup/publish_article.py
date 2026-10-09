"""Update only the authorized existing DEV article. Credentials stay in memory."""
import json
from pathlib import Path
import urllib.request

HERE=Path(__file__).resolve().parent
API='https://dev.to/api/articles/4807743'
TITLE="Same Kind of Bug Isn't the Same Bug: Where AI Models Get Fooled"
URL='https://dev.to/jashanpreet_kaur_917e774f/same-kind-of-bug-isnt-the-same-bug-where-ai-models-get-fooled-21dd'

def identity(d):
 assert d['id']==4807743 and d['title']==TITLE and d['url']==URL
 assert 'kagglechallenge' in d['tag_list'] and d['published_at']

def main():
 key_path=Path.home()/'.devto_key'
 if not key_path.is_file():raise SystemExit('DEV key file is missing; no update attempted.')
 body=(HERE.parent/'post.md').read_text()
 assert body==(HERE/'post_proposed.md').read_text(),'Reviewable candidate differs from post.md'
 assert 'published: true' in body
 for section in ['### The follow-up: same report, different comment','### Nine more same-mistake cases']:
  assert body.count(section)==1
 with urllib.request.urlopen(API,timeout=30) as response:before=json.load(response)
 identity(before)
 baseline=(HERE/'artifacts/post_before_followup.md').read_text()
 assert before['body_markdown'].strip() in (baseline.strip(),body.strip()),'Public article changed outside the reviewed update; inspect before replacing it.'
 backup=HERE/'artifacts/dev_before_followup.json'
 if not backup.exists():backup.write_text(json.dumps(before,indent=2,ensure_ascii=False)+'\n')
 # This is the only credential read. Never log headers or exception payloads.
 key=key_path.read_text().strip()
 if not key:raise SystemExit('DEV key file is empty; no update attempted.')
 request=urllib.request.Request(API,data=json.dumps({'article':{'body_markdown':body,'published':True}}).encode(),method='PUT',headers={'api-key':key,'Content-Type':'application/json','User-Agent':'ZombieBench-authorized-update'})
 try:
  with urllib.request.urlopen(request,timeout=60) as response:
   assert response.status==200
   updated=json.load(response)
 except Exception as error:
  raise SystemExit('DEV update failed: '+type(error).__name__+'. Credential and response details withheld.') from None
 finally:
  del key,request
 identity(updated)
 print('Updated existing DEV article 4807743. Run verify_public.py separately without authentication.')

if __name__=='__main__':main()
