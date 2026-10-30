"""Derive descriptive follow-up breakdowns and verify manuscript tables.

Only existing minimal finals, allocation and bound menu labels are read.
No provider, participant program, physics or new sample is executed.
"""
from pathlib import Path
import importlib.util
import json
from collections import Counter

H = Path(__file__).resolve().parent
MODELS = ('gpt-6-astra', 'gpt-6.1-sol')
NAMES = dict(zip(MODELS, ('Astra', 'Sol')))
ARMS = ('A_optional_model', 'B_required_model', 'C_required_executor')
# Fixed history-family identities disclosed in the common-menu protocol appendix.
FAMILIES = {'probe-01':'continuous','probe-02':'continuous',
            'probe-03':'route','probe-04':'route'}

def read(path):
    return json.loads(path.read_text())

def compute():
    spec = importlib.util.spec_from_file_location('followup_source_check', H/'source_check.py')
    source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    validation = source.verify()
    trials = read(H/'trials.json')['trials']
    menus = read(H.parent/'data/crossing.json')
    contexts, labels = menus['contexts'], menus['labelmaps']
    assert set(contexts)==set(FAMILIES)
    assert all(len(contexts[c]['menu'])==(13 if f=='continuous' else 3)
               for c,f in FAMILIES.items())
    family_counts, history_counts, transitions, sensitive = [], [], [], []
    for model in MODELS:
        rows=[t for t in trials if t['allocation']['model']==model]
        assert len(rows)==24
        for family in ('continuous','route'):
            part=[t for t in rows if FAMILIES[t['allocation']['case_id']]==family]
            counts=Counter(t['label'] for t in part if t['status']=='completed')
            family_counts.append({'model':model,'family':family,'assigned':len(part),
                'completed':sum(counts.values()),
                'technical':sum(t['status']=='technical' for t in part),
                **{label:counts[label] for label in ('P','L','U')}})
        for case in FAMILIES:
            arms={}
            for arm in ARMS:
                part=[t for t in rows if t['allocation']['case_id']==case and t['allocation']['arm']==arm]
                assert len(part)==2
                counts=Counter(t['label'] for t in part if t['status']=='completed')
                arms[arm]={'assigned':2,'completed':sum(counts.values()),
                    'technical':sum(t['status']=='technical' for t in part),
                    **{label:counts[label] for label in ('P','L','U')}}
            history_counts.append({'model':model,'case_id':case,'family':FAMILIES[case],'arms':arms})
        blocks={}
        for trial in rows:
            a=trial['allocation']; key=(a['case_id'],a['repeat'])
            block=blocks.setdefault(key,{})
            assert a['arm'] not in block
            block[a['arm']]=trial
        assert len(blocks)==8 and all(set(b)==set(ARMS) for b in blocks.values())
        for left,right in ((ARMS[0],ARMS[1]),(ARMS[1],ARMS[2])):
            count=Counter(); missing=0
            for block in blocks.values():
                a,b=block[left],block[right]
                assert a['allocation']['block_id']==b['allocation']['block_id']
                if a['status']!='completed' or b['status']!='completed':
                    missing+=1;continue
                assert a['label'] in ('P','L') and b['label'] in ('P','L')
                count[a['label']+'->'+b['label']]+=1
            transitions.append({'model':model,'left':left,'right':right,'planned':8,
                'observed':sum(count.values()),'technical_missing':missing,
                'transitions':{k:count[k] for k in ('P->P','L->L','L->P','P->L')},
                'net_P':count['L->P']-count['P->L']})
        for trial in rows:
            if trial['status']!='completed':continue
            a=trial['allocation']
            computed=source.derive_final((H/f"finals/trial-{a['order']:03d}.json").read_text(),
                                        a['arm'],contexts[a['case_id']])
            d=computed['record_diagnostics']
            if d and not d['rules_choose_same_action']:
                actions=d['rule_actions']
                sensitive.append({'model':model,'case_id':a['case_id'],'repeat':a['repeat'],
                    'arm':a['arm'],'order':a['order'],'actions':actions,
                    'labels':{rule:labels[a['case_id']]['labels'][action] for rule,action in actions.items()}})
    return {'schema':'followup-descriptive-breakdown-v1',
        'source_validation':{k:validation[k] for k in ('final_responses_reparsed','numeric_tables_recomputed','menu_label_bindings_verified')},
        'family_mapping':FAMILIES,'family_counts':family_counts,
        'history_counts':history_counts,'paired_transitions':transitions,
        'rule_sensitive_records':sensitive,
        'menu_outcome_options':{case:dict(Counter(labels[case]['labels'])) for case in FAMILIES},
        'scope':'Purposeful contexts and repeats; separate model strata. Labels are looked up in the existing bound menu census, not physically regraded. No new live counterfactual, population effect or full-task-success measurement.'}

