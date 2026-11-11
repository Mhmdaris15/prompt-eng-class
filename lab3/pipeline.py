"""Reproducible Lab 3 stages. Run `python -m lab3.pipeline --help`."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import requests
from dotenv import dotenv_values
from .config import *

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN = ROOT / 'results/lab3_entanglement'
BASE_URL = 'https://proxy-prompts.aiclab.tech/v1'
EMBEDDING_MODEL = 'cloud-bge/BAAI/bge-m3'

def save(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def write_csv(path, rows, fields=None):
    rows = list(rows)
    with Path(path).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        writer.writeheader(); writer.writerows(rows)

def parse_embedding(text):
    vector = np.asarray(json.loads(text), dtype=np.float32)
    if vector.shape != (EXPECTED_DIM,) or not np.isfinite(vector).all() or np.linalg.norm(vector) == 0:
        raise ValueError('Expected finite nonzero 1024-dimensional BGE-M3 vector')
    return vector

def unit_matrix(matrix):
    matrix = np.asarray(matrix, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=-1, keepdims=True)
    if not np.isfinite(matrix).all() or (norms <= 0).any():
        raise ValueError('Invalid or zero vector')
    return matrix / norms

def prepare(run_dir=DEFAULT_RUN, dataset=ROOT/'lab3/dataset.csv'):
    run_dir = Path(run_dir)
    if (run_dir/'corpus.json').exists():
        manifest=read(run_dir/'manifest.json')
        if manifest['keyword']!=KEYWORD or manifest.get('max_papers',MAX_PAPERS)!=MAX_PAPERS or manifest.get('max_scan_rows',MAX_SCAN_ROWS)!=MAX_SCAN_ROWS:
            raise ValueError('Selection settings changed: use a new run directory')
        return manifest
    run_dir.mkdir(parents=True, exist_ok=True)
    papers=[]; vectors=[]; scanned=0; matches=0; categories={}; fields=[]
    with Path(dataset).open(encoding='utf-8-sig', newline='') as f:
        reader=csv.DictReader(f); fields=reader.fieldnames
        for row in reader:
            if scanned >= MAX_SCAN_ROWS: break
            scanned+=1
            cat=row['main_category']; categories[cat]=categories.get(cat,0)+1
            if KEYWORD not in ' '.join(row[x] for x in ['title','abstract','categories']).lower(): continue
            matches+=1
            if len(papers)>=MAX_PAPERS: continue
            vector=parse_embedding(row.pop('embedding_bge_m3'))
            row['article_id']=str(row['article_id'])
            papers.append(row); vectors.append(vector)
    if not papers: raise ValueError('No matching publications')
    matrix=np.vstack(vectors)
    np.save(run_dir/'vectors.npy',matrix,allow_pickle=False)
    save(run_dir/'corpus.json',papers)
    with Path(dataset).open('rb') as source_file:
        digest=hashlib.sha256()
        for block in iter(lambda:source_file.read(1024*1024),b''): digest.update(block)
        dataset_hash=digest.hexdigest()
    manifest={'status':'prepared_not_executed','keyword':KEYWORD,'max_papers':MAX_PAPERS,'max_scan_rows':MAX_SCAN_ROWS,'scanned':scanned,'matches':matches,'selected':len(papers),
              'matrix_shape':list(matrix.shape),'fields':fields,'categories':categories,
              'dataset_sha256':dataset_hash,
              'embedding_model':EMBEDDING_MODEL,'embedding_endpoint':BASE_URL+'/embeddings',
              'generation_endpoint':BASE_URL+'/chat/completions','questions':QUESTIONS,
              'primary_model':None,'review_model':None,'temperature':0.2,'max_tokens':1400,
              'sentence_prediction':'Sentences 1 and 2 should be closest; both concern AI-based information processing. Recorded before API requests.'}
    save(run_dir/'manifest.json',manifest)
    return manifest

class CourseAPI:
    def __init__(self, env_file=ROOT/'.env', primary=None, reviewer=None):
        values=dotenv_values(env_file)
        self.key=os.getenv('COURSE_API_KEY') or values.get('COURSE_API_KEY') or os.getenv('AICLAB_API_KEY') or values.get('AICLAB_API_KEY')
        if not self.key or self.key in ['your_course_api_key_here','your_api_key_here']:
            raise RuntimeError('Add COURSE_API_KEY to the local .env; never paste it in code or chat.')
        self.primary=os.getenv('COURSE_MODEL_A') or values.get('COURSE_MODEL_A') or primary or 'Qwen/Qwen3-30B-A3B'
        self.reviewer=os.getenv('COURSE_MODEL_B') or values.get('COURSE_MODEL_B') or reviewer or 'GigaChat/GigaChat-3-Pro'
        if self.primary==self.reviewer: raise ValueError('Reviewer must be a different LLM')

    def models(self):
        r=requests.get(BASE_URL.removesuffix('/v1')+'/usage',headers={'Authorization':'Bearer '+self.key},timeout=45)
        r.raise_for_status()
        names={name for provider in r.json().get('provider_configs',[]) for name in provider.get('allowed_models',[])}
        if self.primary not in names or self.reviewer not in names:
            raise ValueError('Configured primary/reviewer unavailable. Allowed models: '+', '.join(sorted(names)))
        return sorted(names)

    def embedding(self,text):
        for attempt in range(3):
            r=requests.post(BASE_URL+'/embeddings',headers={'x-bf-vk':self.key,'Content-Type':'application/json'},
                            json={'model':EMBEDDING_MODEL,'input':text},timeout=90)
            if r.status_code in [429,500,502,503,504] and attempt<2:
                time.sleep(attempt+1); continue
            r.raise_for_status()
            return parse_embedding(json.dumps(r.json()['data'][0]['embedding']))

    def chat(self,model,prompt):
        start=time.monotonic()
        try:
            requested_model=model if model.startswith('cloud/') else 'cloud/'+model
            r=requests.post(BASE_URL+'/chat/completions',headers={'Authorization':'Bearer '+self.key},
                            json={'model':requested_model,'messages':[{'role':'user','content':prompt}], 'temperature':0.2,'max_tokens':1400},timeout=180)
            if not r.ok: raise RuntimeError('HTTP '+str(r.status_code)+': '+r.text[:800].replace(self.key,'[REDACTED]'))
            payload=r.json(); choice=payload['choices'][0]; answer=choice['message'].get('content') or ''
            reason=choice.get('finish_reason','')
            return {'status':'truncated' if reason=='length' else ('ok' if answer.strip() else 'empty'),
                    'answer':answer,'requested_model':requested_model,'finish_reason':reason,'usage':payload.get('usage',{}),'latency_seconds':round(time.monotonic()-start,3)}
        except (requests.RequestException,ValueError,KeyError,IndexError,RuntimeError) as exc:
            return {'status':'error','answer':'','error':type(exc).__name__+': '+str(exc).replace(self.key,'[REDACTED]'),'latency_seconds':round(time.monotonic()-start,3)}

def search_articles(question, papers, matrix, api, run_dir, k=3):
    cache=Path(run_dir)/'query_vectors.json'; stored=read(cache) if cache.exists() else {}
    if question not in stored:
        stored[question]=api.embedding(question).tolist(); save(cache,stored)
    query=unit_matrix(parse_embedding(json.dumps(stored[question])))
    scores=unit_matrix(matrix) @ query
    indexes=np.argsort(-scores,kind='stable')[:min(k,len(papers))]
    return [dict(papers[i],similarity=float(scores[i])) for i in indexes]

def make_context(papers):
    return '\n\n'.join(f"[S{i}] Title: {p['title']}\nAuthors: {p['authors']}\nArXiv ID: {p['article_id']}\nAbstract: {p['abstract']}" for i,p in enumerate(papers,1))

def make_prompt(question,papers,improved=True,correction=False):
    instruction=MY_RAG_INSTRUCTION if improved else 'Answer the question using these article abstracts.'
    if correction: instruction+=CORRECTION_ADDITION
    return instruction+'\n\nQuestion: '+question+'\n\nSources:\n'+make_context(papers)

def ask_llm(prompt, api, model=None):
    """Notebook-compatible generation entry point with explicit status metadata."""
    return api.chat(model or api.primary,prompt)

def execute(run_dir=DEFAULT_RUN,env_file=ROOT/'.env'):
    run_dir=Path(run_dir); manifest=prepare(run_dir); api=CourseAPI(env_file,manifest.get('primary_model'),manifest.get('review_model'))
    models=api.models(); manifest.update(primary_model=api.primary,review_model=api.reviewer,available_models=models,last_executed_at=datetime.now(timezone.utc).isoformat())
    save(run_dir/'manifest.json',manifest)
    papers=read(run_dir/'corpus.json'); matrix=np.load(run_dir/'vectors.npy',allow_pickle=False)
    similarities_file=run_dir/'sentence_experiment.json'
    if not similarities_file.exists():
        sent=unit_matrix(np.vstack([api.embedding(s) for s in SENTENCES]))
        save(similarities_file,{'sentences':SENTENCES,'dimension':sent.shape[1],'cosine_matrix':(sent @ sent.T).tolist(),'prediction':manifest['sentence_prediction']})
    found={str(i+1):search_articles(q,papers,matrix,api,run_dir,5) for i,q in enumerate(QUESTIONS)}
    save(run_dir/'retrieved.json',found)
    calls=read(run_dir/'calls.json') if (run_dir/'calls.json').exists() else {}
    def call(name,question,docs=None,improved=True,model=None,prompt=None,correction=False):
        request=prompt if prompt is not None else (make_prompt(question,docs,improved,correction) if docs is not None else question)
        model=model or api.primary
        fingerprint=hashlib.sha256((model+'\n'+request).encode()).hexdigest()
        if name in calls:
            if calls[name]['fingerprint']!=fingerprint: raise ValueError('Cached request differs; use a new run directory: '+name)
            return calls[name]
        result=ask_llm(request,api,model)
        result.update(model=model,prompt=request,fingerprint=fingerprint,source_ids=[p['article_id'] for p in docs or []])
        calls[name]=result; save(run_dir/'calls.json',calls); print(name,result['status'],flush=True)
        return result
    for i,q in enumerate(QUESTIONS,1):
        call(f'q{i}_plain',q)
        call(f'q{i}_rag',q,found[str(i)][:3])
        if i<=2: call(f'q{i}_simple',q,found[str(i)][:3],improved=False)
    for k in (1,5): call(f'q1_k{k}',QUESTIONS[0],found['1'][:k])
    # Hand-picked positions must follow reading all five abstracts; no silent automatic substitute.
    choices=run_dir/'manual_selection.json'
    if choices.exists():
        selection=read(choices); positions=selection['positions']
        if len(positions)!=3 or len(set(positions))!=3 or not all(1<=x<=5 for x in positions) or not selection.get('reason'):
            raise ValueError('Manual selection requires three distinct positions 1–5 and a reason')
        call('q1_manual',QUESTIONS[0],[found['1'][x-1] for x in positions])
    answer=calls['q1_rag']
    if answer['status']=='ok':
        review_prompt='Review only against the supplied abstracts. Check every citation and claim. Quote supporting abstract fragments for each criticism. Separate unsupported claims from contradictions and missing information. Give one useful criticism and one uncertain point requiring verification.\nQuestion: '+QUESTIONS[0]+'\nSources:\n'+make_context(found['1'][:3])+'\nAnswer:\n'+answer['answer']
        call('review',QUESTIONS[0],found['1'][:3],model=api.reviewer,prompt=review_prompt)
    call('q1_corrected',QUESTIONS[0],found['1'][:3],correction=True)
    export_tables(run_dir,calls,found)
    manifest.update(status='experiments_recorded_reviews_required',calls=len(calls),by_status={s:sum(v['status']==s for v in calls.values()) for s in ['ok','error','empty','truncated']})
    save(run_dir/'manifest.json',manifest)
    return calls

def export_tables(run_dir,calls,found):
    path=Path(run_dir)
    review_file=path/'retrieval_review.csv'
    if not review_file.exists():
        write_csv(review_file,[{'question_id':i,'question':QUESTIONS[int(i)-1],'article_id':p['article_id'],'title':p['title'],'similarity':p['similarity'],'abstract':p['abstract'],'relevance_0_1_2':'','reason':''} for i,ps in found.items() for p in ps[:3]])
    previous={}
    if (path/'rag_comparison.csv').exists():
        with (path/'rag_comparison.csv').open(encoding='utf-8-sig',newline='') as f:
            previous={row['question']:row for row in csv.DictReader(f)}
    write_csv(path/'rag_comparison.csv',[{'question':q,'without_rag':calls[f'q{i}_plain']['answer'],'with_rag':calls[f'q{i}_rag']['answer'],'plain_status':calls[f'q{i}_plain']['status'],'rag_status':calls[f'q{i}_rag']['status'],'arxiv_ids':';'.join(p['article_id'] for p in found[str(i)][:3]),'what_improved':previous.get(q,{}).get('what_improved',''),'remaining_problem':previous.get(q,{}).get('remaining_problem','')} for i,q in enumerate(QUESTIONS,1)])
    variants=[(k,'automatic','q1_rag' if k==3 else f'q1_k{k}') for k in [1,3,5]]
    if 'q1_manual' in calls: variants.append((3,'manual','q1_manual'))
    write_csv(path/'k_experiment.csv',[{'k':k,'selection':mode,'source_ids':';'.join(calls[name]['source_ids']),'answer':calls[name]['answer'],'status':calls[name]['status']} for k,mode,name in variants])
    write_csv(path/'prompt_comparison.csv',[{'question':QUESTIONS[i-1],'simple':calls[f'q{i}_simple']['answer'],'improved':calls[f'q{i}_rag']['answer']} for i in [1,2]])
    claims=path/'claims_review_template.csv'
    if not claims.exists(): write_csv(claims,[{'claim':'','source_id':'','evidence_from_abstract':'','verdict':'','reason':''} for _ in range(3)])

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['prepare','run','report'])
    parser.add_argument('--run-dir',type=Path,default=DEFAULT_RUN)
    parser.add_argument('--env-file',type=Path,default=ROOT/'.env')
    args=parser.parse_args()
    if args.stage=='prepare': print(json.dumps(prepare(args.run_dir),ensure_ascii=True,indent=2))
    elif args.stage=='run': execute(args.run_dir,args.env_file)
    else:
        from .report import build_reports
        build_reports(args.run_dir)

if __name__=='__main__': main()
