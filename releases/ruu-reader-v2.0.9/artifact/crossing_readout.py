"""Pure readout: action differences, P/L flips and unresolved contrasts are distinct."""
from collections import Counter


def _difference(a, b, labels):
    x, y = labels[a], labels[b]
    return {'action_changed': a != b, 'category_changed': x != y,
            'resolved_P_L_flip': x != y and {x, y} == {'P', 'L'},
            'involves_unresolved': 'U' in (x, y), 'categories': [x, y]}


def annotate(crossed, grade_map):
    if (crossed['case_id'], crossed['menu_sha256']) != (grade_map['case_id'], grade_map['menu_sha256']):
        raise ValueError('grade_map_identity')
    labels = grade_map['labels']
    if not isinstance(labels, list) or not labels or any(x not in ('P', 'L', 'U') for x in labels):
        raise ValueError('grade_map_labels')
    native = crossed['native_action_ids']
    for i in native + [c['action_id'] for c in crossed['observed'] + crossed['rule_family']]:
        if type(i) is not int or not 0 <= i < len(labels): raise ValueError('grade_map_coverage')
    observed = []
    for cell in crossed['observed']:
        i, j = cell['pool_repeat'] - 1, cell['rule_repeat'] - 1
        observed.append({**cell, 'label': labels[cell['action_id']],
                         'rule_change_from_own_native': _difference(native[i], cell['action_id'], labels),
                         'pool_change_from_rule_donor_native': _difference(native[j], cell['action_id'], labels)})
    family = []
    for i in (1, 2):
        cells = {c['rule']: c for c in crossed['rule_family'] if c['pool_repeat'] == i}
        family.append({'pool_repeat': i, **_difference(cells['uniform_mean']['action_id'],
                                                      cells['worst_case']['action_id'], labels)})
    return {'case_id': crossed['case_id'], 'menu_sha256': crossed['menu_sha256'],
            'observed': observed, 'family_within_pool_rule_contrasts': family,
            'unique_computations': crossed['unique_computations'],
            'any_observed_rule_action_change': any(c['rule_change_from_own_native']['action_changed'] for c in observed),
            'any_observed_rule_P_L_flip': any(c['rule_change_from_own_native']['resolved_P_L_flip'] for c in observed),
            'any_family_rule_action_change': any(c['action_changed'] for c in family),
            'any_family_rule_P_L_flip': any(c['resolved_P_L_flip'] for c in family),
            'scope': 'explicit surrogate contrasts; cells and reused labels are not independent samples'}


def population(planned_pair_ids, reports, missing_reasons):
    """No absent/unsupported pair is silently dropped or treated as a negative effect."""
    if len(set(planned_pair_ids)) != len(planned_pair_ids): raise ValueError('duplicate_pair')
    planned = set(planned_pair_ids)
    if set(reports) & set(missing_reasons) or set(reports) | set(missing_reasons) != planned:
        raise ValueError('pair_accounting')
    return {'fixed_pair_denominator': len(planned_pair_ids), 'crossable_pairs': len(reports),
            'missing': dict(Counter(missing_reasons.values())),
            'observed_rule_action_change_pairs': sum(r['any_observed_rule_action_change'] for r in reports.values()),
            'observed_rule_P_L_flip_pairs': sum(r['any_observed_rule_P_L_flip'] for r in reports.values()),
            'completion_free_cells_observed': sum(len(r['observed']) for r in reports.values()),
            'no_completed_pairs_means': 'not_assessed' if not reports else 'assessed_on_reported_subset'}
