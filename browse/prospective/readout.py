"""Scalars from committed decisions; no model or physics execution."""
from collections import Counter
from common import MODELS
from protocol import get_bundle, action_copy

def summarize(rows,results):
    byid={x['role_id']:x for x in results};report={}
    for model in MODELS:
        rr=[r for r in rows if r['model']==model];science=[r for r in rr if r['role']!='control']
        counts={role:dict(Counter(byid[r['role_id']]['status'] for r in rr if r['role']==role)) for role in ('control','source','observer','target')}
        pairs=[];sources=[]
        for sr in [r for r in science if r['role']=='source']:
            s=byid[sr['role_id']];sources.append(s)
            for j in range(2):
                members=[r for r in science if r['unit_id']==sr['unit_id'] and r.get('target_index')==j]
                tr=next(r for r in members if r['role']=='target');t=byid[tr['role_id']]
                preds={r['condition']:byid[r['role_id']] for r in members if r['role']=='observer'}
                valid_target=t['status']=='completed';paired=valid_target and all(p['status'] in ('completed','protocol') for p in preds.values())
                correctness={c:(int(p.get('action_id')==t['action_id']) if p['status']=='completed' else 0) for c,p in preds.items()} if paired else None
                bounds=[-1,1]
                if paired:bounds=[correctness['with_record']-correctness['without_record']]*2
                # Tighten bounds when a target and just one observer are observed.
                elif valid_target:
                    c={arm:(int(p.get('action_id')==t['action_id']) if p['status']=='completed' else 0) for arm,p in preds.items() if p['status'] in ('completed','protocol')}
                    if 'with_record' in c:bounds=[c['with_record']-1,c['with_record']]
                    if 'without_record' in c:bounds=[-c['without_record'],1-c['without_record']]
                cp=action_copy(s,get_bundle(sr['history_id'])['targets'][j]) if s['status']=='completed' else None
                pairs.append({'history_id':sr['history_id'],'target_index':j,'target_valid':valid_target,'paired_evaluable':paired,
                    'both_predictions_protocol_valid':paired and all(p['status']=='completed' for p in preds.values()),
                    'correctness':correctness,'difference_bounds':bounds,'copy_legal':cp is not None,
                    'copy_correct':int(cp==t['action_id']) if cp is not None and valid_target else None,
                    'target_action_changed_from_source':t['action_id']!=s.get('action_id') if valid_target and s['status']=='completed' else None})
        clusters=[]
        for h in ('h01','h02','h03','h04'):
            pp=[p for p in pairs if p['history_id']==h]
            clusters.append({'history_id':h,'target_denominator':2,'evaluable_pairs':sum(p['paired_evaluable'] for p in pp),
                'difference_bounds':[sum(p['difference_bounds'][k] for p in pp)/2 for k in (0,1)]})
        valid=[s for s in sources if s['status']=='completed'];paired=[p for p in pairs if p['paired_evaluable']]
        report[model]={'allocated_source_units':4,'allocated_targets':8,'role_status_counts':counts,
            'role_started_count':sum(byid[r['role_id']].get('started',False) for r in rr),
            'paired_evaluable':len(paired),'both_predictions_protocol_valid_pairs':sum(p['both_predictions_protocol_valid'] for p in pairs),
            'primary_allocation_bounds':[sum(c['difference_bounds'][k] for c in clusters)/4 for k in (0,1)],
            'paired_descriptive_difference':sum(p['difference_bounds'][0] for p in paired)/len(paired) if paired else None,
            'arm_correct_counts':{c:sum(p['correctness'][c] for p in paired) for c in ('with_record','without_record')},
            'copy_correct':sum(p['copy_correct'] for p in pairs if p['copy_correct'] is not None),
            'copy_denominator':sum(p['copy_correct'] is not None for p in pairs),
            'changed_target_actions':sum(p['target_action_changed_from_source'] is True for p in pairs),
            'action_change_denominator':sum(p['target_action_changed_from_source'] is not None for p in pairs),
            'valid_source_records':len(valid),'record_proposal_agree':sum(s['record_proposal_agree'] for s in valid),
            'single_row_records':sum(s['record_diagnostics']['single_row'] for s in valid),
            'one_distinct_row_records':sum(s['record_diagnostics']['distinct_numeric_rows']==1 for s in valid),
            'duplicate_row_records':sum(s['record_diagnostics']['duplicate_rows']>0 for s in valid),
            'same_rule_records':sum(s['record_diagnostics']['rules_choose_same_action'] for s in valid),
            'clusters':clusters,'pairs':pairs,'empty_denominator_means':'unavailable, never success'}
    return {'by_profile':report,'pooled_primary':None,'model_ranking':None,
        'scope':'descriptive feasibility; paired allocation bounds are missing-data identification bounds, not confidence intervals',
        'full_task_success_measured':False,'causal_internal_reasoning_measured':False,'old_record_predictiveness_measured':False}
