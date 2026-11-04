"""MSR-02: blinded replay review from OFFLINE Binance USD-M fixture CSV.
No trades. Model detections are NOT expert labels. Charts end at asof.
"""
from __future__ import annotations
import argparse, csv, hashlib, html, json, random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from replay import STEP_MS, iso, read_csv, replay

NAMES={
    "ACC":"ACCUMULATION_LOCKED","SWEEP":"SWEEP_RETURN",
    "BOS":"STRUCTURE_BREAK_CONFIRMED","FVG":"FVG_AFTER_SWEEP",
    "FAIL":"EXPIRED_NO_STRUCTURE"
}
QUOTAS={"ACC":30,"SWEEP":30,"BOS":30,"FVG":30,"FAIL":30,"ALT_ONLY":15,"RANDOM":15}
FLAGS={"accumulation":"ACCUMULATION_LOCKED","sweep_return":"SWEEP_RETURN",
       "structure_break":"STRUCTURE_BREAK_CONFIRMED","fvg":"FVG_AFTER_SWEEP"}
SEED=20261104

def epoch(s):
    return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)

def alternative_sweep(bars):
    """Independent mechanical sweep proxy: previous 32 CLOSED 15m bars only."""
    out=[]
    for i in range(32,len(bars)):
        b=bars[i]; old=bars[i-32:i]
        lo=min(x.l for x in old);hi=max(x.h for x in old)
        up=b.h>hi and b.c<hi and b.h>b.o
        down=b.l<lo and b.c>lo and b.l<b.o
        if up != down:
            out.append({"symbol":b.symbol,"known_at":iso(b.known_at),
                        "side":-1 if up else 1,"event":"ALT_ONLY"})
    return out

def asof(bars,t,tf,keep):
    """Read only fully CLOSED, UTC aligned candles up through timestamp t."""
    n=tf//15
    result=[];part=[];key=None
    for x in bars:
        if x.known_at>t:break
        k=x.t//(n*STEP_MS)
        if key is None:key=k
        if k != key:
            key=k;part=[]
        part.append(x)
        if len(part)==n:
            assert part[0].t==k*n*STEP_MS
            result.append((part[0].o,max(q.h for q in part),min(q.l for q in part),
                           part[-1].c,part[-1].known_at))
            part=[];key=None
    result=result[-keep:]
    assert all(x[4]<=t for x in result)
    return result

