"""Public GET checks only. This script never reads or uses a credential."""
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
import urllib.request,urllib.error
from publish_article import API,TITLE,URL,identity
HERE=Path(__file__).resolve().parent

def get(url):
 request=urllib.request.Request(url,headers={'User-Agent':'ZombieBench-public-verification'})
 with urllib.request.urlopen(request,timeout=40) as response:return response.status,response.geturl(),response.read()

def main():
 status,_,raw=get(API);d=json.loads(raw);identity(d)
 body=(HERE.parent/'post.md').read_text();assert d['body_markdown'].strip()==body.strip(),'Public Markdown differs from committed article'
 sections=['### The follow-up: same report, different comment','### Nine more same-mistake cases']
 for s in sections:assert d['body_markdown'].count(s)==1
 images=re.findall(r'!\[[^\]]*\]\((https://[^)]+)\)',body)
 assert all(image in d['body_markdown'] for image in images)
 assert 'cover.png' in d['cover_image']
 urls=sorted(set(re.findall(r'https://[^\s)<>"*]+',body)))
 checks=[]
 for url in urls:
  try:
   code,final,data=get(url);item=dict(url=url,status=code,final_url=final)
   if url.endswith('.png'):assert data.startswith(b'\x89PNG\r\n\x1a\n');item['bytes']=len(data)
  except urllib.error.HTTPError as error:item=dict(url=url,status=error.code)
  except Exception as error:item=dict(url=url,error=type(error).__name__)
  checks.append(item)
 page_status,page_url,html=get(URL)
 assert page_status==200 and page_url==URL
 report=dict(checked_at=datetime.now(timezone.utc).isoformat(),article_id=d['id'],api_status=status,page_status=page_status,title=d['title'],url=d['url'],tags=d['tag_list'],cover_set=True,sections_present=sections,images_present=images,body_sha256=hashlib.sha256(body.encode()).hexdigest(),links=checks)
 (HERE/'artifacts/public_check.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
 failures=[c for c in checks if c.get('status')!=200]
 if failures:raise SystemExit('Some public links need review; see public_check.json.')

if __name__=='__main__':main()
