"""Recompute twelve candidate plans and five selectors; no participant or physical grader.
Historical P/L labels are linked records, conditional on the stated numerical premises.
"""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import math
import sys

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H.parent / 'legacy-replay/src'))
from w04replay import components


def need(value, label):
    if not value:
        raise ValueError(label)


def close(a, b):
    return abs(a - b) <= 1e-8 * (1 + abs(b))


def run():
    inputs = H.parent / 'legacy-replay/data/component_inputs.json'
    source = H / 'source/pilot-sensitivity.private.json'
    data = json.loads(inputs.read_text()); saved = json.loads(source.read_text())
    vals = {int(k): deepcopy(v) for k, v in data['values'].items()}
    history = data['boundary01_history']; state = history['states'][-1]; n = len(history['actions'])
    need(n == 11, 'history_identity')
    pools = {'A1': [{**deepcopy(m), 'family': 't4', 'id': f't4-{i}', 'C': m['drift_coef']} for i, m in enumerate(vals[4]['models'][:8])],
             'A2': [{**deepcopy(m), 'family': 't6', 'id': f't6-{i}'} for i, m in enumerate(vals[6]['models'])]}
    components.calls = {'candidate_step_evaluations': 0, 'optimizer_invocations': 0, 'new_llm_requests': 0, 'parameter_refits': 0, 'physical_steps': 0}
    computed = {}; maximum_error = 0.0
    for pool, models in pools.items():
        for i, model in enumerate(models):
            plan = components.optimize([model], state, n, 1000)
            targets = plan['candidate_target_norms'][0]
            metrics = {'total_cost': plan['cost'], 'target_max': max(targets), 'target_mean_square': sum(x*x for x in targets)/len(targets),
                       'path_peak': plan['candidate_max_norms'][0], 'terminal_norm': targets[-1]}
            original = next(x for x in saved['records'] if x['pool'] == pool and x['candidate_index'] == i)
            need(original['candidate_id'] == model['id'], 'candidate_identity')
            for key, value in metrics.items():
                need(close(value, original['metrics'][key]), 'metric:' + pool + ':' + str(i) + ':' + key)
                maximum_error = max(maximum_error, abs(value - original['metrics'][key]))
            need(all(close(a, b) for a, b in zip(plan['first_action'], original['action'])), 'first_action')
            computed[pool, i] = {'metrics': metrics, 'action': plan['first_action'], 'archived_diagnosis': original['diagnosis']}
    selectors = []
    for ref in saved['selectors']:
        metric = ref['selector']
        indices = {pool: min(range(len(models)), key=lambda i: (computed[pool, i]['metrics'][metric], i)) for pool, models in pools.items()}
        labels = {pool: computed[pool, i]['archived_diagnosis'] for pool, i in indices.items()}
        native = data['actions']['6']; action = computed['A2', indices['A2']]['action']
        distance = math.dist(native, action)
        need(indices == ref['selected_indices'] and labels == ref['diagnoses'], 'selector:' + metric)
        need(distance <= 1e-6 and close(distance, ref['native_action_distance']), 'native_compatibility')
        selectors.append({'selector': metric, 'selected_indices': indices, 'native_action_distance': distance, 'archived_diagnoses': labels})
    need(len(computed) == 12 and len(selectors) == 5, 'plan_selector_counts')
    return {'passed': True, 'plans_recomputed': len(computed), 'selectors_recomputed': selectors, 'maximum_metric_abs_error': maximum_error,
            'numeric_tolerance': 'abs(a-b) <= 1e-8*(1+abs(b))', 'native_action_tolerance': 1e-6,
            'source_sha256': {p.relative_to(H.parent).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in (inputs, source, Path(components.__file__))},
            'original_grade_file_sha256': saved['grade_file_sha256'], 'work': components.calls,
            'historical_labels_recomputed': False, 'label_scope': 'archived labels; continuous numerical/runtime premises remain open',
            'participant_programs_executed': 0, 'new_model_calls': 0, 'independent_laboratory': False}


if __name__ == '__main__':
    print(json.dumps(run(), sort_keys=True))