def render_tables(r):
    def table(columns,header,rows,caption,label):
        return ('% Generated from identity-bound existing follow-up sources.\n'
            '\\begin{table}[htbp]\n\\centering\\small\n'
            '\\begin{tabular}{'+columns+'}\\toprule\n'+header+'\\\\\\midrule\n'
            +'\n'.join(' & '.join(row)+'\\\\' for row in rows)
            +'\n\\bottomrule\n\\end{tabular}\n\\caption{'+caption+'}\n'
            '\\label{'+label+'}\n\\end{table}\n')
    out={}
    rows=[]
    for x in r['family_counts']:
        rows.append([NAMES[x['model']],x['family'].capitalize(),str(x['assigned']),
            str(x['completed']),str(x['technical']),f"{x['P']}/{x['L']}/{x['U']}"])
    out['table-followup-families.tex']=table('llrrrr','Profile & Family & Assigned & Done & Tech. & P/L/U',rows,
        'Follow-up outcomes by family, separately within each profile. Each family has two purposeful histories and two repeats per arm. Done denotes a completed decision, not full task success. P/L labels in the continuous family retain the numerical/runtime premises.','tab:followup-families')
    rows=[]
    for x in r['paired_transitions']:
        t=x['transitions'];contrast=x['right'][0]+'--'+x['left'][0]
        rows.append([NAMES[x['model']],contrast,f"{x['observed']}/{x['planned']}",str(x['technical_missing']),
            str(t['L->P']),str(t['P->L']),str(t['P->P']+t['L->L']),f"{x['net_P']:+d}"])
    out['table-followup-transitions.tex']=table('llrrrrrr',r'Profile & Contrast & Pairs & Missing & L$\to$P & P$\to$L & Same & Net P',rows,
        'Descriptive paired transitions run from A to B for B--A, and from B to C for C--B. Pairs are observed/planned; Missing counts technical missing pairs; Same includes P-to-P and L-to-L. Dividing Net P by observed pairs recovers the reported paired difference. No pooled estimate or population inference. C--B is the total condition contrast, not an isolated executor effect on the same fixed record.','tab:followup-pairs')
    rows=[]
    for x in r['rule_sensitive_records']:
        rows.append([NAMES[x['model']],x['case_id'],str(x['repeat']),x['arm'][0],
            f"{x['actions']['uniform_mean']} ({x['labels']['uniform_mean']})",
            f"{x['actions']['worst_case']} ({x['labels']['worst_case']})"])
    out['table-followup-rule-examples.tex']=table('llrlll','Profile & History & Repeat & Arm & Mean & Worst case',rows,
        'The two rule-sensitive follow-up records. Entries give zero-based menu index and bound label. The action changes but the label does not; these are per-record calculations on existing menus, not live crossed decisions. Continuous labels remain conditional.','tab:followup-rule-examples')
    rows=[]
    for x in r['history_counts']:
        row=[NAMES[x['model']],x['case_id'],x['family'].capitalize()]
        for arm in ARMS:
            v=x['arms'][arm];row.append(f"{v['P']}/{v['L']}/{v['technical']}")
        rows.append(row)
    out['table-followup-histories.tex']=table('llllll','Profile & History & Family & A: P/L/T & B: P/L/T & C: P/L/T',rows,
        'All follow-up history/arm outcomes; T denotes technical loss with no scientific label. Every cell has two planned assignments. All completed labels are P or L. Repeated contexts are not independent draws of new worlds; P is continuation feasibility, not measured full-task completion.','tab:followup-histories')
    return out

def verify():
    report=compute()
    if report!=read(H/'breakdown.json'):
        raise ValueError('derived_breakdown_mismatch')
    paper=H.parents[1]/'paper'
    for name,text in render_tables(report).items():
        if (paper/name).read_text()!=text:
            raise ValueError('manuscript_table_mismatch:'+name)
    return {'passed':True,'family_rows':len(report['family_counts']),
        'history_rows':len(report['history_counts']),
        'paired_transition_rows':len(report['paired_transitions']),
        'rule_sensitive_examples':len(report['rule_sensitive_records']),
        'manuscript_tables_verified':4,'new_model_calls':0,'new_physics_runs':0,
        'new_samples':0,'scope':report['scope']}

if __name__=='__main__':
    print(json.dumps(verify(),sort_keys=True))
