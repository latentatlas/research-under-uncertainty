"""Portable record-only reconstruction; no participant programs, actors or physics."""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import json,hashlib,sys
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
from executable_selector import parse,validate,consume_final,crossing,digest,RULES,ContractError
from crossing_readout import annotate
from wire import field_text
import paired_statistics
def need(ok,code):
    if not ok:raise ValueError(code)
def equal(a,b,code):need(a==b,code)
def read(p):return json.loads(p.read_text())
def scan(rows):
    """Independent per-record scanner: sum (same argmin as uniform mean), column maxima.
    No pair ID, second record, observed cross cells or census labels are available here.
    """
    sums=[sum(col,Fraction(0)) for col in zip(*rows)]
    peaks=[max(col) for col in zip(*rows)]
    return {'uniform_mean':min(range(len(sums)),key=lambda j:(sums[j],j)),
            'worst_case':min(range(len(peaks)),key=lambda j:(peaks[j],j))}

def one_distinct_row(rows):return len(set(rows))==1
def contrast(a,b,labels):
    x,y=labels[a],labels[b]
    return {'action_changed':a!=b,'category_changed':x!=y,
            'P_L_flip':{x,y}=={'P','L'},'involves_U':'U' in (x,y)}

def reconstruct():
    data=read(H/'data/crossing.json');aa=data['allocation'];contexts=data['contexts'];labelmaps=data['labelmaps']
    equal([a['order'] for a in aa],list(range(1,33)),'ordered_slots')
    equal(len({a['trial_id'] for a in aa}),32,'unique_ids')
    reports={};texts={};results={};groups={}
    supported={'supported_observational_record','executed_record_by_construction'}
    for a in aa:
        tr=data['trials'][a['trial_id']];r=tr['result'];raw=tr['final_text'];captures=[]
        equal(r['allocation'],a,'allocation_binding')
        need(r['status']=='evaluated' and r['action_applied'] is True,'evaluated_slot')
        d=consume_final(raw,a['condition'],contexts[a['case_id']],lambda action:captures.append(action))
        equal(d,tr['decision'],'frozen_decision_reconstruction');equal(len(captures),1,'one_action')
        equal(tr['action'],{'action_id':d['action_id'],'requested_action':captures[0]},'action_binding')
        labels=labelmaps[a['case_id']]['labels'];equal(r['label'],labels[d['action_id']],'native_label')
        results[a['trial_id']]=r
        groups.setdefault((a['condition'],a['block_id']),[]).append(a)
        if d['instrumentation'] not in supported:continue
        text=field_text(raw,'record');rows,rule=validate(parse(text),contexts[a['case_id']]);choices=scan(rows)
        equal(choices[rule],d['action_id'],'independent_native_selection')
        equal(choices,d['record']['diagnostics']['rule_actions'],'independent_rule_choices')
        if one_distinct_row(rows):equal(len(set(choices.values())),1,'identical_row_theorem')
        texts[a['trial_id']]=text
        reports[a['trial_id']]={'trial_id':a['trial_id'],'order':a['order'],'case_id':a['case_id'],
          'condition':a['condition'],'menu_sha256':a['menu_sha256'],'native_action':d['action_id'],'native_label':r['label'],
          'rule':rule,'rows':len(rows),'distinct_rows':len(set(rows)),'duplicate_rows':len(rows)-len(set(rows)),
          'structure_proves_family_invariant':one_distinct_row(rows),'scan_choices':choices,
          'scan_labels':{k:labels[v] for k,v in choices.items()},
          'family_contrast':contrast(choices['uniform_mean'],choices['worst_case'],labels)}
    # Compare only after independent views above have been computed.
    archived=data['interventions']; pair_rows=[]
    for (cond,block),slots in sorted(groups.items()):
        slots=sorted(slots,key=lambda x:x['repeat']);equal([a['repeat'] for a in slots],[1,2],'repeat_identity')
        pair_id=block+'/'+cond
        ids=[a['trial_id'] for a in slots]
        if any(i not in reports for i in ids):
            need(pair_id in archived['conditions'][cond]['missing_pairs'],'missing_pair_binding')
            pair_rows.append({'pair_id':pair_id,'condition':cond,'eligible':False,'reason':'unsupported_or_missing_record',
                              'incremental_effect':None,'interpretation':'not_assessed'})
            continue
        own=[reports[i] for i in ids];labels=labelmaps[slots[0]['case_id']]['labels']
        raw=crossing(*(texts[i] for i in ids),contexts[slots[0]['case_id']]);ann=annotate(raw,labelmaps[slots[0]['case_id']])
        equal({'crossing':raw,'annotated':ann},archived['conditions'][cond]['pair_reports'][pair_id],'archived_crossing_exact')
        same=own[0]['rule']==own[1]['rule'];native=[x['native_action'] for x in own]
        for c in raw['observed']:
            i=c['pool_repeat']-1;j=c['rule_repeat']-1
            equal(c['action_id'],own[i]['scan_choices'][own[j]['rule']],'scan_observed_cell')
            if same:equal(c['action_id'],native[i],'same_rule_native_identity')
        for c in raw['rule_family']:
            equal(c['action_id'],own[c['pool_repeat']-1]['scan_choices'][c['rule']],'scan_family_cell')
        fc=[x['family_contrast'] for x in own]
        family_actions={c['action_id'] for c in raw['rule_family']}
        nr=contrast(native[0],native[1],labels)
        pair_rows.append({'pair_id':pair_id,'condition':cond,'eligible':True,'trial_ids':ids,'same_observed_rule':same,
          'native_repeat_contrast':nr,'observed_cells':4,'observed_cells_inferred_by_native_and_same_rule':4 if same else 2,
          'observed_off_diagonal_cells_inferred_without_crossing':2 if same else 0,
          'family_cells':4,'family_cells_inferred_by_native_and_identical_rows':2+sum(x['structure_proves_family_invariant'] for x in own),
          'structure_settles_whole_family':all(x['structure_proves_family_invariant'] for x in own),
          'family_action_change':any(x['action_changed'] for x in fc),'family_P_L_flip':any(x['P_L_flip'] for x in fc),
          'family_involves_U':any(x['involves_U'] for x in fc),
          'family_new_action_ids_vs_native':sorted(family_actions-set(native)),
          'family_new_categories_vs_native':sorted({labels[i] for i in family_actions}-{labels[i] for i in native}),
          'scan_matches_observed_cells':4,'scan_matches_family_cells':4,
          'full_additional_cells_beyond_scan':0,
          'scope':'Common-menu supported-rule results only; labels reused, not new samples.'})
    conditions={}
    for cond in ['optional_record','executable_record']:
        rr=[x for x in reports.values() if x['condition']==cond];pp=[x for x in pair_rows if x['condition']==cond];ep=[x for x in pp if x['eligible']]
        conditions[cond]={'planned_trials':16,'planned_pairs':8,'eligible_records':len(rr),'eligible_pairs':len(ep),
          'ineligible_pairs':8-len(ep),'ineligible_effect':None,'technical_missing':0,'protocol_invalid':0,'unstarted':0,
          'categories':dict(Counter(r['label'] for r in results.values() if r['allocation']['condition']==cond)),
          'single_row_records':sum(x['rows']==1 for x in rr),'duplicate_row_records':sum(x['duplicate_rows']>0 for x in rr),
          'identical_row_certificate_records':sum(x['structure_proves_family_invariant'] for x in rr),
          'record_scan_invariant_records':sum(not x['family_contrast']['action_changed'] for x in rr),
          'record_scan_changed_records':sum(x['family_contrast']['action_changed'] for x in rr),
          'observed_cells':sum(x['observed_cells'] for x in ep),
          'observed_cells_inferred_from_native_same_rule':sum(x['observed_cells_inferred_by_native_and_same_rule'] for x in ep),
          'family_cells':sum(x['family_cells'] for x in ep),
          'family_cells_inferred_from_native_identical_rows':sum(x['family_cells_inferred_by_native_and_identical_rows'] for x in ep),
          'family_pairs_settled_by_identical_rows':sum(x['structure_settles_whole_family'] for x in ep),
          'family_action_change_pairs':sum(x['family_action_change'] for x in ep),
          'family_P_L_flip_pairs':sum(x['family_P_L_flip'] for x in ep),
          'family_U_pairs':sum(x['family_involves_U'] for x in ep),
          'family_new_actions_vs_native_sum':sum(len(x['family_new_action_ids_vs_native']) for x in ep),
          'family_new_categories_vs_native_sum':sum(len(x['family_new_categories_vs_native']) for x in ep),
          'full_additional_cells_beyond_record_scan':sum(x['full_additional_cells_beyond_scan'] for x in ep) if ep else None,
          'interpretation':'assessed' if ep else 'not_assessed'}
    # Existing transfer adapter remains fixed and is accounted for independently.
    transfer=read(H/'source/transfer-interventions.json')
    transfer_counts={k:transfer[k] for k in ['trial_denominator','pair_denominator','supported_pairs','supported_trials']}
    equal(transfer_counts,{'trial_denominator':48,'pair_denominator':24,'supported_pairs':0,'supported_trials':1},'old_transfer_preserved')
    pilot=pilot_audit()
    return {'schema':'crossing-incremental-value-v1','retrospective':True,'conditions':conditions,'historical_transfer':transfer_counts,
      'pilot':pilot,'new_model_calls':0,'new_physics_calls':0,'participant_programs_executed':0,
      'cross_labels':'reused bound archived census','comparison':'deterministic operation ablation, same archive access; no performance superiority estimate',
      'continuous_labels':'conditional on unchanged numerical/runtime premises',
      'independent_lab_validation':False,'usage_of_this_assistant':'unmeasured'}, {'records':list(reports.values()),'pairs':pair_rows}

