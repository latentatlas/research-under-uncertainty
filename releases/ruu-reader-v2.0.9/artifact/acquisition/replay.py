"""Offline reconstruction of the existing sample. No RNG, actor process or provider call.
Historical times/PIDs are identity-checked records, not regenerated attestations.
"""
from pathlib import Path
import sys,json,time,argparse,hashlib
from collections import Counter
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H));sys.path.insert(0,str(H.parent/'inspection'))
import population as pop
import sampling,wire,compute,selector
from loader import source,original_hash,records,project_records,read,need,canonical,digest_bytes

def identity_chain():
    bindings=read(H/'SOURCE-BINDINGS.json')['files']
    for n,b in bindings.items():need(digest_bytes((H/n).read_bytes())==b['distributed_sha256'],'source_bytes:'+n)
    for name in bindings:
        if name.startswith('source/') and name.endswith('.json'):source(Path(name).stem)
    intent=source('structural-intent')
    for key,name in [('DESIGN.json','sampling-design'),('PRIVATE-DEVELOPMENT-WORLDS.json','development-fixtures')]:need(intent['sources'][key]==original_hash(name),'structural_intent:'+key)
    need(intent['sources']['population.py']==bindings['population.py']['source_sha256'],'structural_generator_identity')
    closure=source('records-closure');need(closure['status']=='passed' and closure['all_actor_children_exited'],'saved_records_closure')
    for field,name in [('commitment_sha256','commitment'),('events_sha256','events'),('readout_sha256','readout'),('truth_audit_sha256','truth-audit')]:need(closure[field]==original_hash(name),'closure:'+field)
    main=source('main-closure');need(main['status']=='passed' and main['completed_pairs']==5000 and main['technical_missing']==main['unstarted']==main['provider_calls']==0,'main_closure')
    for field,name in [('draw_sha256','draw'),('freeze_sha256','freeze'),('records_closure_sha256','records-closure'),('source_bindings_sha256','source-bindings')]:need(main[field]==original_hash(name),'main_closure:'+field)
    classes={pop.canonical(t) for n in (1,2,3) for t in pop.enumerate_tables(n)}
    counts=dict(Counter(str(len(t)//2) for t in classes));need(counts=={'1':4,'2':144,'3':11352},'canonical_class_counts')
    fixtures=source('development-fixtures');excluded={pop.canonical(pop.from_world(w)) for w in fixtures['worlds']}
    initial=source('initial-catalog');tables=[tuple(map(tuple,t)) for t in initial['worlds']]
    need(tables==sorted(t for t in classes if len(t)==6 and t not in excluded) and len(tables)==11350,'initial_catalog_order')
    need(source('sampling-design')['primary_population']['minimal_reachable_states']==3,'sampling_class')
    first=read(H/'source/first-development-index.json');rows=first['rows'];old=sorted({r['world_index'] for r in rows})
    need(len(rows)==1600 and len(old)==1499 and all(r['unit_rank']//256==r['world_index'] for r in rows),'first_exclusions')
    reconstructed=[]
    for i,r in enumerate(rows,1):
        wi,actions=sampling.split(r['unit_rank'],11350);table=initial['worlds'][wi]
        world={'schema':'private-finite-machine-v0.4','states':3,'initial_state':0,'edges':[{'from':s,'action':a,'to':table[2*s+a][0],'output':table[2*s+a][1]} for s in range(3) for a in (0,1)]}
        reconstructed.append({**r,'actions':actions,'history_id':f'h{i:04d}','target_id':f'i{i:04d}','world':world})
    need(digest_bytes((json.dumps(reconstructed,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())==first['source_sha256'],'full_first_development_manifest')
    intermediate=source('intermediate-catalog');indices=[i for i in range(11350) if i not in set(old)]
    need(intermediate['original_catalog_sha256']==original_hash('initial-catalog'),'initial_binding')
    need(intermediate['development_manifest_sha256']==first['source_sha256'],'development_index_binding')
    need(intermediate['excluded_development_world_indices']==old and intermediate['original_indices']==indices,'intermediate_indices')
    need(intermediate['worlds']==[initial['worlds'][i] for i in indices] and len(indices)==9851,'intermediate_tables')
    prior=source('prior-draw');used=sorted({rank//256 for rank in prior['ranks']});need(len(prior['ranks'])==1600 and len(used)==1479,'second_exclusions')
    e=source('eligibility');left=[i for i in range(9851) if i not in set(used)]
    need(e['source_catalog_sha256']==original_hash('intermediate-catalog') and e['prior_draw_sha256']==original_hash('prior-draw'),'eligibility_bindings')
    need(e['source_local_indices_excluded']==used and e['eligible_source_local_indices']==left and len(left)==8372,'eligible_local_indices')
    need(e['eligible_original_indices']==[indices[i] for i in left] and e['original_indices_excluded_now']==[indices[i] for i in used],'eligible_original_indices')
    frame=source('frame');need(frame['remaining_class_history_pairs']==8372*256==2143232 and frame['eligibility_sha256']==original_hash('eligibility'),'frame')
    f=source('freeze')
    for field,n in [('catalog_sha256','intermediate-catalog'),('eligibility_sha256','eligibility'),('seed_sha256','seed'),('design_contract_sha256','design-contract')]:need(f[field]==original_hash(n),'freeze:'+field)
    for name,h in f['source_hashes'].items():need(digest_bytes((H/'historical-code'/(name+'.txt')).read_bytes())==h,'frozen_code:'+name)
    for name in ('compute.py','selector.py','wire.py'):
        need(digest_bytes((H.parent/'inspection'/name).read_bytes())==f['source_hashes']['actor/'+name],'active_scientific_code:'+name)
    need(source('structural-intent')['created_utc']<f['created_utc'],'local_design_precedes_main')
    saved=source('draw');draw=sampling.draw(2143232,5000,sampling.words(source('seed')['seed_hex']));need(all(saved[k]==v for k,v in draw.items()),'exact_rejection_draw')
    for field,n in [('catalog_sha256','intermediate-catalog'),('eligibility_sha256','eligibility'),('seed_sha256','seed')]:need(saved[field]==original_hash(n),'draw_binding:'+field)
    plan=source('record-plan');need(plan['source_manifest_sha256']==original_hash('draw') and plan['main_binding']['freeze_sha256']==original_hash('freeze'),'plan_draw_freeze')
    return intermediate,e,draw,{'classes_by_minimal_states':counts,'original_catalog':11350,'first_exclusions':1499,'intermediate':9851,'second_exclusions':1479,'eligible_classes':8372,'pairs':2143232,'distinct_sample_pairs':len(set(draw['ranks'])),'distinct_sample_classes':len({x//256 for x in draw['ranks']}),'rejected_words':sum(not r['accepted'] for r in draw['receipts'])}

def observe(table,state,query,view,arm):
    need(query in wire.QUERIES,'only_permitted_query')
    next_state,output=table[2*state+(query=='q1')]
    return {'schema':'one-step-observation-v1','trial_id':view['trial_id'],'arm':arm,'view_sha256':wire.digest(view),'query_id':query,'output':output}

def run(limit=None):
    started=time.monotonic();catalog,e,draw,identities=identity_chain();raw=records();bindings=source('source-bindings')
    n=5000 if limit is None else limit;need(0<n<=5000,'replay_limit');states=[];computed=[];posthoc=[]
    for i,(rank,r,b) in enumerate(zip(draw['ranks'][:n],raw[:n],bindings[:n])):
        tid=f't{i+1:04d}';ei,actions=sampling.split(rank,8372);si=e['eligible_source_local_indices'][ei];oi=e['eligible_original_indices'][ei];table=catalog['worlds'][si];state=0;history=[]
        for action in actions:state,y=table[2*state+action];history.append([action,y])
        view=wire.make_view(tid,history);need(view==r['view'],'replayed_view:'+tid)
        expected={'trial_id':tid,'rank':rank,'eligible_index':ei,'source_index':si,'original_index':oi,'table_sha256':wire.digest(table),'actions_sha256':wire.digest(actions),'original_state_sha256':wire.digest([table,state,history]),'view_sha256':wire.digest(view)}
        need(b==expected,'raw_source_binding:'+tid)
        arms={}
        for arm in wire.ARMS:
            adaptive=arm=='adaptive';scan=compute.scan(history,wire.QUERIES) if adaptive else None
            query=selector.select_query(scan['cardinalities']) if adaptive else 'q0'
            if adaptive:scan['work']['selection_branch_checks']=4
            sel={'schema':'query-selection-v1','trial_id':tid,'arm':arm,'view_sha256':wire.digest(view),'query_id':query,'pre_observation_history_checks':scan['work']['history_checks'] if adaptive else 0,'pre_observation_query_evaluations':scan['work']['query_candidate_evaluations'] if adaptive else 0,'possible_gain_loss':compute.possibilities(scan,query) if adaptive else None}
            obs=observe(table,state,query,view,arm);wire.guard_receipt(obs,view,arm,query)
            if scan is None:scan=compute.scan(history,('q0',))
            cert=compute.finish(scan,query,obs['output'],adaptive)
            result={'schema':'arm-result-v1','trial_id':tid,'arm':arm,'view_sha256':wire.digest(view),'selection_sha256':wire.digest(sel),'observation_sha256':wire.digest(obs),'query_id':query,'output':obs['output'],**cert,'work':scan['work']}
            saved=r['arms'][arm];need(sel==saved['selection'] and obs==saved['observation'],'replayed_selection_observation:'+tid+':'+arm)
            need(result=={k:v for k,v in saved['result'].items() if k not in ('timing','pid','process_io_gate')},'replayed_result:'+tid+':'+arm)
            arms[arm]=result
            if adaptive:
                # Additional, retrospective comparators. Reuse the reconstructed
                # candidate scan, but never change historical work counters or arms.
                alternative={}
                for q in wire.QUERIES:
                    response=table[2*state+(q=='q1')][1]
                    support=[j for j,count in enumerate(scan['counts'][q][response]) if count]
                    need(bool(support),'posthoc_nonempty_support')
                    alternative[q]={'certificate':len(support)==1,'prediction':support[0] if len(support)==1 else None}
                posthoc.append(alternative)
        computed.append(arms);states.append((table,state))
        if (i+1)%500==0:print(json.dumps({'replayed_pairs':i+1,'of':n}),file=sys.stderr,flush=True)
    # Predictions for all requested records are fixed before target comparisons.
    truth=source('truth-audit')[:n];wrong=0;posthoc_wrong=0
    for i,((table,state),arms,saved) in enumerate(zip(states,computed,truth)):
        vals=[]
        for action in (0,1):
            next_state,_=table[2*state+action];_,y=table[2*next_state];vals.append(y)
        target=2*vals[0]+vals[1];bad=sum(int(a['certificate'] and a['prediction']!=target) for a in arms.values());wrong+=bad
        need(saved=={'trial_id':f't{i+1:04d}','truth':target,'wrong_certificates':bad},'replayed_truth')
        posthoc_wrong+=sum(int(a['certificate'] and a['prediction']!=target) for a in posthoc[i].values())
        need(posthoc[i]['q0']['certificate']==arms['fixed']['certificate'],'posthoc_q0_reconstruction')
    report={'passed':True,'mode':'full_existing_sample' if n==5000 else 'prefix_smoke_only','pairs_replayed':n,'identity_chain':identities,'wrong_certificates':wrong,'committed_records_exact':5000,'replayed_history_steps':8*n,'replayed_query_responses':2*n,'replayed_target_steps':4*n,'new_sample_draws':0,'provider_calls':0,'participant_programs_executed':0,'historical_process_or_timing_reattested':False,'independent_laboratory':False,'replay_wall_seconds':time.monotonic()-started}
    totals={q:sum(r[q]['certificate'] for r in posthoc) for q in wire.QUERIES}
    report['posthoc_comparators']={'scope':'existing-input retrospective calculation, not preregistered evidence', 'draws':n,
        'fixed_q0_certificates':totals['q0'],'fixed_q1_certificates':totals['q1'],
        'fair_random_expected_certificates':(totals['q0']+totals['q1'])/2,
        'adaptive_certificates':sum(r['adaptive']['certificate'] for r in computed),
        'wrong_certificates_in_q0_q1_reconstruction':posthoc_wrong,
        'random_policy_observed':False,'new_live_observations':0,'new_sample_draws':0,
        'primary_analysis_changed':False,'draw_sha256':original_hash('draw'),
        'reconstructed_alternatives_sha256':wire.digest(posthoc)}
    need(posthoc_wrong==0,'posthoc_validity')
    if n==5000:
        sys.path.insert(0,str(H.parent));import check
        got=check.acquisition(project_records(raw,source('truth-audit')));ref=read(H.parent/'data/acquisition-reference.json')
        for k in ('cells','decision','diagnostics','work','wrong_certificates'):need(got[k]==ref[k],'aggregate:'+k)
        report['acquisition']=got
        need(totals=={'q0':283,'q1':219},'posthoc_comparator_counts')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);p.add_argument('--smoke',type=int);p.add_argument('--show-record');a=p.parse_args()
    if a.show_record:
        rows=records();matching=[r for r in rows if r['view']['trial_id']==a.show_record];need(len(matching)==1,'record_id');print(json.dumps(matching[0],indent=2));return
    result=run(a.smoke)
    if a.output:
        need(not a.output.exists() and H.parent.parent not in a.output.resolve().parents,'new_output_outside_bundle');a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='acquisition'},sort_keys=True))
if __name__=='__main__':main()
