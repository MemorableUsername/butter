import os
import sys
sys.path += [os.path.join(sys.path[0], '..')]
import prob
import unittest

class ProbTest(unittest.TestCase):
    def testCumsum(self):
        self.assertEqual(prob.cumsum([1]*10), range(1,11))
        self.assertEqual(prob.cumsum([1,2,3,4,5]), [1,3,6,10,15])

    def testLookup(self):
        cum = [0]+prob.cumsum([5]*10)
        self.assertEqual(prob.lookup(cum,  0), 0)
        self.assertEqual(prob.lookup(cum,  4), 0)
        self.assertEqual(prob.lookup(cum,  5), 1)
        self.assertEqual(prob.lookup(cum, 18), 3)
        self.assertEqual(prob.lookup(cum, 49), 9)

        cum = [0]+prob.cumsum([10, 0, 5, 10])
        self.assertEqual(prob.lookup(cum,  0), 0)
        self.assertEqual(prob.lookup(cum,  8), 0)
        self.assertEqual(prob.lookup(cum, 11), 2)
        self.assertEqual(prob.lookup(cum, 14), 2)
        self.assertEqual(prob.lookup(cum, 15), 3)
        self.assertEqual(prob.lookup(cum, 24), 3)

        counts = [0, 0, 0, 0]
        for i in range(cum[-1]):
            counts[prob.lookup(cum, i)] += 1
        self.assertEqual(counts, [10, 0, 5, 10])

    def testLinspace(self):
        self.assertEqual(list(prob.linspace(2.0, 3.0, 5)),
                         [2.0, 2.25, 2.5, 2.75, 3.0])
        self.assertEqual(list(prob.linspace(2.0, 3.0, 4, endpoint=False)),
                         [2.0, 2.25, 2.5, 2.75])
        self.assertRaises(Exception, prob.linspace, (1.0, 2.0, 1))

if __name__ == '__main__':
    unittest.main()
