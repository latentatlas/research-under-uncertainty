"""Known-class computation, never actual-world computation. One full pass per arm."""
from wire import need, QUERIES

COUNTERS = ("candidate_decodes", "history_checks", "history_steps", "candidate_history_resets",
            "query_candidate_evaluations", "query_candidate_steps", "target_candidate_evaluations",
            "target_candidate_steps", "selection_branch_checks", "certificate_branch_lookups",
            "within_arm_reused_query_values")


def decode(code):
    edges = []
    for _ in range(6):
        code, digit = divmod(code, 6)
        edges.append((digit // 2, digit % 2))
    return edges


def candidate_target(table, state):
    # Public target contract, applied to hypothetical candidates only.
    left = table[2 * state][0]
    right = table[2 * state + 1][0]
    return 2 * table[2 * left][1] + table[2 * right][1]


def scan(history, queries):
    need(queries in (("q0",), QUERIES), "scan_scope")
    work = dict.fromkeys(COUNTERS, 0)
    counts = {q: [[0] * 4 for _ in range(2)] for q in queries}
    joint = [0] * 16 if len(queries) == 2 else None
    initial_targets = [0] * 4
    compatible = 0
    for code in range(46656):
        table = decode(code)
        work["candidate_decodes"] += 1
        work["history_checks"] += 1
        work["candidate_history_resets"] += 1
        state = 0
        for action, expected in history:
            state, output = table[2 * state + action]
            work["history_steps"] += 1
            if output != expected:
                break
        else:
            compatible += 1
            target = candidate_target(table, state)
            work["target_candidate_evaluations"] += 1
            work["target_candidate_steps"] += 4
            initial_targets[target] += 1
            ys = []
            for q in queries:
                y = table[2 * state + (q == "q1")][1]
                counts[q][y][target] += 1
                ys.append(y)
                work["query_candidate_evaluations"] += 1
                work["query_candidate_steps"] += 1
            if joint is not None:
                joint[4 * (2 * ys[0] + ys[1]) + target] += 1
    need(compatible > 0, "empty_initial_support")
    cardinalities = {q: [sum(n > 0 for n in row) for row in rows] for q, rows in counts.items()}
    return {"counts": counts, "joint": joint, "cardinalities": cardinalities,
            "initial_target_cardinality": sum(n > 0 for n in initial_targets),
            "compatible_before": compatible, "work": work}


def possibilities(scan_result, chosen):
    need(scan_result["joint"] is not None, "both_queries_required")
    cards = scan_result["cardinalities"]
    gain = loss = False
    for y0 in range(2):
        for y1 in range(2):
            offset = 4 * (2 * y0 + y1)
            if not sum(scan_result["joint"][offset:offset + 4]):
                continue
            fixed = cards["q0"][y0] == 1
            adaptive = cards[chosen][y1 if chosen == "q1" else y0] == 1
            gain |= adaptive and not fixed
            loss |= fixed and not adaptive
    return {"gain_possible": gain, "loss_possible": loss}


def finish(scan_result, query, response, adaptive):
    row = scan_result["counts"][query][response]
    targets = [i for i, n in enumerate(row) if n]
    need(bool(targets), "empty_post_observation_support")
    scan_result["work"]["certificate_branch_lookups"] += 1
    if adaptive:
        scan_result["work"]["within_arm_reused_query_values"] += scan_result["compatible_before"]
    return {"certificate": len(targets) == 1, "prediction": targets[0] if len(targets) == 1 else None,
            "target_values": targets, "compatible_after": sum(row),
            "compatible_before": scan_result["compatible_before"],
            "initial_target_cardinality": scan_result["initial_target_cardinality"],
            "chosen_branch_target_cardinality": len(targets)}
