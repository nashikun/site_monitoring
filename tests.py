import unittest

from FixedSizeQueue import FixedSizeQueue
from operator import itemgetter


class MyTestCase(unittest.TestCase):
    def test_add(self):
        queue = FixedSizeQueue(5, itemgetter(0))
        queue.add((0, 0))
        queue.add((1, 0))
        queue.add((5, 0))
        queue.add((2, 0))
        queue.add((4, 0))
        queue.add((3, 0))
        self.assertEqual(queue.h, [(1, 0), (2, 0), (3, 0), (4, 0), (5, 0)])

    def test_slice(self):
        queue = FixedSizeQueue(5, itemgetter(0))
        queue.add((0, 0))
        queue.add((1, 0))
        queue.add((5, 0))
        queue.add((2, 0))
        queue.add((4, 0))
        queue.add((3, 0))
        self.assertEqual(queue.get_slice(3, 4), [(3, 0), (4, 0)])
        self.assertEqual(queue.get_slice(2, 5), [(2,0), (3, 0), (4, 0), (5, 0)])



if __name__ == '__main__':
    unittest.main()
