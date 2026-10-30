"""The recorded one-action grading procedure with local, explicit inputs."""
from . import physics as W
from .records import digest
from .snapshot_core import assess, bind_method, response_action, score_action, validate_packet


def grade(bundle, action):
    case = bundle['case']
    packet = bundle['packet']
    validate_packet(packet, case)
    if digest(bundle['world']) != bundle['world_sha256']:
        raise ValueError('world identity mismatch')
    if len(bundle['source_trace']) != case['after_step']:
        raise ValueError('source prefix length mismatch')
    bind_method(W)
    response_action({'action': action}, W)
    count = 0

    def step(episode, value):
        nonlocal count
        count += 1
        return episode.step(value)

    episode = W.Episode(bundle['world'])
    for row in bundle['source_trace']:
        step(episode, row['action'])
        if episode.trace[-1] != row:
            raise ValueError('source transition mismatch')
    if episode.history() != packet['history']:
        raise ValueError('visible history mismatch')
    before = assess(episode, W, step)
    step(episode, action)
    after = assess(episode, W, step)
    return {'case_id': case['case_id'], 'before': before, 'after': after,
            'applied_action': episode.actions[-1],
            'diagnostic_score': score_action(before, after), 'local_physics_steps': count}
