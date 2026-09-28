#!/usr/bin/env python3
"""Offline arithmetic and provenance checks for one frozen research work sample.

Python 3.10+ standard library only. No network, model client or live agent execution.
The supplied process judgments are inputs, not inferred or certified by this script.
"""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
import scoring

ROUNDING_TOLERANCE = Fraction(1, 2_000_000)


class EvidenceError(ValueError):
    """The supplied evidence or one of its arithmetic checks failed."""


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def number(value):
    return Fraction(str(value))


def response(sequence, law):
    """Exact finite sum, separate from the original laboratory's state update."""
    center = number(law["center"])
    mechanism = law.get("interaction", law.get("mechanism"))
    require(mechanism in (None, "none", "forward", "reverse"), "Unknown mechanism")
    result = Fraction(0)
    previous_u = previous_v = Fraction(0)
    for index, tick in enumerate(sequence):
        require(len(tick) == 3, "A tick must have x, u and v")
        x, u, v = map(number, tick)
        b = min(Fraction(1), max(Fraction(0), 2 * (x - center + Fraction(1, 4))))
        product = previous_u * v if mechanism == "forward" else previous_v * u
        interaction = 4 * b * (1 - b) * product if mechanism in ("forward", "reverse") else 0
        result += (b + u + v + interaction) / 2 ** (len(sequence) - 1 - index)
        previous_u, previous_v = u, v
    return result


def public_observations(packet):
    """The actual observation prefix accessible before a committed action."""
    state = packet["public_payload"]["state"]
    all_records = list(state["records"])
    for event in state["history"]:
        all_records.extend(event["response"].get("records", []))
    unique = {}
    for record in all_records:
        if record["id"] in unique:
            require(unique[record["id"]] == record, "Conflicting observation identity")
        unique[record["id"]] = record
    return list(unique.values())


def claim_check(records, law):
    checked, mismatches = 0, []
    for record in records:
        require(len(record["read_at"]) == len(record["values"]), "Readout shape mismatch")
        for tick, observed in zip(record["read_at"], record["values"]):
            require(1 <= tick <= len(record["sequence"]), "Readout outside the experiment")
            predicted = response(record["sequence"][:tick], law)
            checked += 1
            if abs(number(observed) - predicted) > ROUNDING_TOLERANCE:
                mismatches.append({"record_id": record["id"], "tick": tick,
                                   "observed": str(observed), "predicted": str(predicted)})
    return checked, mismatches


def validate_episode(episode, packets, review, profile, rubric):
    ident = episode["id"]
    require(episode["world"]["coupling"] == "local", "This example covers local coupling only")
    require(len(packets) == episode["committed_decisions"], "Decision coverage changed")
    records = {r["id"]: r for r in episode["observations"]}
    require(len(records) == len(episode["observations"]), "Duplicate observation")
    checked, errors = claim_check(episode["observations"], episode["world"])
    require(not errors, f"Recorded observation disagrees with the evaluator law: {ident}")
    for packet in packets.values():
        require(packet["episode_id"] == ident, "Cross-episode packet")
        for record in public_observations(packet):
            require(record["id"] in records, "Unknown observation in a public prefix")
            require(record == records[record["id"]], "Public/source observation differs")
    closure = episode["closure_claim"]
    packet = packets[f'd{closure["decision"]:05d}']
    claim_count, contradictions = claim_check(public_observations(packet), closure["law"])
    require(claim_count == closure["expected_readings"], "Claim-time coverage changed")
    require(len(contradictions) == closure["expected_mismatches"], "Claim-time residuals changed")
    calculated_profile = scoring.score_review(review, packets, rubric)
    require(calculated_profile == profile, "Frozen process aggregation differs")
    cells = Counter(r["state"] for row in review["decisions"] for r in row["dimensions"].values())
    submission = episode["submission"]
    accepted = sensitive = sensitive_total = None
    target_checks = 0
    if submission is None:
        require(episode["status"] == "participant_protocol_error", "Unexplained absent submission")
        require(episode["original_accepted"] is None, "An unsubmitted run must stay unscored")
        require(episode["original_target_groups"]["point_groups"] is None, "Unscored groups changed")
        failure = episode["uncommitted_protocol_response"]
        require(failure is not None and failure["action"] is not None and failure["stop_reason"],
                "Missing invalid terminal envelope")
    else:
        require(episode["status"] == "completed" and submission["kind"] == "point", "Wrong final type")
        values, targets = submission["values"], episode["targets"]
        require(len(values) == len(targets) == 24, "Final target coverage changed")
        mask = []
        sensitivity = []
        additive = dict(episode["world"], interaction=None)
        for value, target in zip(values, targets):
            exact = response(target["sequence"], episode["world"])
            mask.append(abs(number(value) - exact) <= number(episode["tolerance"]))
            sensitivity.append(abs(exact - response(target["sequence"], additive)) > number(episode["tolerance"]))
        require(mask == episode["original_accepted"], "Original acceptance changed")
        accepted, target_checks = sum(mask), len(mask)
        sensitive = sum(ok and active for ok, active in zip(mask, sensitivity))
        sensitive_total = sum(sensitivity)
        groups = episode["original_target_groups"]
        require(groups["unchanged_total"] == {"accepted": accepted, "total": len(mask)}, "Total differs")
        require(groups["point_groups"]["interaction_sensitive"] ==
                {"accepted": sensitive, "total": sensitive_total}, "Sensitive target group differs")
    return {"id": ident, "status": episode["status"], "accepted": accepted,
            "sensitive_accepted": sensitive, "sensitive_total": sensitive_total,
            "available_at_closure": claim_count, "closure_contradictions": len(contradictions),
            "observation_values_checked": checked, "submitted_targets_checked": target_checks,
            "decisions": len(packets), "process_cell_states": dict(cells),
            "first_contradiction": contradictions[0] if contradictions else None}


