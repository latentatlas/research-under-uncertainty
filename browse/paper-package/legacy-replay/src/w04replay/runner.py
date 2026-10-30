"""Fixed replay and reference comparison; expected outputs never choose actions."""
from collections import Counter
from copy import deepcopy
import math
from .records import canonical, digest, read, loads, write_new
from .snapshot_core import validate_packet, response_action, verdict, verify_bounds
from . import physics as W

PRESERVED = 'feasibility_preserved_by_witness'
LOST = 'feasibility_lost_by_certificate'
CASES = {'case-01', 'boundary-01', 'case-03', 'boundary-02'}


def require(value, label):
    if not value:
        raise ValueError(label)


class Comparison:
    def __init__(self):
        self.scalar_count = 0
        self.exact_count = 0
        self.numeric_nonexact = 0
        self.max_abs_error = 0.0
        self.max_action_distance = 0.0

    def compare(self, actual, expected, path, *, exact=False):
        if type(expected) is dict:
            require(type(actual) is dict and set(actual) == set(expected), path + ': keys')
            for key in expected:
                self.compare(actual[key], expected[key], path + '/' + key, exact=exact)
        elif type(expected) is list:
            require(type(actual) is list and len(actual) == len(expected), path + ': length')
            if path.endswith(('/action', '/first_action', '/applied_action')) and len(expected) == 2:
                distance = math.dist(actual, expected)
                self.max_action_distance = max(self.max_action_distance, distance)
                require(distance <= 1e-6, path + ': action tolerance')
            for index, value in enumerate(expected):
                self.compare(actual[index], value, path + '/' + str(index), exact=exact)
        else:
            self.scalar_count += 1
            if type(actual) is type(expected) and actual == expected:
                self.exact_count += 1
                return
            if not exact and type(expected) is float and type(actual) is float:
                require(math.isfinite(actual) and math.isfinite(expected), path + ': finite')
                delta = abs(actual - expected)
                self.max_abs_error = max(self.max_abs_error, delta)
                self.numeric_nonexact += 1
                require(math.isclose(actual, expected, rel_tol=1e-6, abs_tol=1e-6), path + ': numeric tolerance')
            else:
                raise ValueError(path + ': exact mismatch')


def inputs(root):
    cases = read(root / 'data/cases.json')
    trials = read(root / 'data/trials.json')
    comp = read(root / 'data/component_inputs.json')
    refs = read(root / 'data/references.json')
    require(set(cases) == CASES, 'case allowlist')
    require([t['ordinal'] for t in trials] == list(range(1, 9)), 'trial order')
    require(Counter((t['case_id'], t['repeat']) for t in trials) ==
            Counter((c, r) for c in CASES for r in (1, 2)), 'four cases by two repeats')
    for name, bundle in cases.items():
        require(bundle['case']['case_id'] == name, 'canonical case identity')
        validate_packet(bundle['packet'], bundle['case'])
        require(digest(bundle['world']) == bundle['world_sha256'], 'world identity')
    require(len({c['world_sha256'] for c in cases.values()}) == 2, 'two world configurations')
    for trial in trials:
        packet = deepcopy(trial['delivered_snapshot'])
        require(packet['case_id'] == trial['opaque_id'], 'masked delivery identity')
        packet['case_id'] = trial['case_id']
        require(canonical(packet) == canonical(cases[trial['case_id']]['packet']), 'canonical delivery equality')
        response_action({'action': trial['action']}, W)
    for name in CASES:
        pair = [t for t in trials if t['case_id'] == name]
        require(canonical(pair[0]['delivered_snapshot']) == canonical(pair[1]['delivered_snapshot']), 'repeat delivery equality')
        require(pair[0]['delivery_sha256'] == pair[1]['delivery_sha256'], 'repeat delivery hash')
    require(set(comp['values']) == set(comp['actions']) == {'2', '4', '6', '8'}, 'component trial identities')
    for ordinal, action in comp['actions'].items():
        require(action == trials[int(ordinal)-1]['action'], 'component action binding')
    require(comp['boundary01_history'] == cases['boundary-01']['packet']['history'], 'component history')
    require(len(refs['graded_cells']) == len(refs['computation']['cells']) == 91, 'reference cell count')
    require(len({(x['case'], x['id']) for x in refs['graded_cells']}) == 91, 'unique reference identities')
    return cases, trials, comp, refs


