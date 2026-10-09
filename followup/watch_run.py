"""Monitor a saved run version without starting inference or changing the task."""
import argparse,time
from kaggle import api
from kagglesdk.benchmarks.types.benchmark_tasks_api_service import ApiListBenchmarkTaskRunsRequest
from download_run import download

def main():
 p=argparse.ArgumentParser();p.add_argument('version',type=int);p.add_argument('model_slug');p.add_argument('run_id',type=int);a=p.parse_args()
 slug=api._make_task_slug('jashanpreetkaur24/zombiebench-followup');slug.version_number=a.version
 request=ApiListBenchmarkTaskRunsRequest();request.task_slug=slug;request.model_version_slugs=[a.model_slug]
 last=None
 while True:
  with api.build_kaggle_client() as client:runs=client.benchmarks.benchmark_tasks_api_client.list_benchmark_task_runs(request).runs
  run=next((r for r in runs if r.id==a.run_id),None)
  if run is None:raise SystemExit('Expected exact run was not found; no new inference scheduled.')
  if run.state!=last:print('Exact run',a.run_id,'state:',run.state.name,flush=True);last=run.state
  if run.state in api._TERMINAL_RUN_STATES:download(a.version,a.model_slug,a.run_id);return
  time.sleep(30)

if __name__=='__main__':main()
