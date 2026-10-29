"""Pure reproducible rejection mapping; no environment, target or model execution."""
import hashlib


def require(ok, code):
    if not ok:
        raise ValueError(code)


def words(seed_hex):
    require(type(seed_hex) is str and len(seed_hex) == 64, "seed_length")
    seed = bytes.fromhex(seed_hex)
    require(len(seed) == 32, "seed_bytes")
    for counter in range(10000):
        block = hashlib.sha256(b"paired-observation-study-v1\0" + seed + counter.to_bytes(8, "big")).digest()
        for offset in range(0, 32, 4):
            yield int.from_bytes(block[offset:offset + 4], "big")


def draw(population, n, stream):
    require(type(population) is int and 0 < population <= 2**32, "population")
    require(type(n) is int and n > 0, "draw_N")
    limit = (2**32 // population) * population
    ranks, receipts = [], []
    for word in stream:
        require(type(word) is int and 0 <= word < 2**32, "entropy_word")
        accepted = word < limit
        receipts.append({"word": word, "accepted": accepted})
        if accepted:
            ranks.append(word % population)
        if len(ranks) == n or len(receipts) == n * 16:
            break
    return {"status": "complete" if len(ranks) == n else "technical_entropy_incomplete",
            "population_pairs": population, "requested_N": n, "limit": limit,
            "ranks": ranks, "receipts": receipts}


def split(rank, world_count):
    require(type(world_count) is int and world_count > 0, "world_count")
    require(type(rank) is int and 0 <= rank < 256 * world_count, "rank")
    index, word = divmod(rank, 256)
    return index, [(word >> (7 - bit)) & 1 for bit in range(8)]