def check_inventory(root):
    manifest = read(root / "data/MANIFEST.json")
    for row in manifest["files"]:
        path = root / row["path"]
        require(path.is_file(), f'Missing evidence: {row["path"]}')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == row["sha256"],
                f'Evidence bytes changed: {row["path"]}')
    return len(manifest["files"])


def verify(root=ROOT):
    root = Path(root)
    files_checked = check_inventory(root)
    data = read(root / "data/episodes.json")
    rubric = read(root / "src/RUBRIC.json")
    require(len(data["episodes"]) == 4, "The registered four-run set must remain complete")
    rows, counts = [], Counter()
    for episode in data["episodes"]:
        folder = root / "evidence" / episode["id"]
        row = validate_episode(episode, read(folder / "PACKETS.json"), read(folder / "REVIEW.json"),
                               read(folder / "PROFILE.json"), rubric)
        rows.append(row)
        counts.update(row["process_cell_states"])
    exemplar = data["matched_history"]
    ep = next(e for e in data["episodes"] if e["id"] == "sol-high-cdr-w2-r2")
    selected = [next(r for r in ep["observations"] if r["id"] == ident) for ident in exemplar["record_ids"]]
    require(selected[0]["sequence"][1:] == selected[1]["sequence"][1:], "Continuations differ")
    for record, first, second in zip(selected, exemplar["first_values"], exemplar["second_values"]):
        values = dict(zip(record["read_at"], record["values"]))
        require(values[1] == first and values[2] == second, "Matched-history measurements differ")
    require(exemplar["first_values"][0] == exemplar["first_values"][1], "Unequal initial outputs")
    require(exemplar["second_values"][0] != exemplar["second_values"][1], "No observed divergence")
    return {"status": "passed", "scope": "Offline numeric, identity, citation and frozen-aggregation checks; no semantic certification or live experiment.",
            "files_checked": files_checked, "episodes": rows,
            "numeric_values_checked": sum(r["observation_values_checked"] + r["submitted_targets_checked"] for r in rows),
            "decisions": sum(r["decisions"] for r in rows), "process_cell_states": dict(counts),
            "scalar_process_score": None, "matched_history": exemplar}


def show_decision(suffix, decision):
    data = read(ROOT / "data/episodes.json")
    matches = [e for e in data["episodes"] if e["id"] == suffix or e["id"].endswith("-" + suffix)]
    require(len(matches) == 1, "Choose exactly one recorded episode")
    ident = matches[0]["id"]
    packet = read(ROOT / "evidence" / ident / "PACKETS.json")[f"d{decision:05d}"]
    # The next packet is the first stored pre-action context that contains this response.
    packets = read(ROOT / "evidence" / ident / "PACKETS.json")
    next_packet = packets.get(f"d{decision + 1:05d}")
    response_event = next_packet["public_payload"]["state"]["history"][-1] if next_packet else None
    return {"episode": ident, "decision": decision,
            "measurements_available_before": sum(len(r["values"]) for r in public_observations(packet)),
            "action_and_public_record": packet["decision"],
            "next_recorded_event": response_event,
            "next_public_record": next_packet["decision"]["record"] if next_packet else None,
            "scope": "Original public records; not private chain-of-thought. No next packet exists after the last committed decision."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print the complete verification report")
    parser.add_argument("--episode", help="Inspect a decision, e.g. w2-r2")
    parser.add_argument("--decision", type=int, help="One-based committed decision")
    args = parser.parse_args()
    try:
        if args.episode or args.decision is not None:
            require(bool(args.episode) and args.decision is not None, "Use --episode and --decision together")
            check_inventory(ROOT)
            print(json.dumps(show_decision(args.episode, args.decision), ensure_ascii=False, indent=2))
            return
        result = verify()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("Offline evidence checks: PASSED")
            print("Episode       Outcome                    Targets   Sensitive   Contradictions at closure")
            for row in result["episodes"]:
                total = "unscored" if row["accepted"] is None else f'{row["accepted"]}/24'
                sensitive = "unscored" if row["sensitive_total"] is None else f'{row["sensitive_accepted"]}/{row["sensitive_total"]}'
                print(f'{row["id"].removeprefix("sol-high-cdr-"):<13} {row["status"]:<26} {total:<9} {sensitive:<11} {row["closure_contradictions"]}/{row["available_at_closure"]}')
            print(f'{result["numeric_values_checked"]} numeric values; {result["decisions"]} decisions; {sum(result["process_cell_states"].values())} process cells.')
            print("No overall process score. Ratings are supplied interpretations, not validated by this computation.")
    except (ValueError, KeyError, IndexError, OSError) as exc:
        print(f"Verification failed: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
