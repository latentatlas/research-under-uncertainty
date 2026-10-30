"""Exact permitted data surface. Contains no catalog, actual table or truth reader."""
import hashlib
import json
import re

TARGET = {"reference_action": 0, "alternative_action": 1,
          "continuation": [0], "terminal_goal": 1}
CLASS = {"max_states": 3, "initial_state": 0, "actions": [0, 1], "outputs": [0, 1]}
ARMS = ("fixed", "adaptive")
QUERIES = ("q0", "q1")


class ContractError(ValueError):
    pass


def need(condition, code):
    if not condition:
        raise ContractError(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def bit(value):
    return type(value) is int and value in (0, 1)


def history_guard(history):
    need(type(history) is list and len(history) == 8, "history_length")
    need(all(type(p) is list and len(p) == 2 and all(bit(v) for v in p)
             for p in history), "history_symbols")


def make_view(trial_id, history):
    history_guard(history)
    hid = digest(history)
    view = {"schema": "paired-observation-view-v1", "trial_id": trial_id,
            "history_id": hid, "target_id": digest([hid, TARGET]),
            "cutoff": 8, "history": history, "candidate_class": CLASS, "target": TARGET}
    return guard_view(view)


def guard_view(view):
    need(type(view) is dict and set(view) == {"schema", "trial_id", "history_id", "target_id",
         "cutoff", "history", "candidate_class", "target"}, "view_fields")
    need(view["schema"] == "paired-observation-view-v1", "view_schema")
    need(type(view["trial_id"]) is str and re.fullmatch(r"[st][0-9]{4}", view["trial_id"])
         and 1 <= int(view["trial_id"][1:]) <= 5000, "trial_identity")
    need(type(view["cutoff"]) is int and view["cutoff"] == 8, "cutoff")
    history_guard(view["history"])
    need(view["history_id"] == digest(view["history"]), "history_identity")
    need(canonical(view["candidate_class"]) == canonical(CLASS), "candidate_class")
    need(canonical(view["target"]) == canonical(TARGET), "target_contract")
    need(view["target_id"] == digest([view["history_id"], TARGET]), "target_identity")
    return view


def guard_receipt(receipt, view, arm, query):
    need(type(receipt) is dict and set(receipt) == {"schema", "trial_id", "arm",
         "view_sha256", "query_id", "output"}, "observation_fields")
    need(receipt["schema"] == "one-step-observation-v1", "observation_schema")
    need(receipt["trial_id"] == view["trial_id"] and receipt["arm"] == arm and
         receipt["view_sha256"] == digest(view), "observation_identity")
    need(receipt["query_id"] == query and query in QUERIES, "observation_query")
    need(bit(receipt["output"]), "observation_bit")
    return receipt