def pilot_audit():
    refs=read(H.parent/'legacy-replay/data/references.json');primary=[x for x in refs['graded_cells'] if x['group']=='primary']
    equal(len(primary),8,'eight_pilot_primary_cells')
    score={'feasibility_preserved_by_witness':'P','feasibility_lost_by_certificate':'L'}
    by_case={}
    for x in primary:
        need(x['status']=='computed','pilot_primary_status')
        label=score.get(x['diagnostic_score'],'U');g=refs['grade_references'][x['grade_path']]
        need(not(g['after']['witness_success'] and g['after']['certificate']['certified']),'pilot_conflict')
        equal(label,'P' if g['after']['witness_success'] else 'L' if g['after']['certificate']['certified'] else 'U','pilot_grade_evidence')
        by_case.setdefault(x['case'],{})[x['id']]=label
    expected={'boundary-01':{'A1-R1':'L','A1-R2star':'P','A2-R1':'P','A2-R2star':'P'},
              'boundary-02':{'A1-R1':'P','A1-R2':'L','A2-R1':'L','A2-R2':'L'}}
    equal(by_case,expected,'published_pilot_primary_tables')
    native={case:Counter('P' if g['after']['witness_success'] else 'L' if g['after']['certificate']['certified'] else 'U'
             for g in refs['pilot'].values() if g['case_id']==case) for case in expected}
    equal(native['boundary-01'],Counter({'P':1,'L':1}),'pilot_B_native_labels')
    equal(native['boundary-02'],Counter({'P':1,'L':1}),'pilot_D_native_labels')
    sensitivity=read(H/'source/pilot-sensitivity.private.json')
    selectors=sensitivity['selectors'];equal(len(selectors),5,'five_selectors')
    need(all(x['native_compatible'] for x in selectors),'native_compatible_selectors')
    return {'total_pilot_trials':8,'total_pilot_history_pairs':4,'declared_component_pairs':2,
      'other_history_pairs':'not_assessed_for_component_crossing; no extrapolation',
      'primary_cells':8,'native_cells':4,'non_native_cells':4,'tables':by_case,
      'native_categories':{'B':['L','P'],'D':['P','L']},
      'cross_categories_absent_from_native':{'B':[],'D':[]},
      'off_diagonal_categories':{'B':['P','P'],'D':['L','L']},
      'D_interpretation':'Native P/L outcomes already include preservation; off-diagonal losses reveal the conditional joint-change pattern from the losing A2/R2 combination.',
      'B_interpretation':'Declared-completion rescue is not invariant across native-compatible completions.',
      'B_selectors':[{k:x[k] for k in ['selector','native_compatible','diagnoses']} for x in selectors],
      'full_vs_record_scan':'not_assessed: heterogeneous optimizers/mappings, no new execution under current authorization',
      'pilot_baseline_limit':'Archive-table comparison only; not a same-rule common-menu head-to-head extension',
      'auxiliary_cells_preserved':len(refs['graded_cells'])-8,
      'source_physics_reexecuted':False}

