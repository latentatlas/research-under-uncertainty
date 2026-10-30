"""Scalar source checks for the interpretation revision. No collector imports."""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json

H = Path(__file__).resolve().parents[1]

def read(p):
    return json.loads(p.read_text())

def prospective_reporting(pairs, supplement):
    """Post hoc description of fixed assignments; no model or physics execution."""
    packets = {h:read(supplement/'packets'/f'{h}.json') for h in ['h01','h02','h03','h04']}
    design = []
    for h, packet in packets.items():
        source = packet['source']
        assert source['family'] == ('continuous' if h in ['h01','h02'] else 'route')
        assert len(packet['targets']) == 2
        branch_actions = []
        for target in packet['targets']:
            assert target['family'] == source['family']
            assert target['physical_step'] == source['physical_step'] + 1
            assert target['history']['actions'][:-1] == source['history']['actions']
            assert target['history']['states'][:-1] == source['history']['states']
            assert len(target['history']['states']) == len(source['history']['states']) + 1
            assert target['action_menu'] == source['action_menu']
            branch_actions.append(target['history']['actions'][-1])
            if source['family'] == 'route':
                k = branch_actions[-1][0]
                assert target['history']['states'][-1][0] - source['history']['states'][-1][0] == source['task']['advance_by_action'][k]
        step = 6 if source['family'] == 'continuous' else 4
        actions = [[0.6,0.0],[-0.6,0.0]] if step == 6 else [[0,0],[2,0]]
        assert source['physical_step'] == step and branch_actions == actions
        design.append({'history_id':h,'family':source['family'],'source_step':step,'target_step':step+1,
                       'source_menu_size':len(source['action_menu']),'branch_actions':branch_actions,
                       'new_transition_observations_per_target':1})
    histories, families = [], []
    for model in ['gpt-6-astra','gpt-6.1-sol']:
        for h in packets:
            subset = [p for p in pairs if p['model']==model and p['history_id']==h]
            assert len(subset)==2
            with_record = sum(p['category'] in ['both_correct','only_with_record'] for p in subset)
            without = sum(p['category'] in ['both_correct','only_without_record'] for p in subset)
            histories.append({'model':model,'history_id':h,'family':packets[h]['source']['family'],
                              'targets':2,'with_record_correct':with_record,'without_record_correct':without,
                              'net_correct':with_record-without})
        for family in ['continuous','route']:
            rows = [h for h in histories if h['model']==model and h['family']==family]
            assert len(rows)==2
            families.append({'model':model,'family':family,'histories':2,'targets':4,
                             **{k:sum(h[k] for h in rows) for k in ['with_record_correct','without_record_correct','net_correct']}})
    provenance = read(H/'artifact/prospective-design/SOURCE-PROVENANCE.json')
    for name, digest in provenance['original_file_sha256'].items():
        assert hashlib.sha256((H/'artifact/prospective-design'/name).read_bytes()).hexdigest()==digest
    generation = read(H/'artifact/prospective-design/CASE-GENERATION.json')
    assert generation['generated_before_model_outputs'] and generation['purposeful_feasibility_sample_not_population']
    assert generation['histories']==4 and generation['packets']==12 and generation['operator_reference_viable_states']==12
    return {'analysis_timing':'post hoc descriptive reporting; original primary aggregate retained',
            'family_correctness':families,'history_correctness':histories,'branch_design':design,
            'generation_record':generation,'generation_reexecuted':False}

