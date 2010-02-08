import random

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

if __name__ == "__main__":
    import unittest
    class Test(unittest.TestCase):
        def testCumsum(self):
            self.assertEqual(cumsum([1]*10), range(1,11))
            self.assertEqual(cumsum([1,2,3,4,5]), [1,3,6,10,15])

        def testLookup(self):
            cum = [0]+cumsum([5]*10)
            self.assertEqual(lookup(cum,  0), 0)
            self.assertEqual(lookup(cum,  4), 0)
            self.assertEqual(lookup(cum,  5), 1)
            self.assertEqual(lookup(cum, 18), 3)
            self.assertEqual(lookup(cum, 49), 9)

            cum = [0]+cumsum([10, 0, 5, 10])
            self.assertEqual(lookup(cum,  0), 0)
            self.assertEqual(lookup(cum,  8), 0)
            self.assertEqual(lookup(cum, 11), 2)
            self.assertEqual(lookup(cum, 14), 2)
            self.assertEqual(lookup(cum, 15), 3)
            self.assertEqual(lookup(cum, 24), 3)

            counts = [0, 0, 0, 0]
            for i in range(cum[-1]):
                counts[lookup(cum, i)] += 1
            self.assertEqual(counts, [10, 0, 5, 10])

    unittest.main()