def negative_controls(cases, refs):
    checks = []
    def rejects(name, call):
        try:
            call()
        except (ValueError, TypeError):
            checks.append({'check': name, 'passed': True})
        else:
            raise ValueError('negative control accepted: ' + name)
    bundle = cases['boundary-01']
    packet = deepcopy(bundle['packet']); packet['case_id'] = 'wrong-case'
    rejects('wrong_case', lambda: validate_packet(packet, bundle['case']))
    changed = deepcopy(bundle['packet']); changed['history']['states'][-1][0] += .001
    rejects('changed_history', lambda: validate_packet(changed, bundle['case']))
    clock = deepcopy(bundle['packet']); clock['physical_step'] = True
    rejects('boolean_physical_clock', lambda: validate_packet(clock, bundle['case']))
    for label, action in [('boolean_action', [True, 0]), ('nonfinite_action', [float('nan'), 0]),
                          ('over_limit_action', [.61, 0])]:
        rejects(label, lambda a=action: response_action({'action': a}, W))
    rejects('extra_response_field', lambda: response_action({'action': [0, 0], 'private': 1}, W))
    rejects('contradictory_evidence', lambda: verdict(True, True))
    require(verdict(False, False) == 'unresolved', 'no evidence stays unresolved')
    checks.append({'check': 'no_evidence_is_not_false', 'passed': True})
    cert = next(deepcopy(g['after']['certificate']) for g in refs['pilot'].values()
                if g['after']['certificate'].get('method') == 'fixed_positive_projection'
                and g['after']['certificate'].get('certified'))
    require(verify_bounds(cert), 'reference certificate arithmetic')
    cert['bounds'][-1] += .01
    rejects('corrupt_certificate_bounds', lambda: verify_bounds(cert))
    rejects('duplicate_json_key', lambda: loads('{"a":1,"a":2}'))
    rejects('nonfinite_json', lambda: loads('{"a":NaN}'))
    return checks


def verify(root):
    cases, trials, comp, refs = inputs(root)
    controls = negative_controls(cases, refs)
    return {'passed': True, 'case_count': len(cases), 'trial_count': len(trials),
            'negative_controls': controls, 'physics_transitions': 0, 'candidate_evaluations': 0}


