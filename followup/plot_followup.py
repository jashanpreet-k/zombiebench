"""Render white/blue 200-dpi figures exclusively from analyzed saved runs."""
import json,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from metrics import LEVELS
HERE=Path(__file__).resolve().parent
OUT=HERE.parent/'charts'

def label(model):return model.split('/')[-1].split('@')[0].replace('-2026-03-17','')
def main():
 d=json.loads((HERE/'analysis.json').read_text());models=d['included_first_run_models'];n=len(models)
 plt.rcParams.update({'figure.facecolor':'white','axes.facecolor':'white','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
 cols=3;rows=math.ceil((n+1)/cols)
 fig,axs=plt.subplots(rows,cols,figsize=(13,rows*2.9),squeeze=False,layout='constrained')
 entries=[('Pooled first runs',d['pooled'])]+[(label(m),d['models'][m]) for m in models]
 for ax,(name,report) in zip(axs.flat,entries):
  ladder=report['exp1']['1']['all']
  for metric,ci_name,color,marker,legend in [('accuracy','accuracy_wilson95','#164471','o','Correct answer'),('followed_rate','followed_wilson95','#70add2','s','Wrong target ID')]:
   values=np.array([ladder[v][metric]*100 for v in LEVELS]);ci=np.array([ladder[v][ci_name] for v in LEVELS])*100
   ax.errorbar(range(5),values,yerr=np.maximum(0,np.array([values-ci[:,0],ci[:,1]-values])),color=color,marker=marker,capsize=3,lw=2,label=legend)
  ax.set_xticks(range(5),LEVELS);ax.set_ylim(-5,108);ax.set_title(name,fontsize=10);ax.set_ylabel('Answers (%)');ax.grid(axis='y',alpha=.15)
 for ax in list(axs.flat)[len(entries):]:ax.set_visible(False)
 fig.suptitle('Same report, different comment: accuracy and wrong-target choices',fontsize=16)
 axs.flat[0].legend(loc='best',fontsize=8,framealpha=.9)
 fig.supxlabel('L0 clean · P irrelevant placebo · L1 hedged · L2 confident · L3 claimed authority\nFirst runs only. Bars: descriptive Wilson 95% intervals; pooled dependence is not modeled.',fontsize=10)
 OUT.mkdir(exist_ok=True);fig.savefig(OUT/'zombiebench-followup-ladder.png',dpi=200);plt.close(fig)
 fig,ax=plt.subplots(figsize=(11,max(4,n*.58+1.8)),layout='constrained');y=np.arange(n)
 for offset,variant,color,title in [(-.19,'different','#2166ac','Different code (new bug)'),(.19,'same','#92c5de','Same code (regression)')]:
  groups=[d['models'][m]['exp2'][variant] for m in models];rates=np.array([g['accuracy']*100 for g in groups]);ci=np.array([g['accuracy_wilson95'] for g in groups])*100
  ax.barh(y+offset,rates,height=.34,color=color,label=title)
  ax.errorbar(rates,y+offset,xerr=[rates-ci[:,0],ci[:,1]-rates],fmt='none',ecolor='#164471',capsize=2,alpha=.65)
  for pos,rate,g in zip(y+offset,rates,groups):ax.text(102,pos,f'{g["correct"]}/{g["answered"]}',va='center',fontsize=9)
 ax.set_yticks(y,[label(m) for m in models]);ax.invert_yaxis();ax.set_xlim(0,111);ax.set_xticks([0,25,50,75,100]);ax.set_xlabel('Accuracy (%) · bars show Wilson 95% intervals');ax.set_title('Same mistake: different code versus the historically patched code',pad=42);ax.legend(loc='lower left',bbox_to_anchor=(0,1.01),ncol=2,frameon=False);ax.grid(axis='x',alpha=.15)
 fig.savefig(OUT/'zombiebench-followup-code.png',dpi=200);plt.close(fig)
 print('Wrote both follow-up charts from analysis.json.')
if __name__=='__main__':main()
