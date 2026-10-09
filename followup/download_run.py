"""Download an exact Kaggle run, preserving its version even after a task push."""
import argparse
import shutil
import zipfile
from pathlib import Path
from kaggle import api
from kagglesdk.benchmarks.types.benchmark_tasks_api_service import ApiDownloadBenchmarkTaskRunOutputRequest
HERE=Path(__file__).resolve().parent

def download(version,model_slug,run_id):
 out=HERE/'runs/zombiebench-followup'/str(version)/api._normalize_model_slug(model_slug)/str(run_id)
 if out.exists() and any(out.iterdir()):print('Exact run already saved:',version,model_slug,run_id,flush=True);return
 out.parent.mkdir(parents=True,exist_ok=True)
 staging=out.with_name(out.name+'.download');archive=out.with_suffix('.zip')
 request=ApiDownloadBenchmarkTaskRunOutputRequest();request.run_id=int(run_id);request.include_source=False
 with api.build_kaggle_client() as client:
  response=client.benchmarks.benchmark_tasks_api_client.download_benchmark_task_run_output(request)
  # Response may contain a signed download URL. Never print or persist it.
  api.download_file(response,str(archive),client.http_client(),quiet=True)
 if staging.exists():shutil.rmtree(staging)
 staging.mkdir()
 with zipfile.ZipFile(archive) as z:
  for name in z.namelist():assert (staging/name).resolve().is_relative_to(staging.resolve()),'Invalid archive path'
  z.extractall(staging)
 staging.rename(out);archive.unlink()
 print('Saved exact Kaggle run:',version,model_slug,run_id,flush=True)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('version',type=int);p.add_argument('model_slug');p.add_argument('run_id',type=int);a=p.parse_args();download(a.version,a.model_slug,a.run_id)
