"""Read-only error accounting from cumulative requests; no submitted code is run."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import sys

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import executable_selector as selector


def need(value, label):
    if not value:
        raise ValueError(label)


def read(path):
    return json.loads(path.read_text())


def error_kind(result):
    if result['status'] == 'ok':
        return 'ok'
    need(result['status'] == 'code_error', 'unexpected_analysis_status')
    error = result['error']
    if error == "AttributeError: 'dict' object has no attribute 'states'":
        return 'dict_attribute_states'
    if error == "NameError: name 'next' is not defined":
        return 'unavailable_next'
    # Preserve an error category without displaying participant source or payload.
    return error.split(':', 1)[0]


def audit():
    data = read(H / 'data/crossing.json')
    paths = sorted((H / 'protocol').glob('requests-*.json'))
    requests = sorted([r for p in paths for r in read(p)], key=lambda r: r['call'])
    need([r['call'] for r in requests] == list(range(1, 81)), 'request_order')
    grouped = defaultdict(list)
    for r in requests:
        grouped[r['trial_id']].append(r)
    allocation = data['allocation']
    ids = [r['trial_id'] for r in allocation]
    need(len(ids) == len(set(ids)) == 32 and set(ids) == set(grouped) == set(data['trials']), 'trial_identity')
    rows = []
    for a in sorted(allocation, key=lambda x: x['order']):
        tid = a['trial_id']; trial = data['trials'][tid]; reqs = grouped[tid]
        final = reqs[-1]['payload']['analysis_records']
        need(len(final) == trial['result']['analysis_calls'], 'analysis_total:' + tid)
        for i, req in enumerate(reqs):
            prefix = req['payload']['analysis_records']
            need(prefix == final[:len(prefix)] and len(prefix) == i, 'cumulative_prefix:' + tid)
            need(req['payload']['remaining_analysis_calls'] == 3 - len(prefix), 'budget:' + tid)
        kinds = Counter(error_kind(item['result']) for item in final)
        failed = [(i + 1, error_kind(item['result'])) for i, item in enumerate(final) if item['result']['status'] != 'ok']
        parsed = selector.parse(trial['final_text']); sensitive = False
        if a['condition'] == 'executable_record':
            record, _ = selector.validate(parsed['record'], data['contexts'][a['case_id']])
            sensitive = not selector._diagnostics(record)['rules_choose_same_action']
        rows.append({'trial_id': tid, 'order': a['order'], 'family': a['family'], 'condition': a['condition'],
                     'analysis_attempts': len(final), 'analysis_ok': kinds['ok'], 'analysis_errors': len(failed),
                     'error_slots': [{'slot': slot, 'kind': kind} for slot, kind in failed],
                     'consumed_error_slots': len(failed), 'status': trial['result']['status'],
                     'native_label': trial['result']['label'], 'mandatory_rule_sensitive': sensitive})
    affected = [r for r in rows if r['analysis_errors']]
    kinds = Counter(e['kind'] for r in rows for e in r['error_slots'])
    need(sum(r['analysis_attempts'] for r in rows) == 48, 'common_attempts')
    need(sum(r['analysis_ok'] for r in rows) == 41 and len(affected) == 7, 'common_errors')
    need(kinds == {'dict_attribute_states': 5, 'unavailable_next': 2}, 'common_error_kinds')
    need(Counter(r['condition'] for r in affected) == {'optional_record': 5, 'executable_record': 2}, 'affected_conditions')
    need(all(r['analysis_attempts'] == 3 and r['analysis_ok'] == 2 and r['analysis_errors'] == 1 for r in affected), 'consumed_one_of_three')
    sensitive = [r for r in rows if r['mandatory_rule_sensitive']]
    need(len(sensitive) == 1 and sensitive[0] in affected, 'sensitive_trial_affected')
    transfer = []; transfer_paths = sorted((H.parent / 'legacy-replay/data/transfer/trials').glob('trial-*.json'))
    for p in transfer_paths:
        t = read(p); a = t['allocation']; analyses = t['analyses']
        transfer.append({'trial_file': p.name, 'family': a['family'], 'ordinal': a['ordinal'],
                         'analysis_attempts': len(analyses), 'analysis_ok': sum(x['status'] == 'ok' for x in analyses),
                         'analysis_errors': sum(x['status'] != 'ok' for x in analyses),
                         'error_kinds': dict(Counter(error_kind(x) for x in analyses if x['status'] != 'ok'))})
    need(len(transfer) == 48, 'transfer_trial_count')
    totals = {}
    for family in sorted({r['family'] for r in transfer}):
        subset = [r for r in transfer if r['family'] == family]
        totals[family] = {'trials': len(subset), 'zero_attempt_trials': sum(r['analysis_attempts'] == 0 for r in subset),
                          **{key: sum(r[key] for r in subset) for key in ('analysis_attempts', 'analysis_ok', 'analysis_errors')}}
    need(sorted((r['trials'], r['zero_attempt_trials'], r['analysis_attempts'], r['analysis_ok'], r['analysis_errors']) for r in totals.values()) == [(24, 0, 72, 67, 5), (24, 24, 0, 0, 0)], 'transfer_accounting')
    source_paths = paths + [H / 'data/crossing.json'] + transfer_paths
    return {'passed': True, 'scope': 'existing_records_error_accounting', 'common_menu': {
        'trials': 32, 'evaluated': sum(r['status'] == 'evaluated' for r in rows), 'analysis_attempts': 48,
        'analysis_ok': 41, 'analysis_errors': 7, 'affected_trials': 7, 'error_kinds': dict(kinds),
        'affected_by_condition': dict(Counter(r['condition'] for r in affected)), 'sensitive_trial_affected': sensitive[0]['trial_id'],
        'trials_detail': rows}, 'transfer': {'totals_by_family': totals, 'trials_detail': transfer},
        'source_sha256': {p.relative_to(H.parent).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},
        'causal_effect_on_actions_or_record_structure': 'unassessed', 'submitted_programs_executed': 0,
        'new_model_calls': 0, 'historical_records_modified': False}


if __name__ == '__main__':
    print(json.dumps(audit(), sort_keys=True))