def svg(rows,title):
    if not rows:return "<p>Недостаточно завершённых свечей.</p>"
    W,H=950,250;left,top=64,25
    mn=min(x[2] for x in rows);mx=max(x[1] for x in rows)
    sp=max(mx-mn,1e-10);mn-=sp*.06;mx+=sp*.06
    X=lambda i:left+(i+.5)*(W-left-8)/len(rows)
    Y=lambda p:top+(mx-p)/(mx-mn)*(H-top-28)
    objects=[f"<rect width='{W}' height='{H}' fill='#fafafa'/>",
             f"<text x='{left}' y='16' font-size='14'>{title}</text>"]
    for i,(o,h,l,c,t) in enumerate(rows):
        col="#159a68" if c>=o else "#cf4444"
        x=X(i);u=Y(max(o,c));v=Y(min(o,c))
        bw=max(1,(W-left-8)/len(rows)*.56)
        objects.extend([f"<line x1='{x:.2f}' y1='{Y(h):.2f}' x2='{x:.2f}' y2='{Y(l):.2f}' stroke='{col}'/>",
                        f"<rect x='{x-bw/2:.2f}' y='{u:.2f}' width='{bw:.2f}' height='{max(1,v-u):.2f}' fill='{col}'/>"])
    for i in range(5):
        price=mn+(mx-mn)*i/4
        y=Y(price)
        objects.extend([f"<line x1='{left}' x2='{W-8}' y1='{y:.2f}' y2='{y:.2f}' stroke='#ddd' stroke-dasharray='2,4'/>",
                        f"<text x='{left-5}' y='{y+3:.2f}' text-anchor='end' font-size='10'>{price:.5g}</text>"])
    for i in (0,len(rows)//2,len(rows)-1):
        t=datetime.fromtimestamp(rows[i][4]/1000,tz=timezone.utc).strftime("%d.%m %H:%M")
        objects.append(f"<text x='{X(i):.2f}' y='{H-6}' text-anchor='middle' font-size='10'>{t}</text>")
    return f"<svg viewBox='0 0 {W} {H}' style='width:100%;max-width:{W}px;border:1px solid #ddd'>"+"".join(objects)+"</svg>"

def balanced(pool,n,used,rng):
    d=defaultdict(list)
    for e in pool:
        key=(e["symbol"],e["known_at"])
        if key not in used:d[e["symbol"]].append(e)
    for a in d.values():rng.shuffle(a)
    syms=list(sorted(d));rng.shuffle(syms);picked=[]
    while len(picked)<n and any(d.values()):
        for sym in syms:
            while d[sym] and (sym,d[sym][-1]["known_at"]) in used:d[sym].pop()
            if d[sym] and len(picked)<n:
                e=d[sym].pop();used.add((sym,e["known_at"]));picked.append(e)
    if len(picked)!=n:raise ValueError(f"insufficient independent samples: {len(picked)}/{n}")
    return picked

def diagnose(events):
    result={}
    for name in NAMES.values():
        a=[e for e in events if e["event"]==name]
        keys={(e["symbol"],e["known_at"],e.get("side",0)) for e in a}
        result[name]={"raw":len(a),"unique_bar_side":len(keys),
                      "duplicate_same_bar_side":len(a)-len(keys)}
    items=defaultdict(dict)
    for e in events:
        if e["candidate_id"]!="-":items[(e["symbol"],e["candidate_id"])][e["event"]]=e
    x=Counter()
    for d in items.values():
        a=d.get("ACCUMULATION_LOCKED");s=d.get("SWEEP_RETURN");b=d.get("STRUCTURE_BREAK_CONFIRMED")
        if s and (not a or epoch(a["known_at"])>=epoch(s["known_at"])):x["sweep_order_error"]+=1
        if b and (not s or epoch(s["known_at"])>=epoch(b["known_at"])):x["bos_order_error"]+=1
        if a and b:
            x["bos_total"]+=1
            if a["level_low"]<=b["reference"]<=a["level_high"]:x["bos_pivot_inside_range"]+=1
            if s and epoch(b["pivot_known_at"])>epoch(s["known_at"]):x["pivot_after_sweep"]+=1
    result["structure_checks"]=dict(x)
    return result

def build(files,out):
    out.mkdir(parents=True,exist_ok=True)
    blind=out/"blind_review";private=out/"sealed_model_evidence"
    (blind/"cases").mkdir(parents=True,exist_ok=True);private.mkdir(exist_ok=True)
    rng=random.Random(SEED);bars_by={};events=[];receipts=[];alternatives=[]
    for f in sorted(files):
        b,sha=read_csv(f);sym=b[0].symbol
        if sym in bars_by:raise ValueError("duplicate symbol "+sym)
        bars_by[sym]=b
        result=replay(b).events
        events.extend(result)
        alternatives.extend(alternative_sweep(b))
        receipts.append({"symbol":sym,"csv_sha256":sha,"bars":len(b),
                         "events":dict(Counter(x["event"] for x in result))})
    if len(bars_by)!=19:raise ValueError("need exactly 19 symbols")
    detected_sweeps=defaultdict(set)
    for x in events:
        if x["event"]=="SWEEP_RETURN":detected_sweeps[x["symbol"]].add((epoch(x["known_at"]),x["side"]))
    alt_only=[x for x in alternatives if not any(abs(epoch(x["known_at"])-t)<=STEP_MS and x["side"]==side
                                                  for t,side in detected_sweeps[x["symbol"]])]
    control=[]
    for sym,b in bars_by.items():
        control.extend({"symbol":sym,"known_at":iso(x.known_at),"event":"RANDOM"}
                       for x in b[256::12])
    groups={k:[x for x in events if x["event"]==v] for k,v in NAMES.items()}
    groups["ALT_ONLY"]=alt_only;groups["RANDOM"]=control
    used=set();selected=[]
    for k,n in QUOTAS.items():
        selected.extend((k,x) for x in balanced(groups[k],n,used,rng))
    rng.shuffle(selected)
    exact=defaultdict(set)
    for x in events:exact[(x["symbol"],x["known_at"])].add(x["event"])
    sealed=[];labels=[];links=[]
    for stratum,x in selected:
        sym,when=x["symbol"],x["known_at"];t=epoch(when)
        id=hashlib.sha256((str(SEED)+sym+when).encode()).hexdigest()[:12]
        flags={key:ev in exact[(sym,when)] for key,ev in FLAGS.items()}
        sealed.append({"case_id":id,"stratum":stratum,"symbol":sym,"known_at":when,
                       "event":x["event"],"candidate_id":x.get("candidate_id"),"model_flags":flags})
        labels.append({"case_id":id,**{key:"" for key in FLAGS},"amd_sequence":"",
                       "certainty":"","reviewer":"","notes":""})
        views="".join(svg(asof(bars_by[sym],t,tf,n),f"{tf}m — только история")
                      for tf,n in [(15,100),(60,80),(240,36)])
        document=f"""<!doctype html><html lang='ru'><meta charset='utf-8'>
<style>body{{font:15px Arial;max-width:990px;margin:25px auto;padding:0 16px}}p{{color:#565f70}}</style>
<h2>Слепой график {id}</h2><p>{html.escape(sym)} / {html.escape(when)} UTC.
Проверяйте признаки только на ПОСЛЕДНЕЙ завершённой свече; будущего нет.</p>
{views}<p><a href='../index.html'>К списку</a></p></html>"""
        (blind/"cases"/f"{id}.html").write_text(document,encoding="utf-8")
        links.append(f"<li><a href='cases/{id}.html'>{id}</a> — {sym}, {when}</li>")
    with (blind/"labels_template.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(labels[0]))
        w.writeheader();w.writerows(labels)
    (blind/"index.html").write_text("<!doctype html><html lang='ru'><meta charset='utf-8'>"
       "<h1>MSR-02: 180 слепых контрольных графиков</h1><p>Категории отбора и ответы алгоритма скрыты. "
       "Графики только из прошлых закрытых свечей. Форму labels_template.csv заполнить yes/no/uncertain."
       "</p><ol>"+"".join(links)+"</ol></html>",encoding="utf-8")
    (blind/"HOW_TO_LABEL_RU.md").write_text(
       "# Слепая разметка MSR-02\n\n"
       "1. Откройте index.html, все 180 графиков. НЕ открывайте sealed_model_evidence.\n"
       "2. Для каждой строки labels_template.csv: yes/no/uncertain. Не гадайте: uncertain.\n"
       "3. Оценивайте только последнее завершённое событие на крайней правой свече: "
       "accumulation — впервые зафиксирован значимый диапазон; sweep_return — новый ложный пробой с возвратом; "
       "structure_break — значимый структурный BOS, не локальный шум; fvg — новый трёхсвечный дисбаланс; "
       "amd_sequence — вся последовательность уже видима к срезу.\n"
       "4. Запишите reviewer и notes. После независимой разметки запустите функцию score.\n"
       "Отбор по событиям намеренно не репрезентативен по частоте: оценка согласия "
       "на 180 случаях не является популяционной точностью.\n",encoding="utf-8")
    payload={"cases":sealed,"seed":SEED,"quota":QUOTAS,
             "status":"SEALED_MODEL_FLAGS_NOT_INDEPENDENT_LABELS"}
    body=json.dumps(payload,ensure_ascii=False,sort_keys=True)
    payload["sha256_without_self"]=hashlib.sha256(body.encode()).hexdigest()
    (private/"sealed_flags.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    diagnostics={"mode":"RESEARCH_ONLY_NO_ORDERS","records":receipts,
        "bars":sum(r["bars"] for r in receipts),"model_events":dict(Counter(x["event"] for x in events)),
        "alternative_sweep_all":len(alternatives),"alternative_only_sweep":len(alt_only),
        "event_multiplication":diagnose(events),"cases":len(sealed),
        "reviewer_labels":0,"semantic_accuracy":"UNKNOWN_NOT_ASSESSED"}
    (private/"machine_diagnostics.json").write_text(json.dumps(diagnostics,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"RESULTS_RU.md").write_text("# MSR-02 — итог машинного аудита\n\n"+
       "Код и причинность проверяются автоматически. Независимой экспертной разметки пока нет.\n\n"+
       f"Свечи 15m: {diagnostics['bars']}; случаев для разметки: {len(sealed)}.\n\n"+
       "Дополнительный детектор — независимый механический контроль, НЕ эталон правильного чтения.\n\n"+
       json.dumps(diagnostics,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"bars":diagnostics["bars"],"cases":len(sealed),
                      "alt_only":len(alt_only),"multiplication":diagnostics["event_multiplication"]},ensure_ascii=False))
    return diagnostics

def score(sealed,labels,out):
    data=json.loads(sealed.read_text(encoding="utf-8"))
    flags={x["case_id"]:x["model_flags"] for x in data["cases"]}
    report={k:Counter() for k in FLAGS}
    seen=set()
    with labels.open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            id=row["case_id"]
            if id in seen or id not in flags:raise ValueError("duplicate or unknown case "+id)
            seen.add(id)
            for key in FLAGS:
                a=row.get(key,"").strip().lower()
                if a not in ("yes","no","uncertain",""):raise ValueError("invalid answer "+a)
                if a in ("uncertain",""):continue
                positive=flags[id][key]
                report[key]["agreement" if positive==(a=="yes") else "disagreement"]+=1
                if positive and a=="no":report[key]["machine_yes_expert_no"]+=1
                if not positive and a=="yes":report[key]["machine_no_expert_yes"]+=1
    result={"status":"BLIND_AGREEMENT_ONLY_NOT_MARKET_TRUTH","submitted":len(seen),
            "not_population_precision_recall":True,
            "comparison":{k:dict(v) for k,v in report.items()}}
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    return result

def main():
    p=argparse.ArgumentParser()
    sub=p.add_subparsers(dest="cmd",required=True)
    a=sub.add_parser("build");a.add_argument("--csv",required=True,nargs="+",type=Path);a.add_argument("--out",required=True,type=Path)
    b=sub.add_parser("score");b.add_argument("--sealed",required=True,type=Path);b.add_argument("--labels",required=True,type=Path);b.add_argument("--out",required=True,type=Path)
    x=p.parse_args()
    if x.cmd=="build":build(x.csv,x.out)
    else:print(json.dumps(score(x.sealed,x.labels,x.out),ensure_ascii=False))
if __name__=="__main__":main()
