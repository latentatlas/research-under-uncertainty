"""Offline executable numeric decision contract. Standard library; no provider or physics.

Numeric JSON lexemes are exact decimal rationals. A table is a multiset of
uncalibrated failure forecasts, not verified hypotheses or latent reasoning.
"""
from copy import deepcopy
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import json

SCHEMA = 'executable-decision-record-v1'
LOSS = 'remaining_task_failure_forecast_v1'
RULES = ('uniform_mean', 'worst_case')
MAX_BYTES = 262144


class ContractError(ValueError):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _number(text):
    if len(text) > 80:
        raise ContractError('numeric_lexeme_limit')
    try:
        dec = Decimal(text)
    except InvalidOperation:
        raise ContractError('invalid_number') from None
    if not dec.is_finite() or abs(dec.as_tuple().exponent) > 100:
        raise ContractError('numeric_exponent_or_finiteness')
    return Fraction(dec)


def _pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ContractError('duplicate_key')
        out[key] = value
    return out


def _constant(_):
    raise ContractError('nonfinite_number')


def parse(text):
    if type(text) is not str or len(text.encode()) > MAX_BYTES:
        raise ContractError('submission_size_or_type')
    try:
        return json.loads(text, parse_int=_number, parse_float=_number,
                          parse_constant=_constant, object_pairs_hook=_pairs)
    except (json.JSONDecodeError, RecursionError, UnicodeError):
        raise ContractError('invalid_json') from None


def check_context(context):
    if type(context) is not dict or set(context) != {'case_id', 'menu', 'menu_sha256'}:
        raise ContractError('context_schema')
    menu = context['menu']
    if type(context['case_id']) is not str or type(menu) is not list or not menu:
        raise ContractError('context_identity')
    try:
        actual = digest(menu)
    except (ValueError, TypeError):
        raise ContractError('context_menu') from None
    if actual != context['menu_sha256']:
        raise ContractError('context_menu_binding')
    return len(menu)


def validate(record, context):
    n = check_context(context)
    fields = {'schema', 'case_id', 'menu_sha256', 'loss_definition_id', 'candidate_losses', 'rule'}
    if type(record) is not dict or set(record) != fields:
        raise ContractError('record_fields')
    if record['schema'] != SCHEMA or record['loss_definition_id'] != LOSS:
        raise ContractError('record_version_or_loss')
    if record['case_id'] != context['case_id'] or record['menu_sha256'] != context['menu_sha256']:
        raise ContractError('record_identity')
    if record['rule'] not in RULES:
        raise ContractError('unsupported_rule')
    rows = record['candidate_losses']
    if type(rows) is not list or not 1 <= len(rows) <= 128:
        raise ContractError('row_count')
    if any(type(row) is not list or len(row) != n for row in rows):
        raise ContractError('rectangular_losses')
    if any(type(x) is not Fraction or not 0 <= x <= 1 for row in rows for x in row):
        raise ContractError('loss_range_or_type')
    # Immutable internal rows prevent a caller from changing the decision after validation.
    return tuple(tuple(row) for row in rows), record['rule']


def select(rows, rule):
    if rule not in RULES:
        raise ContractError('unsupported_rule')
    n = len(rows[0])
    if rule == 'uniform_mean':
        scores = tuple(sum((row[j] for row in rows), Fraction()) / len(rows) for j in range(n))
    else:
        scores = tuple(max(row[j] for row in rows) for j in range(n))
    index = min(range(n), key=lambda j: (scores[j], j))
    return index, scores


def _diagnostics(rows):
    choices = {rule: select(rows, rule)[0] for rule in RULES}
    return {'rows': len(rows), 'distinct_numeric_rows': len(set(rows)),
            'duplicate_rows': len(rows) - len(set(rows)), 'single_row': len(rows) == 1,
            'distinct_argmin_sets': len({tuple(j for j, x in enumerate(row) if x == min(row)) for row in rows}),
            'rules_choose_same_action': len(set(choices.values())) == 1,
            'rule_actions': choices, 'hypothesis_semantics_verified': False}


