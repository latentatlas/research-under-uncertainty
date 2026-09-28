"""Experimental ordinal scoring. Semantic judgments are authored, never inferred here."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
DIMENSIONS = ('D1', 'D2', 'D3', 'D4', 'D5')
UNSCORED = ('no_opportunity', 'insufficient_evidence', 'out_of_rubric', 'disputed')


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def require(test, message):
    if not test:
        raise ValueError(message)


def pointer(value, path):
    require(isinstance(path, str) and path.startswith('/'), 'Absolute JSON pointer required')
    for token in path[1:].split('/'):
        key = token.replace('~1', '/').replace('~0', '~')
        if isinstance(value, list):
            require(key.isdigit() and (key == '0' or not key.startswith('0')), 'Invalid list pointer')
            value = value[int(key)]
        else:
            value = value[key]
    return value


def packets_from_events(episode_id, events):
    """A packet contains only the exact current public payload and committed decision."""
    by_id = {e['id']: e for e in events}
    require(len(by_id) == len(events), 'Duplicate event identity')
    packets = {}
    for event in events:
        if event['kind'] != 'decision_commit':
            continue
        callback = by_id[event['body']['callback_id']]
        require(callback['kind'] == 'callback_started' and callback['sequence'] < event['sequence'], 'Wrong callback')
        env = event['body']['envelope']
        packet = {'schema_version': 'process-score-packet-v1', 'episode_id': episode_id,
                  'decision_id': event['id'], 'sequence': event['sequence'], 'phase': 'pre',
                  'public_payload': callback['body']['payload'],
                  'decision': {k: env.get(k) for k in ('action', 'record', 'stop_reason')}}
        packets[event['id']] = packet
    return packets


def cite(packet, path):
    require(path.startswith(('/public_payload/', '/decision/')), 'Evidence outside public packet')
    return {'pointer': path, 'value_sha256': digest(pointer(packet, path))}


def validate_citations(packet, values, required=False):
    require(isinstance(values, list) and (values or not required), 'Missing evidence')
    for ref in values:
        require(isinstance(ref, dict) and set(ref) == {'pointer', 'value_sha256'}, 'Invalid citation fields')
        require(cite(packet, ref['pointer']) == ref, 'Evidence pointer/hash differs')


def score_review(review, packets, rubric=None):
    rubric = rubric or read(ROOT/'RUBRIC.json')
    require(review.get('rubric_sha256') == digest(rubric), 'Wrong frozen rubric')
    require(review.get('reviewer', {}).get('kind') == 'model', 'Reviewer provenance must be explicit')
    require(review['reviewer'].get('exposure') == 'project_designer_outcome_known', 'Exposure declaration missing')
    rows = review.get('decisions')
    require(isinstance(rows, list), 'Decision coverage missing')
    require([r['decision_id'] for r in rows] == list(packets), 'Decision order/coverage differs')
    issues = review.get('issues', [])
    require(isinstance(issues, list), 'Issue list required')
    indexed = {x['issue_id']: x for x in issues}
    require(len(indexed) == len(issues), 'Duplicate issue id')
    used_issues = set()
    episode_ids = {p['episode_id'] for p in packets.values()}
    require(not packets or episode_ids == {review['episode_id']}, 'Cross-episode review')
    for row in rows:
        packet = packets[row['decision_id']]
        require(row.get('packet_sha256') == digest(packet), 'Packet identity differs')
        require(set(row.get('dimensions', {})) == set(DIMENSIONS), 'All five dimensions require coverage')
        for dim, reading in row['dimensions'].items():
            require(isinstance(reading.get('rationale'), str) and reading['rationale'].strip(), 'Rationale missing')
            require(isinstance(reading.get('limitation'), str) and reading['limitation'].strip(), 'Limit missing')
            require(isinstance(reading.get('issue_ids'), list), 'Issue links missing')
            require(len(reading['issue_ids']) == len(set(reading['issue_ids'])), 'Duplicate issue link')
            state = reading.get('state')
            if state == 'scored':
                anchor = reading.get('anchor')
                require(anchor in rubric['dimensions'][dim]['anchors'], 'Unknown dimension anchor')
                expected = rubric['dimensions'][dim]['anchors'][anchor]['score']
                require(type(reading.get('score')) is int and reading['score'] == expected, 'Score/anchor mismatch')
                validate_citations(packet, reading.get('evidence'), required=True)
                if expected < 2:
                    require(bool(reading['issue_ids']), 'Partial/adverse judgment needs a concrete issue')
            else:
                require(state in UNSCORED and reading.get('score') is None and reading.get('anchor') is None,
                        'Unscored state must remain null')
                validate_citations(packet, reading.get('evidence'), required=False)
            for ident in reading['issue_ids']:
                require(ident in indexed and indexed[ident]['dimension'] == dim, 'Wrong issue/criterion binding')
                issue = indexed[ident]
                require(issue['opened_at'] in packets and packets[issue['opened_at']]['sequence'] <= packet['sequence'],
                        'Future issue attribution')
                used_issues.add(ident)
    require(used_issues == set(indexed), 'Unused issue changes aggregation')
    for issue in issues:
        require(isinstance(issue.get('group_id'), str) and bool(issue['group_id']), 'Cross-dimension issue group missing')
        require(isinstance(issue.get('description'), str) and bool(issue['description']), 'Issue explanation missing')
        opened = packets[issue['opened_at']]
        first = next(r for r in rows if r['decision_id'] == issue['opened_at'])['dimensions'][issue['dimension']]
        require(issue['issue_id'] in first['issue_ids'], 'Issue not present at declared opening')
        resolved = issue.get('resolved_at')
        if resolved is not None:
            require(resolved in packets and packets[resolved]['sequence'] > opened['sequence'], 'Recovery must be later')
            require(isinstance(issue.get('closure_rationale'), str) and bool(issue['closure_rationale']), 'Recovery rationale missing')
            validate_citations(packets[resolved], issue.get('closure_evidence'), required=True)
        else:
            require(not issue.get('closure_evidence'), 'Unresolved issue has recovery evidence')
    profile = {}
    for dim in DIMENSIONS:
        readings = [r['dimensions'][dim] for r in rows]
        scored = [r for r in readings if r['state'] == 'scored']
        unknown = [r for r in readings if r['state'] in ('insufficient_evidence', 'out_of_rubric', 'disputed')]
        critical = {i for r in scored if r['score'] == 0 for i in r['issue_ids']}
        unresolved = sorted(i for i in critical if indexed[i].get('resolved_at') is None)
        observed = (None if not scored else 0 if unresolved else 1 if any(r['score'] < 2 for r in scored) else 2)
        profile[dim] = {
            'score': None if unknown else observed,
            'observed_subset_score': observed,
            'coverage': {'all_decisions': len(rows), 'scored': len(scored),
                         **{s: sum(r['state'] == s for r in readings) for s in UNSCORED}},
            'decision_level_counts': {str(i): sum(r['score'] == i for r in scored) for i in (0, 1, 2)},
            'unresolved_critical_issue_ids': unresolved,
            'recovered_critical_issue_ids': sorted(critical-set(unresolved)),
            'status': 'incomplete_evidence' if unknown else 'not_observed' if not scored else 'experimental_profile',
        }
    return {'schema_version': 'ordinal-process-profile-v1', 'episode_id': review['episode_id'],
            'rubric_sha256': digest(rubric), 'review_sha256': digest(review),
            'packet_sha256': {k: digest(v) for k, v in packets.items()},
            'profile': profile, 'unique_issue_groups': sorted({i['group_id'] for i in issues}),
            'scalar_score': None, 'ranking_validated': False, 'semantic_validation': 'researcher_judgment_not_independent',
            'scope': 'Conservative ordinal profile of recorded opportunities. Complete pointer/coverage checks do not certify semantic judgments. '
                     'Any unresolved critical issue gives0; partial or recovered concern gives1; otherwise observed criteria give2. '
                     'No frequency averaging, step-count reward, or general research-ability ratio.'}


def write_new(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