def derive(supplement):
    binding = read(H/'PROSPECTIVE-BINDING.json')
    assert hashlib.sha256((supplement/'MANIFEST.json').read_bytes()).hexdigest() == binding['manifest_sha256']
    allocation = read(supplement/'ALLOCATION.json')['rows']
    byid = {r['role_id']: r for r in allocation}
    assert len(byid) == len(allocation) == 64
    decisions, origins = {}, {}
    for segment in read(supplement/'INDEX.json')['segments']:
        assert segment['mock_only'] is False
        for role in segment['roles']:
            rid = role['role_id']
            if role['status'] != 'completed' or byid[rid]['role'] == 'control':
                continue
            assert rid not in decisions, 'completed scientific role repeated'
            req = role['requests'][-1]
            assert req['receipted'] and not req['technical_faults']
            path = supplement/req['path']/'response.json'
            decision = read(path)['decision']
            row = byid[rid]
            packet = read(supplement/'packets'/f"{row['history_id']}.json")
            case = packet['source'] if row['role'] == 'source' else packet['targets'][row['target_index']]
            assert decision['case_id'] == row['case_id'] == case['case_id']
            assert decision['action_id'] in case['action_ids']
            decisions[rid] = decision
            origins[rid] = {'path':path.relative_to(supplement).as_posix(),
                            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
    assert len(decisions) == 56
    counts = {m:Counter({k:0 for k in ['both_correct','only_with_record','only_without_record','both_wrong']})
              for m in ['gpt-6-astra','gpt-6.1-sol']}
    pairs = []
    for target in [r for r in allocation if r['role'] == 'target']:
        arms = {r['condition']:r for r in allocation if r['role']=='observer'
                and r['unit_id']==target['unit_id'] and r['target_index']==target['target_index']}
        assert set(arms) == {'with_record','without_record'}
        target_action = decisions[target['role_id']]['action_id']
        right = {arm:decisions[r['role_id']]['action_id']==target_action for arm,r in arms.items()}
        category = {(True,True):'both_correct',(True,False):'only_with_record',
                    (False,True):'only_without_record',(False,False):'both_wrong'}[tuple(right[a] for a in ['with_record','without_record'])]
        counts[target['model']][category] += 1
        pairs.append({'target_role':target['role_id'],'model':target['model'],
                      'history_id':target['history_id'],'category':category})
    assert len(pairs)==16 and all(sum(c.values())==8 for c in counts.values())
    structures = []
    for row in [r for r in allocation if r['role']=='source']:
        record = decisions[row['role_id']]['record']
        rows = record['table']['candidate_losses']
        prose = ['assumptions','decision_criterion','expected_observation','uncertainty']
        assert all(isinstance(record[k],str) and record[k].strip() for k in prose)
        structures.append({'role':row['role_id'],'row_count':len(rows),
                           'distinct_rows':len({tuple(r) for r in rows}),'four_prose_fields_present':True})
    numerical = read(H/'artifact/source/pilot-sensitivity.private.json')['records']
    a2 = [r for r in numerical if r['pool']=='A2']
    assert len(a2)==4
    metrics = ['total_cost','target_max','target_mean_square','path_peak','terminal_norm']
    dominance = {}
    for metric in metrics:
        best = min(a2,key=lambda r:r['metrics'][metric])
        others = [r for r in a2 if r is not best]
        assert best['candidate_index']==2 and all(best['metrics'][metric]<r['metrics'][metric] for r in others)
        dominance[metric] = {'best_plan_index':2,'strict_comparisons':len(others)}
    def final_required(name):
        variants=read(supplement/'schemas'/name)['properties']['decision']['anyOf']
        finals=[v['required'] for v in variants if 'action_id' in v['properties']]
        assert len(finals)==1
        return finals[0]
    source_req=final_required('source.json')
    target_req=final_required('target.json')
    assert set(source_req)=={'case_id','action_id','record'} and set(target_req)=={'case_id','action_id'}
    return {'passed':True,'paired_correctness':counts,'pairs':pairs,
            'prospective_reporting':prospective_reporting(pairs,supplement),
            'A2_dominance':dominance,'source_structure':structures,
            'source_final_required':source_req,'target_final_required':target_req,
            'terminal_source_files':origins,'prose_semantic_value_evaluated':False,
            'protocol_change_effect_isolated':False,'same_input_target_variability_evaluated':False,
            'new_model_calls':0,'participant_programs_executed':0,'new_physics_runs':0}

def table(counts):
    rows=[]
    for model,label in [('gpt-6-astra','Astra'),('gpt-6.1-sol','Sol')]:
        c=counts[model]
        rows.append(label+' & '+' & '.join(str(c[k]) for k in ['both_correct','only_with_record','only_without_record','both_wrong'])+r'\\')
    return r'''\begin{table}[htbp]
\centering\small
\begin{tabular}{lrrrr}\toprule
Profile & Both correct & Record only & No-record only & Both wrong\\\midrule
'''+ '\n'.join(rows)+r'''
\bottomrule\end{tabular}
\caption{Joint top-1 prediction correctness for the combined panel, eight
targets per profile. Record only and No-record only identify which observer
is correct on the same target. Each cell uses one generation per role;
the counts describe paired outcomes, not case-level causal effects.}
\label{tab:prospective-paired}
\end{table}
'''

def reporting_tables(report):
    labels={'gpt-6-astra':'Astra','gpt-6.1-sol':'Sol','continuous':'Continuous','route':'Route'}
    def signed(n):return f'{n:+d}' if n else '0'
    rows=[f"{labels[r['model']]} & {labels[r['family']]} & {r['with_record_correct']}/4 & {r['without_record_correct']}/4 & ${signed(r['net_correct'])}$\\\\"
          for r in report['family_correctness']]
    families=r'''\begin{table}[htbp]
\centering\small
\begin{tabular}{llrrr}\toprule
Profile & Family & With record & Without record & Net correct\\\midrule
'''+ '\n'.join(rows)+r'''
\bottomrule\end{tabular}
\caption{Post hoc descriptive family breakdown of the combined prospective
panel. Each family has two purposeful histories with two linked targets each.
Net correct is the count with minus without the record. The prespecified
per-profile aggregate remains primary; these four-target contrasts do not
estimate family-level causal effects.}
\label{tab:prospective-families}
\end{table}
'''
    rows=[f"{labels[r['model']]} & {r['history_id']} & {labels[r['family']]} & {r['with_record_correct']}/2 & {r['without_record_correct']}/2 & ${signed(r['net_correct'])}$\\\\"
          for r in report['history_correctness']]
    histories=r'''\begin{table}[htbp]
\centering\small
\begin{tabular}{lllrrr}\toprule
Profile & History & Family & With record & Without record & Net correct\\\midrule
'''+ '\n'.join(rows)+r'''
\bottomrule\end{tabular}
\caption{Post hoc breakdown by the eight source-history/profile units.
Each row contains its two linked target branches. Sol h04 includes the
separately completed final target; the original fifteen-target panel remains
in Table~\ref{tab:prospective}. Histories are not repeated independent draws.}
\label{tab:prospective-histories}
\end{table}
'''
    branches=r'''\begin{table}[htbp]
\centering\small
\begin{tabular}{llcl}\toprule
Histories & Family & Source $\to$ target step & Two separate branch actions\\\midrule
h01, h02 & Continuous & $6\to7$ & $(0.6,0)$; $(-0.6,0)$\\
h03, h04 & Route & $4\to5$ & $(0,0)$; $(2,0)$: advance 1; 3 nodes\\
\bottomrule\end{tabular}
\caption{Fixed source--target construction. Step counts completed transitions.
Each target preserves the entire source history and adds one transition and
its observation under the indicated exogenous action. The two branches are
alternatives from the same source, not consecutive transitions. Branch actions
were fixed before source-model outputs and need not equal the source proposal.}
\label{tab:prospective-branches}
\end{table}
'''
    return {'table-prospective-families.tex':families,'table-prospective-histories.tex':histories,
            'table-prospective-branches.tex':branches}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--prospective-dir',type=Path,required=True)
    p.add_argument('--emit-table',action='store_true');args=p.parse_args()
    report=derive(args.prospective_dir.resolve());latex=table(report['paired_correctness'])
    if args.emit_table:
        print(latex,end='')
    else:
        assert (H/'paper/table-prospective-paired.tex').read_text()==latex,'paired table differs from source'
        for name, text in reporting_tables(report['prospective_reporting']).items():
            assert (H/'paper'/name).read_text()==text, 'reporting table differs from source: '+name
        print(json.dumps(report,sort_keys=True))