def _selection(record, context):
    rows, rule = validate(record, context)
    index, scores = select(rows, rule)
    canonical = {**{k: record[k] for k in ('schema', 'case_id', 'menu_sha256', 'loss_definition_id', 'rule')},
                 'candidate_losses': [[str(x) for x in row] for row in rows]}
    return {'case_id': context['case_id'], 'menu_sha256': context['menu_sha256'],
            'record_sha256': digest(canonical), 'rule': rule, 'action_id': index,
            'requested_action': deepcopy(context['menu'][index]),
            'scores_exact': [str(s) for s in scores], 'diagnostics': _diagnostics(rows),
            'researcher_completion_used': False}


def select_text(text, context):
    out = _selection(parse(text), context)
    out['raw_submission_sha256'] = hashlib.sha256(text.encode()).hexdigest()
    return out


def _index(value, n):
    if type(value) is not Fraction or value.denominator != 1 or not 0 <= value < n:
        raise ContractError('action_id')
    return int(value)


def consume_final(text, condition, context, sink):
    """Validate before a single sink call. Caller supplies only a local test sink here.

    The required arm's executed index comes from the record. The optional arm
    executes its independently supplied legal index even if its record is absent
    or invalid. A malformed JSON document/illegal final action never reaches sink.
    """
    n = check_context(context)
    payload = parse(text)
    if type(payload) is not dict:
        raise ContractError('final_fields')
    record_result = None
    if condition == 'executable_record':
        if set(payload) != {'record'}:
            raise ContractError('required_final_fields')
        record_result = _selection(payload['record'], context)
        index = record_result['action_id']
        instrumentation = 'executed_record_by_construction'
    elif condition == 'optional_record':
        if set(payload) not in ({'action_id'}, {'action_id', 'record'}):
            raise ContractError('optional_final_fields')
        index = _index(payload['action_id'], n)
        instrumentation = 'no_record'
        if 'record' in payload:
            try:
                record_result = _selection(payload['record'], context)
                instrumentation = ('supported_observational_record' if index == record_result['action_id']
                                   else 'record_action_mismatch')
            except ContractError as error:
                instrumentation = 'unsupported_record:' + error.code
    else:
        raise ContractError('condition')
    requested = deepcopy(context['menu'][index])
    sink_receipt = sink(deepcopy(requested))
    return {'condition': condition, 'case_id': context['case_id'], 'menu_sha256': context['menu_sha256'],
            'action_id': index, 'requested_action': requested, 'instrumentation': instrumentation,
            'record': record_result, 'sink_receipt': sink_receipt,
            'raw_submission_sha256': hashlib.sha256(text.encode()).hexdigest(),
            'scope': 'external executable selector, not verification of internal reasoning'}


def crossing(first_text, second_text, context):
    records = [parse(first_text), parse(second_text)]
    tables = [validate(r, context) for r in records]
    native = [select(rows, rule)[0] for rows, rule in tables]
    computed = {}

    def cell(pool_index, rule, rule_repeat=None):
        rows, _ = tables[pool_index]
        key = digest({'losses': [[str(x) for x in row] for row in rows], 'rule': rule,
                      'case_id': context['case_id'], 'menu_sha256': context['menu_sha256']})
        if key not in computed:
            action, scores = select(rows, rule)
            computed[key] = {'action_id': action, 'scores_exact': [str(x) for x in scores]}
        return {'pool_repeat': pool_index + 1, 'rule_repeat': rule_repeat, 'rule': rule,
                'computation_id': key, **computed[key], 'researcher_completion_used': False}

    observed = [cell(i, tables[j][1], j + 1) for i in range(2) for j in range(2)]
    family = [cell(i, rule) for i in range(2) for rule in RULES]
    return {'case_id': context['case_id'], 'menu_sha256': context['menu_sha256'],
            'native_action_ids': native, 'same_observed_rule': tables[0][1] == tables[1][1],
            'observed': observed, 'rule_family': family, 'unique_computations': len(computed),
            'observed_unique_actions': sorted({c['action_id'] for c in observed}),
            'observed_new_actions_vs_native': sorted({c['action_id'] for c in observed} - set(native)),
            'family_unique_actions': sorted({c['action_id'] for c in family}),
            'diagnosis_categories': 'not_evaluated_here', 'synthetic_or_live': 'caller_must_record'}
