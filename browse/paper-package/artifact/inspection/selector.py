"""Pure selector over public-contract branch cardinalities; no world access."""
def select_query(branch_target_counts):
    if type(branch_target_counts) is not dict or set(branch_target_counts)!={'q0','q1'}:
        raise ValueError('exactly the two contracted queries required')
    scores=[]
    for order,q in enumerate(('q0','q1')):
        counts=branch_target_counts[q]
        if type(counts) not in (list,tuple) or len(counts)!=2:
            raise ValueError('two response branches required')
        if any(type(n) is not int or n<0 for n in counts) or not any(counts):
            raise ValueError('invalid cardinality or empty compatible class')
        pure=sum(n==1 for n in counts)
        scores.append((-pure,max(counts),order,q))
    return min(scores)[-1]
