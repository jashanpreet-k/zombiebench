"""Offline tests for paired metrics, independent repetitions, resume, and budget stops."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from grading import build_prompt,judge
from metrics import summarize
CASES=json.loads((HERE/'cases_followup.json').read_text())

class Chat:
    def __init__(self,name):self.name=name;self.usage=types.SimpleNamespace(input_tokens=100,output_tokens=20,input_tokens_cost_nanodollars=1000000,output_tokens_cost_nanodollars=1000000,total_backend_latency_ms=1)
    def __enter__(self):return self
    def __exit__(self,*args):pass

class Task:
    def __init__(self,fn):self.fn=fn
    def run(self,**kwargs):return self.fn(**kwargs)

class FakeModel:
    model='test/model'
    def __init__(self):self.calls=[];self.expected={build_prompt(c):c['expected'] for c in CASES}
    def prompt(self,prompt):
        self.calls.append(prompt)
        return json.dumps(dict(self.expected[prompt],reason='Offline gold fixture.'))

class FollowupTests(unittest.TestCase):
    def setUp(self):
        self.chat_names=[]
        def new(name):self.chat_names.append(name);return Chat(name)
        fake=types.ModuleType('kaggle_benchmarks');fake.task=lambda **kwargs:lambda fn:Task(fn);fake.chats=types.SimpleNamespace(new=new)
        sys.modules['kaggle_benchmarks']=fake
        spec=importlib.util.spec_from_file_location('task_under_test',HERE/'kaggle_followup.py')
        self.mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.mod)
        self.mod.time=types.SimpleNamespace(sleep=lambda _:None)
        self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.cwd=os.getcwd();os.chdir(self.tmp.name)
    def tearDown(self):os.chdir(self.cwd);self.tmp.cleanup();sys.modules.pop('kaggle_benchmarks',None)
    def test_fresh_repetitions_and_resume(self):
        model=FakeModel()
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(self.mod.BudgetStop):self.mod.execute_model(model,model.model,self.mod.Budget(10),max_calls=5)
            score=self.mod.execute_model(model,model.model,self.mod.Budget(10),n_runs=2)
        self.assertEqual(score,1.0);self.assertEqual(len(model.calls),188)
        self.assertEqual(len(set(self.chat_names)),188)
        data=self.mod.load(model.model)
        self.assertTrue(data['summary']['complete'])
        self.assertEqual(data['summary']['stability']['all']['changed'],0)
        self.assertEqual(data['summary']['stability']['all']['comparable_valid_answers'],85)
        self.assertEqual(len(data['calls']),188)
        with contextlib.redirect_stdout(io.StringIO()):self.mod.execute_model(model,model.model,self.mod.Budget(10),n_runs=2)
        self.assertEqual(len(model.calls),188)
    def test_single_run_then_second_exp1_only(self):
        model=FakeModel()
        with contextlib.redirect_stdout(io.StringIO()):
            self.mod.execute_model(model,model.model,self.mod.Budget(10),n_runs=1)
            self.assertEqual(len(model.calls),103)
            self.mod.execute_model(model,model.model,self.mod.Budget(10),n_runs=2)
        self.assertEqual(len(model.calls),188)
        self.assertEqual(self.mod.load(model.model)['summary']['stability']['all']['identical'],85)
    def test_error_retried_once_and_raw_attempt_saved(self):
        model=FakeModel();original=model.prompt;attempts=[0]
        def flaky(prompt):
            attempts[0]+=1
            if attempts[0]==1:raise RuntimeError('fixture')
            return original(prompt)
        model.prompt=flaky
        with contextlib.redirect_stdout(io.StringIO()):
            self.mod.execute_model(model,model.model,self.mod.Budget(10))
        data=self.mod.load(model.model)
        self.assertEqual(len(data['calls']),104)
        self.assertEqual(data['calls'][0]['status'],'error')
        self.assertEqual(data['calls'][0]['reason'],'RuntimeError')
        self.assertIn('raw_reply',data['calls'][1])
        self.assertTrue(data['summary']['complete'])
    def test_changed_and_unreadable_answers(self):
        rows={}
        for c in CASES:
            for rep in ((1,2) if c['experiment']=='exp1' else (1,)):
                r=judge(c,json.dumps(c['expected']));r['comment_bug_id']=c.get('comment_bug_id');rows[f'r{rep}:{c["id"]}']=r
        c=CASES[0];key='r2:'+c['id'];rows[key].update(verdict='new',bug_id=None,status='fail')
        c2=CASES[1];rows['r2:'+c2['id']].update(verdict=None,bug_id=None,problem='unreadable',status='fail')
        summary=summarize(CASES,rows,n_runs=2)
        self.assertEqual(summary['stability']['all']['changed'],1)
        self.assertEqual(summary['stability']['all']['comparable_valid_answers'],84)
        self.assertEqual(len(summary['stability']['all']['unreadable_pair_ids']),1)
    def test_missing_cost_and_reserve_fail_closed(self):
        b=self.mod.Budget(10);b.record({})
        with self.assertRaises(self.mod.BudgetStop):b.before()
        b=self.mod.Budget(10);b.spent=7.5
        with self.assertRaises(self.mod.BudgetStop):b.before()
        with self.assertRaises(ValueError):self.mod.Budget(0)
    def test_errors_excluded_not_stable(self):
        rows={'r1:'+CASES[0]['id']:{'status':'error'}}
        summary=summarize(CASES,rows,n_runs=2)
        self.assertFalse(summary['complete']);self.assertEqual(summary['overall']['answered'],0)
        self.assertIsNone(summary['stability']['all']['change_rate'])
    def test_no_label_fields_in_prompt(self):
        for c in CASES:
            prompt=build_prompt(c)
            altered=dict(c)
            for marker in ('source_case_id','comparison_bug_id','comment_bug_id','key_clue','expected','experiment','pair_id','why','type','tier'):
                altered[marker]='SECRET_METADATA_SENTINEL'
            self.assertEqual(prompt,build_prompt(altered))

if __name__=='__main__':unittest.main()