def reproduce(root, output):
    from .grading import grade
    from .components import compute
    cases, trials, comp, refs = inputs(root)
    checks = negative_controls(cases, refs)
    comparison = Comparison()
    pilot = {}
    pilot_steps = 0
    for trial in trials:
        ordinal = str(trial['ordinal'])
        actual = grade(cases[trial['case_id']], trial['action'])
        pilot[ordinal] = actual
        pilot_steps += actual['local_physics_steps']
        comparison.compare(actual, refs['pilot'][ordinal], 'pilot/' + ordinal, exact=True)
    write_new(output / 'PILOT.json', pilot)
    computed = compute(comp)
    write_new(output / 'COMPUTATION.json', computed)
    comparison.compare({k: v for k, v in computed.items() if k != 'checks'}, refs['computation'], 'computation')
    require(all(c['passed'] for c in computed['checks']), 'component internal checks')
    graded = []
    unique = {}
    component_steps = 0
    for cell, expected in zip(computed['cells'], refs['graded_cells']):
        for field in ('case', 'id', 'group', 'status'):
            require(cell[field] == expected[field], 'ordered cell identity/' + field)
        row = {k: cell[k] for k in ('case', 'id', 'group', 'status', 'action')}
        if cell['status'] == 'unresolved_numeric':
            require(cell['action'] is None and expected['score'] is None and expected['grade_path'] is None, 'unresolved is not failure')
            row.update(diagnostic_score=None, score=None, grade_id=None)
        else:
            key = digest([cell['case'], cell['action']])
            if key not in unique:
                result = grade(cases[cell['case']], cell['action'])
                unique[key] = result
                component_steps += result['local_physics_steps']
            result = unique[key]
            # Recompute first, then compare; the archived grade never sets the action or verdict.
            comparison.compare(result, refs['grade_references'][expected['grade_path']], 'grade/' + cell['id'], exact=True)
            diagnosis = result['diagnostic_score']
            score = 1 if diagnosis == PRESERVED else (0 if diagnosis == LOST else None)
            row.update(diagnostic_score=diagnosis, score=score, grade_id=key)
            require(diagnosis == expected['diagnostic_score'] and score == expected['score'], 'cell diagnosis')
        graded.append(row)
    write_new(output / 'COMPONENT-GRADES.json', unique)
    write_new(output / 'CELLS.json', graded)
    lookup = {(c['case'], c['id']): c for c in graded}
    tables = {
        'boundary-01': [[lookup['boundary-01', a + '-' + r]['score'] for r in ('R1', 'R2star')] for a in ('A1', 'A2')],
        'boundary-02': [[lookup['boundary-02', a + '-' + r]['score'] for r in ('R1', 'R2')] for a in ('A1', 'A2')],
    }
    require(tables == {'boundary-01': [[0, 1], [1, 1]], 'boundary-02': [[1, 0], [0, 0]]}, 'primary tables')
    losses = {}
    for group, total in [('single_scenario_omission', 66), ('parent_omission', 11)]:
        rows = [c for c in graded if c['group'] == group]
        require(len(rows) == total and all(r['score'] == 0 for r in rows), group)
        losses[group] = {'total': total, 'preserved': 0, 'certified_loss': total}
    summary = {
        'schema': 'world04-portable-replay-v1', 'passed': True,
        'pilot': {'total': 8, 'preserved': sum(g['diagnostic_score'] == PRESERVED for g in pilot.values()),
                  'certified_loss': sum(g['diagnostic_score'] == LOST for g in pilot.values())},
        'component_cells': {'planned': len(graded), 'computed': sum(c['status'] == 'computed' for c in graded),
                            'unresolved_numeric': sum(c['status'] == 'unresolved_numeric' for c in graded),
                            'unique_graded_actions': len(unique)},
        'tables': tables, 'omissions': losses,
        'usage': {'new_llm_requests': 0, 'new_llm_tokens': 0, 'parameter_refits': 0,
                  'candidate_step_evaluations': computed['counts']['candidate_step_evaluations'],
                  'optimizer_invocations': computed['counts']['optimizer_invocations'],
                  'pilot_local_physics_transitions': pilot_steps,
                  'component_local_physics_transitions': component_steps,
                  'total_local_physics_transitions': pilot_steps + component_steps,
                  'analyst_usage': 'not_measured_by_this_program'},
        'comparison': dict(vars(comparison)), 'negative_controls': checks,
        'component_internal_checks': len(computed['checks']),
        'limitations': ['same_algorithm_local_replay_not_independent_scientific_replication',
                        'selected_cases_not_population_or_difficulty_calibration',
                        'R2star_is_researcher_completed_selection_and_magnitude_can_change',
                        'sufficient_certificate_and_fixed_privileged_witness_not_complete_viability',
                        'historical_missing_usage_and_confirmatory_status_unchanged'],
    }
    require(summary['pilot'] == {'total': 8, 'preserved': 6, 'certified_loss': 2}, 'pilot totals')
    require(summary['component_cells'] == {'planned': 91, 'computed': 90, 'unresolved_numeric': 1, 'unique_graded_actions': 13}, 'component totals')
    require(component_steps == 617, 'historical component transition count')
    write_new(output / 'SUMMARY.json', summary)
    return summary
