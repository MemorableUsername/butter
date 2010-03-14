import math
import random
import itertools

def cumsum(l, t=0):
    """Return the cumulative sum of an iterable"""
    r = [None] * len(l)
    for i,v in enumerate(l):
        r[i] = t = t+v
    return r

def lookup(p, k):
    """Given a cumulative distribution of discrete values, return the value at
    k"""
    lo = 0
    hi = len(p)-1
    while True:
        if lo == hi: return lo
        mid = hi - (hi-lo)/2
        if p[mid] > k:
            hi = mid-1
        else:
            lo = mid

def weighted_sample(weights, k):
    """Return a list of k choices in the range [0, len(weights)) with the
    probabilities specified in weights"""
    cum = [0]+cumsum(weights)
    n = cum[-1]
    result = [None] * k
    selected = set()

    for i in xrange(k):
        j = random.randrange(n)
        while lookup(cum, j) in selected:
            j = random.randrange(n)
        result[i] = lookup(cum, j)
        selected.add(result[i])
    return result

def weighted_choice(weights):
    """Return an integer in the range [0, len(weights)) with the probabilities
    specified in weights"""
    cum = [0]+cumsum(weights)
    n = cum[-1]
    return lookup(cum, random.randrange(n))

def poissonvariate(lambd):
    x = random.random()
    
    # special-case i = 0
    coeff = math.exp(-lambd)
    factorial = 1.0
    x -= coeff
    if x < 0: return 0

    # i = (1, 2, ...)
    for i in itertools.count(1):
        factorial *= i
        x -= coeff * (lambd**i/factorial)
        if x < 0: return i
