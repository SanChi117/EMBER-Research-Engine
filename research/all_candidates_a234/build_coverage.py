import json
import re
from pathlib import Path
from collections import Counter

root = Path(__file__).parent
docs = json.loads((root/'prior_evidence.json').read_text())
registry = json.loads((root/'registry.json').read_text())
known = {r['source'].lower() for r in registry}
veto = {'abdullae100/perp-quant-lab','octopustakopi/funding-rate-alpha','agarwalchirag535-lab/smallcap-pump-reversal'}
sources = {}
for d in docs:
    for line in d['content'].splitlines():
        for owner, repo in re.findall(r'https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)',line):
            key = owner+'/'+repo
            if key.lower() == 'sanchi117/ember-research-engine':
                continue
            sources.setdefault(key,[]).append({'document':d['path'],'blob':d['sha'],'excerpt':line})
coverage=[]
for source,evidence in sorted(sources.items()):
    state = 'REGISTERED' if source.lower() in known else ('USER_VETO' if source.lower() in veto else 'UNCLASSIFIED_SOURCE_REVIEW_REQUIRED')
    coverage.append({'source':source,'coverage_status':state,'evidence':evidence})
record={'scope':'URL census of selected historical reports; not exhaustive all-repository/all-chat census',
        'documents_read':len(docs),'registry_records':len(registry),
        'records_may_group_related_variants':True,
        'coverage_counts':dict(Counter(x['coverage_status'] for x in coverage)),
        'sources':coverage,
        'remaining_scope':['Other branches and historical handoffs not fully inventoried',
          'Bare author-only references require repository resolution',
          'Grouped variants require individual source IDs before economic tests',
          'Early EMBER/SMOKE internal variants: legacy evidence audit, not new original candidates']}
(root/'A234_COVERAGE.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
md=['# A234 — расширенный реестр переоценки','',
    '74 записи источников/вариантов, не 74 завершённых теста и не 74 независимых механизма. Все REVIEW_OPEN.','',
    '| ID | Кандидат | Циклы | Ветка проверки | Что требуется |','|---|---|---|---|---|']
for r in registry:
    md.append('| '+' | '.join(r[k] for k in ('id','name','prior_cycles','review_lane','next_required_check'))+' |')
(root/'A234_REGISTRY_RU.md').write_text('\n'.join(md)+'\n')
assert len({r['id'] for r in registry})==len(registry)
assert not (known & veto)
assert not any(r['new_native_backtest_completed'] or r['verified'] for r in registry)
print(json.dumps({'documents':len(docs),'records':len(registry),'coverage':record['coverage_counts'],
    'unclassified':[r['source'] for r in coverage if r['coverage_status']=='UNCLASSIFIED_SOURCE_REVIEW_REQUIRED']},ensure_ascii=False))
