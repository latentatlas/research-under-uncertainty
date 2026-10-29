"""Private structural population definition. No trajectory or target evaluator."""
from itertools import product


def require(ok, message):
    if not ok:
        raise ValueError(message)


def validate(table):
    require(isinstance(table, tuple) and len(table) in (2, 4, 6), "table shape")
    n = len(table) // 2
    for edge in table:
        require(isinstance(edge, tuple) and len(edge) == 2, "edge shape")
        s, o = edge
        require(type(s) is int and 0 <= s < n, "next state")
        require(type(o) is int and o in (0, 1), "output")
    return n


def from_world(world):
    require(set(world) == {"schema", "states", "initial_state", "edges"}, "world fields")
    n = world["states"]
    require(type(n) is int and n in (1, 2, 3), "states")
    require(type(world["initial_state"]) is int and world["initial_state"] == 0, "initial")
    index = {}
    require(isinstance(world["edges"], list), "edges")
    for e in world["edges"]:
        require(set(e) == {"from", "action", "to", "output"}, "edge fields")
        require(type(e["from"]) is int and 0 <= e["from"] < n, "source")
        require(type(e["action"]) is int and e["action"] in (0, 1), "action")
        k = (e["from"], e["action"])
        require(k not in index, "duplicate edge")
        index[k] = (e["to"], e["output"])
    require(len(index) == n * 2, "incomplete world")
    table = tuple(index[s, a] for s in range(n) for a in (0, 1))
    validate(table)
    return table


def reachable(table):
    validate(table)
    order = [0]
    for s in order:
        for a in (0, 1):
            t = table[2 * s + a][0]
            if t not in order:
                order.append(t)
    return order


def canonical(table):
    """Minimize by stable output/next-block refinement, then root-preserving BFS."""
    states = reachable(table)
    blocks = {s: 0 for s in states}
    while True:
        signature_ids = {}
        new = {}
        for s in states:
            sig = tuple((table[2 * s + a][1], blocks[table[2 * s + a][0]]) for a in (0, 1))
            new[s] = signature_ids.setdefault(sig, len(signature_ids))
        if new == blocks:
            break
        blocks = new
    reps = {}
    for s in states:
        reps.setdefault(blocks[s], s)
    queue = [blocks[0]]
    result = []
    for b in queue:
        s = reps[b]
        for a in (0, 1):
            t, o = table[2 * s + a]
            target = blocks[t]
            if target not in queue:
                queue.append(target)
            result.append((queue.index(target), o))
    return tuple(result)


def equivalent(left, right):
    """Independent product-relation check; does not use partition refinement."""
    validate(left)
    validate(right)
    pending, visited = [(0, 0)], set()
    while pending:
        pair = pending.pop()
        if pair in visited:
            continue
        visited.add(pair)
        s, t = pair
        for a in (0, 1):
            ls, lo = left[2 * s + a]
            rs, ro = right[2 * t + a]
            if lo != ro:
                return False
            pending.append((ls, rs))
    return True


def relabel(table, permutation):
    n = validate(table)
    require(permutation[0] == 0 and sorted(permutation) == list(range(n)), "rooted permutation")
    result = [None] * (n * 2)
    for s in range(n):
        for a in (0, 1):
            t, o = table[2 * s + a]
            result[2 * permutation[s] + a] = (permutation[t], o)
    return tuple(result)


def enumerate_tables(n):
    require(type(n) is int and n in (1, 2, 3), "state count")
    edges = tuple(product(range(n), (0, 1)))
    yield from product(edges, repeat=2 * n)


def draw_ranks(population_pairs, count, words):
    """Future iid-with-replacement mapping. Caller's word stream; no RNG or outcomes."""
    require(type(population_pairs) is int and 0 < population_pairs <= 2 ** 32, "population pairs")
    require(type(count) is int and count > 0, "draw count")
    limit = (2 ** 32 // population_pairs) * population_pairs
    ranks, receipts = [], []
    stream = iter(words)
    for _ in range(count * 16):
        try:
            word = next(stream)
        except StopIteration:
            break
        require(type(word) is int and 0 <= word < 2 ** 32, "entropy word")
        accepted = word < limit
        receipts.append({"word": word, "accepted": accepted})
        if accepted:
            ranks.append(word % population_pairs)
            if len(ranks) == count:
                return {"status": "complete", "ranks": ranks, "receipts": receipts}
    return {"status": "technical_entropy_incomplete", "ranks": ranks, "receipts": receipts}


def split_rank(rank, world_count):
    require(type(world_count) is int and world_count > 0, "world count")
    require(type(rank) is int and 0 <= rank < world_count * 256, "unit rank")
    world_index, word = divmod(rank, 256)
    actions = tuple((word >> (7 - i)) & 1 for i in range(8))
    return world_index, actions
