"""MSR-06: blinded two-reviewer validation, without opening model labels.
This never reads the sealed model flags. No accuracy estimate before adjudication.
"""
from __future__ import annotations
import argparse,csv,hashlib,json
from collections import Counter
from pathlib import Path
FIELDS=('accumulation','sweep_return','structure_break','fvg','amd_sequence')
VALUES={'yes','no','uncertain'}
CERTAINTY={'high','medium','low'}

def read_cases(template):
    with template.open(encoding='utf-8-sig',newline='') as f:
        ids=[r['case_id'] for r in csv.DictReader(f)]
    if len(ids)!=180 or len(set(ids))!=180:
        raise ValueError('180 unique blind IDs required')
    return ids

def read_labels(path,ids):
    with path.open(encoding='utf-8-sig',newline='') as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=180:raise ValueError('180 complete reviews required')
    got={};names=set()
    for r in rows:
        k=r.get('case_id','').strip()
        if k not in ids or k in got:raise ValueError('duplicate or unknown case '+k)
        for field in FIELDS:
            ans=r.get(field,'').strip().lower()
            if ans not in VALUES:raise ValueError('missing/invalid '+field+' '+k)
            r[field]=ans
        if r.get('certainty','') not in CERTAINTY:
            raise ValueError('certainty missing '+k)
        reviewer=r.get('reviewer','').strip()
        if not reviewer:raise ValueError('reviewer ID missing')
        names.add(reviewer);got[k]=r
    if len(names)!=1:raise ValueError('one reviewer per CSV')
    return next(iter(names)),got,hashlib.sha256(path.read_bytes()).hexdigest()

def kappa(x,y,labels):
    n=len(x)
    if n==0:return None
    p0=sum(a==b for a,b in zip(x,y))/n
    cx=Counter(x);cy=Counter(y)
    pe=sum(cx[z]*cy[z] for z in labels)/n**2
    return None if pe==1 else round((p0-pe)/(1-pe),6)

def run(template,a,b,out):
    ids=read_cases(template)
    name1,r1,sha1=read_labels(a,ids)
    name2,r2,sha2=read_labels(b,ids)
    if name1==name2:raise ValueError('independent reviewer IDs required')
    metrics={}
    for field in FIELDS:
        left=[r1[k][field] for k in ids]
        right=[r2[k][field] for k in ids]
        both=[(x,y) for x,y in zip(left,right) if x!='uncertain' and y!='uncertain']
        metrics[field]={
            'exact_agreement':sum(x==y for x,y in zip(left,right)),
            'uncertain_either':sum(x=='uncertain' or y=='uncertain' for x,y in zip(left,right)),
            'both_definite':len(both),
            'kappa_3_choices':kappa(left,right,('yes','no','uncertain')),
            'kappa_definite':kappa([x for x,y in both],[y for x,y in both],('yes','no')) if both else None,
            'confusion':{x+'__'+y:v for (x,y),v in Counter(zip(left,right)).items()}
        }
    result={'status':'REVIEWER_AGREEMENT_ONLY_NOT_MODEL_ACCURACY',
            'reviewers':[name1,name2],'sha256':[sha1,sha2],
            'case_count':len(ids),'per_field':metrics,'sealed_flags_opened':False,
            'note':'Two different IDs do not prove two independent humans'}
    out.mkdir(parents=True,exist_ok=True)
    (out/'reviewer_agreement.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    with (out/'adjudication_template.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=['case_id',*FIELDS,'adjudicator','notes']);w.writeheader()
        for cid in ids:
            w.writerow({'case_id':cid,'adjudicator':'','notes':'',
                        **{field:r1[cid][field] if r1[cid][field]==r2[cid][field] else '' for field in FIELDS}})
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--template',required=True,type=Path)
    ap.add_argument('--first',required=True,type=Path)
    ap.add_argument('--second',required=True,type=Path)
    ap.add_argument('--out',required=True,type=Path)
    a=ap.parse_args()
    print(json.dumps(run(a.template,a.first,a.second,a.out),ensure_ascii=False,indent=2))
