"""Exercise analysis with synthetic fixtures in a temporary directory, never runs/."""
import contextlib,hashlib,io,json,tempfile,unittest
from pathlib import Path
import analyze_followup as analysis
from grading import build_prompt,judge

class AnalysisTests(unittest.TestCase):
 def test_regrades_and_rejects_conflicting_or_tampered_answers(self):
  original=analysis.HERE
  cases=json.loads((original/'cases_followup.json').read_text())
  sha=hashlib.sha256(json.dumps(cases,sort_keys=True).encode()).hexdigest()
  with tempfile.TemporaryDirectory() as temp:
   analysis.HERE=Path(temp);(analysis.HERE/'runs').mkdir();(analysis.HERE/'cases_followup.json').write_text(json.dumps(cases))
   rows={}
   for c in cases:
    raw=json.dumps(dict(c['expected'],reason='Synthetic test fixture.'))
    r=judge(c,raw);r.update(raw_reply=raw,prompt_sha256=hashlib.sha256(build_prompt(c).encode()).hexdigest(),comment_bug_id=c.get('comment_bug_id'))
    rows['r1:'+c['id']]=r
   path=analysis.HERE/'runs/fixture.json';data=dict(model='fixture',dataset_sha256=sha,results=rows,calls=[])
   path.write_text(json.dumps(data))
   try:
    with contextlib.redirect_stdout(io.StringIO()):out=analysis.analyze()
    self.assertEqual(out['pooled']['exp1']['1']['all']['L2']['correct'],17)
    self.assertIsNone(out['pooled']['stability']['all']['identical_rate'])
    rows[next(iter(rows))]['status']='fail';path.write_text(json.dumps(data))
    with self.assertRaisesRegex(ValueError,'grading mismatch'):analysis.analyze()
   finally:analysis.HERE=original

if __name__=='__main__':unittest.main()
