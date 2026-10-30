"""Inspect existing B records and arithmetic controls, without scientific execution.

The action-copy construction depends only on a proposed menu index. It is a
counterexample to the sufficiency of matching, not a model trial or an account
of how participants produced their records. The positive control demonstrates
that the reader can detect a rule contrast when one is present.
"""
from pathlib import Path
import importlib.util
import json

H = Path(__file__).resolve().parent
MODELS = ('gpt-6-astra', 'gpt-6.1-sol')
NAMES = dict(zip(MODELS, ('Astra', 'Sol')))


def read(path):
    return json.loads(path.read_text())


def source_reader():
    spec = importlib.util.spec_from_file_location('contribution_source', H/'source_check.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic_record(source, table, proposal, rule):
    # Synthetic identities, distinct from every experimental history/menu.
    menu = list(range(len(table[0])))
    context = {'case_id':'constructed-arithmetic-control', 'menu':menu,
               'menu_sha256':source.digest(menu)}
    record = {'schema':'executable-decision-record-v1',
              'case_id':context['case_id'], 'menu_sha256':context['menu_sha256'],
              'loss_definition_id':'remaining_task_failure_forecast_v1',
              'candidate_losses':table, 'rule':rule}
    wire = json.dumps({'decision':{'action_id':proposal, 'record':record}})
    return source.derive_final(wire, 'B_required_model', context)


def controls(source):
    copies = []
    for n in (3, 13):
        for proposal in range(n):
            row = [0 if j == proposal else 1 for j in range(n)]
            for rule in source.RULES:
                result = synthetic_record(source, [row], proposal, rule)
                actions = result['record_diagnostics']['rule_actions']
                if not result['record_valid'] or not result['record_action_agreement']:
                    raise ValueError('action_copy_match')
                if set(actions.values()) != {proposal}:
                    raise ValueError('action_copy_rule_invariance')
                copies.append({'menu_size':n, 'proposal':proposal, 'declared_rule':rule,
                               'rule_actions':actions})
    positive = []
    for rule, proposal in (('uniform_mean', 0), ('worst_case', 1)):
        result = synthetic_record(source, [[0, 0.4], [0.7, 0.4]], proposal, rule)
        if result['record_diagnostics']['rule_actions'] != {'uniform_mean':0, 'worst_case':1}:
            raise ValueError('positive_control_sensitivity')
        if not result['record_action_agreement']:
            raise ValueError('positive_control_declared_selection')
        positive.append({'declared_rule':rule, 'proposal':proposal,
                         'rule_actions':result['record_diagnostics']['rule_actions']})
    return {'action_copy_cases':copies, 'rule_sensitive_cases':positive,
            'action_copy_inputs':'Menu size and proposed action index only; no history, world, label or participant trace.',
            'scope':'Constructed arithmetic controls, not new model trials, calibrated forecasts or evidence that participant records were produced by copying actions.'}


def compute():
    source = source_reader()
    validation = source.verify()
    trials = read(H/'trials.json')['trials']
    menus = read(H.parent/'data/crossing.json')
    decomposition = []
    for model in MODELS:
        selected = [t for t in trials if t['allocation']['model'] == model
                    and t['allocation']['arm'] == 'B_required_model']
        rows = []
        for trial in selected:
            a = trial['allocation']
            if trial['status'] != 'completed':
                raise ValueError('B_completed_source')
            result = source.derive_final((H/f"finals/trial-{a['order']:03d}.json").read_text(),
                                        a['arm'], menus['contexts'][a['case_id']])
            diag = result['record_diagnostics']
            rows.append({'order':a['order'], 'rows':diag['rows'],
                         'distinct_rows':diag['distinct_numeric_rows'],
                         'proposal_match':result['record_action_agreement'],
                         'same_action':diag['rules_choose_same_action']})
        single = [r for r in rows if r['rows'] == 1]
        multi = [r for r in rows if r['rows'] > 1]
        decomposition.append({'model':model, 'valid_records':len(rows),
                              'proposal_matches':sum(r['proposal_match'] for r in rows),
                              'single_row_forced_same_action':len(single),
                              'single_distinct_row_records':sum(r['distinct_rows'] == 1 for r in rows),
                              'multirow_records':len(multi),
                              'multirow_same_action_observed':sum(r['same_action'] for r in multi),
                              'multirow_proportion':None if not multi else sum(r['same_action'] for r in multi)/len(multi),
                              'per_record':rows})
    trial = next(t for t in trials if t['allocation']['order'] == 3)
    a = trial['allocation']
    if (a['model'], a['case_id'], a['repeat'], a['arm']) != ('gpt-6-astra', 'probe-03', 1, 'B_required_model'):
        raise ValueError('example_trial_identity')
    raw = (H/'finals/trial-003.json').read_text()
    result = source.derive_final(raw, a['arm'], menus['contexts'][a['case_id']])
    numeric = source.DECODER.decode(raw)['decision']['record']['candidate_losses']
    example = {'order':3, 'model':a['model'], 'case_id':a['case_id'], 'repeat':a['repeat'],
               'arm':a['arm'], 'table_rationals':[[str(v) for v in row] for row in numeric],
               'declared_rule':json.loads(raw)['decision']['record']['rule'],
               'proposal':result['proposed_action_id'], 'rule_actions':result['record_diagnostics']['rule_actions'],
               'executed_action':result['executed_action_id'],
               'label_from_bound_menu':menus['labelmaps'][a['case_id']]['labels'][result['executed_action_id']]}
    return {'schema':'record-contribution-checks-v1',
            'source_validation':{k:validation[k] for k in ('final_responses_reparsed','numeric_tables_recomputed','menu_label_bindings_verified')},
            'B_structure_by_profile':decomposition, 'real_record_example':example,
            'arithmetic_controls':controls(source),
            'limits':['No pooled primary inference or profile ranking.',
                      'Single-row invariance is forced by the rule definitions; multirow invariance is checked from values.',
                      'Proposal correspondence does not identify the record-generation process or internal causation.',
                      'Labels are bound historical census lookups, not fresh physics or full task success.']}


def render_tables(report):
    rows = []
    for x in report['B_structure_by_profile']:
        ratio = '--' if not x['multirow_records'] else f"{x['multirow_same_action_observed']}/{x['multirow_records']}"
        rows.append(f"{NAMES[x['model']]} & {x['proposal_matches']}/{x['valid_records']} & "
                    f"{x['single_row_forced_same_action']} & {x['multirow_records']} & {ratio}\\\\")
    decomposition = (r'''% Generated from the preserved minimal finals by contribution_checks.py.
\begin{table}[htbp]
\centering\small
\begin{tabular}{lrrrr}\toprule
Profile & Proposal matches & One row & Multiple rows & Multirow same action\\\midrule
''' + '\n'.join(rows) + r'''
\bottomrule\end{tabular}
\caption{B records, separated by profile. One-row mean/worst-case equality is
forced by the contract. For multirow records, equality is an observed property
of the archived values. Astra has no multirow denominator, so its dash is
undefined, not a success. Sol's two multirow records have three and four
distinct rows, respectively.}
\label{tab:B-structure}
\end{table}
''')
    example = report['real_record_example']
    # Keep the displayed decimals exact, not a rounded summary of a table.
    if example['table_rationals'] != [['7/20','3/10','1/4']]:
        raise ValueError('example_numeric_values')
    if example['declared_rule'] != 'uniform_mean' or example['proposal'] != 2 or example['rule_actions'] != {'uniform_mean':2,'worst_case':2} or example['label_from_bound_menu'] != 'P':
        raise ValueError('example_derived_values')
    real = r'''% Exact numeric values from finals/trial-003.json; no rounding.
\begin{table}[htbp]
\centering\small
\begin{tabular}{lrrr}\toprule
Archived candidate-loss row & Menu action 0 & Menu action 1 & Menu action 2\\\midrule
Only row & 0.35 & 0.30 & 0.25\\\bottomrule
\end{tabular}
\caption{A real B record: Astra, route history \texttt{probe-03}, repeat 1,
trial 3. The declared mean rule selects action 2, as does worst case.
The model proposed action 2 and B executed that proposal. Its bound menu label
is P. The numbers are uncalibrated forecasts; their ordering and the matching
proposal are reproducible, but their semantic adequacy or causal role is not
established. Exact final JSON and identity bindings are in the bundle.}
\label{tab:real-record}
\end{table}
'''
    return {'table-b-structure.tex':decomposition, 'table-real-record.tex':real}


def verify():
    report = compute()
    if report != read(H/'contribution-checks.json'):
        raise ValueError('contribution_source_mismatch')
    for name, text in render_tables(report).items():
        if (H.parents[1]/'paper'/name).read_text() != text:
            raise ValueError('contribution_table_mismatch:'+name)
    return {'passed':True, 'B_profiles':2, 'B_records':16,
            'source_tables':report['source_validation']['numeric_tables_recomputed'],
            'source_finals_and_labels':report['source_validation']['final_responses_reparsed'],
            'action_copy_control_cases':len(report['arithmetic_controls']['action_copy_cases']),
            'rule_sensitive_control_cases':len(report['arithmetic_controls']['rule_sensitive_cases']),
            'generated_tables':2, 'new_model_calls':0, 'new_physics_runs':0,
            'new_scientific_samples':0,
            'scope':'Existing sources plus constructed arithmetic controls; no predictive-utility or internal-faithfulness measurement.'}


if __name__ == '__main__':
    print(json.dumps(verify(), sort_keys=True))
