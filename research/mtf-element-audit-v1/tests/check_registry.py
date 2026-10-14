"""Structural self-consistency only. NOT course semantic validation."""
import collections,copy,json,sys
from pathlib import Path
SRC=Path('/mnt/data/MTF_SPECIFICATION_FROM_ZERO_20261014')
REQ=('id','title','layer','tf','meaning','appears','confirms','ends','output','provenance','current','gate')

def check(reg,sts):
 errs=[];items=reg.get('items',[]);entries=sts.get('entries',[])
 ids=[x.get('id') for x in items];sid=[x.get('id') for x in entries]
 if len(items)!=45:errs.append('COUNT_NOT_45')
 if len(ids)!=len(set(ids)):errs.append('DUPLICATE_ID')
 if len(entries)!=len(set(sid)):errs.append('DUPLICATE_STATUS_ID')
 if set(ids)!=set(sid):errs.append('ID_SET_MISMATCH')
 for item in items:
  for field in REQ:
   if not isinstance(item.get(field),str) or not item[field].strip():errs.append(f'BLANK_{field}_{item.get("id")}')
 for o in entries:
  if o.get('component_approved') and o.get('status')!='INFRA_ENGINEERING_CHECKED':errs.append('INVALID_APPROVAL_'+str(o.get('id')))
 return sorted(set(errs))

def main():
 reg=json.loads((SRC/'ELEMENTS_REGISTRY.json').read_text(encoding='utf8'))
 sts=json.loads((SRC/'ELEMENTS_STATUS.json').read_text(encoding='utf8'))
 normal=check(reg,sts)
 mutations={}
 for case in ('remove','duplicate','empty_gate','status_wrong_id','wrong_approval'):
  a,b=copy.deepcopy(reg),copy.deepcopy(sts)
  if case=='remove':a['items'].pop()
  elif case=='duplicate':a['items'][0]['id']=a['items'][1]['id']
  elif case=='empty_gate':a['items'][0]['gate']=''
  elif case=='status_wrong_id':b['entries'][0]['id']='FAKE'
  elif case=='wrong_approval':b['entries'][4]['component_approved']=True
  mutations[case]=check(a,b)
 res={'test':'C00_registry_structure','actual_45':len(reg['items']),'status_count':len(sts['entries']),
      'normal_errors':normal,'mutation_tests':mutations,
      'fields_per_item':len(REQ),
      'exact_source_field_present':sum(bool(x.get('source_uri') or x.get('source_ref') or x.get('source_quote')) for x in reg['items']),
      'status_counts':dict(collections.Counter(x['status'] for x in sts['entries'])),
      'conclusion':'STRUCTURE_PASSES_BUT_SOURCE_TRACEABILITY_FAILS',
      'integrity_passed':not normal and all(mutations.values()),
      'semantic_approval':False}
 print(json.dumps(res,ensure_ascii=False,indent=2))
 return 0 if res['integrity_passed'] else 1
if __name__=='__main__':sys.exit(main())