def controls():
    checks=[]
    def ok(name,condition):need(condition,name);checks.append(name)
    f=Fraction
    one=((f(1,3),f(1,4)),)
    ok('single_and_identical_rows_invariant',len(set(scan(one).values()))==1 and scan(one)==scan(one*3))
    dup=((f(0),f(3,5)),(f(0),f(3,5)),(f(1),f(3,5)))
    ok('duplicate_rows_do_not_prove_invariance',not one_distinct_row(dup) and scan(dup)['uniform_mean']!=scan(dup)['worst_case'])
    ok('changed_action_can_keep_P',contrast(0,1,['P','P'])=={'action_changed':True,'category_changed':False,'P_L_flip':False,'involves_U':False})
    ok('U_is_not_a_resolved_loss',not contrast(0,1,['P','U'])['P_L_flip'] and contrast(0,1,['P','U'])['involves_U'])
    context={'case_id':'synthetic','menu':[0,1],'menu_sha256':digest([0,1])}
    rec={'schema':'executable-decision-record-v1','case_id':'synthetic','menu_sha256':context['menu_sha256'],
         'loss_definition_id':'remaining_task_failure_forecast_v1','candidate_losses':[[f(0),f(1)]],'rule':'uniform_mean'}
    bad={**rec,'case_id':'wrong'}
    try:validate(bad,context)
    except ContractError as e:ok('wrong_case_rejected',e.code=='record_identity')
    else:raise ValueError('identity_not_rejected')
    parsed=parse('{"x":0.50000000000000000001,"y":0.5}')
    ok('raw_decimal_precision',parsed['x']>parsed['y'])
    # Exhaust a small synthetic two-action/two-row grid, including ties; no task physics.
    from itertools import product
    from executable_selector import select
    count=0
    for v in product([f(0),f(1,2),f(1)],repeat=4):
        rows=(v[:2],v[2:]);out=scan(rows)
        for rule in RULES:equal(out[rule],select(rows,rule)[0],'synthetic_differential')
        count+=1
    ok('81_synthetic_tables_match_frozen_selector',count==81)
    return checks

