import unittest
from collections import Counter
from src.fixed_size import FixedSizeQueue
from operator import itemgetter
from src.utils import Requester
from src.site_monitor import SiteMonitor, RequestScheduler
import time


class MyTestCase(unittest.TestCase):
    def test_add(self):
        queue = FixedSizeQueue(5, itemgetter(0))
        queue.add((0, 0))
        queue.add((1, 0))
        queue.add((5, 0))
        queue.add((2, 0))
        queue.add((4, 0))
        queue.add((3, 0))
        self.assertListEqual(queue.h, [(1, 0), (2, 0), (3, 0), (4, 0), (5, 0)])

    def test_slice(self):
        queue = FixedSizeQueue(5, itemgetter(0))
        queue.add((0, 0))
        queue.add((1, 0))
        queue.add((5, 0))
        queue.add((2, 0))
        queue.add((4, 0))
        queue.add((3, 0))
        self.assertListEqual(queue.get_slice(3, 4), [(3, 0), (4, 0)])
        self.assertListEqual(queue.get_slice(2, 5), [(2, 0), (3, 0), (4, 0), (5, 0)])

    def test_requester(self):
        queue = FixedSizeQueue(int(600 / 1), key=itemgetter(0))
        requester = Requester('http://localhost:4444', queue, 5)
        requester.start()
        time.sleep(5)
        self.assertIsInstance(queue.h, list)
        _, code, elapsed = queue.h[0]
        self.assertEqual(code, 200)
        self.assertTrue(0 < elapsed < 1)

    def test_request_scheduler(self):
        scheduler = RequestScheduler(1, 'http://localhost:4444/delay?increment=1&reset_after=6', 5)
        t = time.time()
        scheduler.start()
        time.sleep(6.1)
        scheduler.stop()
        time.sleep(5)
        time_slice = scheduler.results.get_slice(t, t + 6.1)
        self.assertIsInstance(time_slice, list)
        self.assertEqual(len(time_slice), 6)
        _, code, elapsed = zip(*time_slice)
        self.assertTrue(all([-0.1 < a-b < 0.1 for a, b in zip(elapsed, [1, 2, 3, 4, 5, 5])]))
        self.assertListEqual(list(code), [200, 200, 200, 200, 408, 408])

    def test_stats(self):
        monitor = SiteMonitor('probability', 'http://localhost:4444/unavailable?probability=1', 0.1, 5)
        t = time.time()
        monitor.start()
        time.sleep(121)
        monitor.stop()
        time.sleep(5)
        self.assertAlmostEqual(monitor.unavailable_since, t, 1)
        self.assertEqual(monitor.metrics[120]['availability'], 0)
        self.assertIsInstance(monitor.metrics, dict)
        self.assertIsInstance(monitor.metrics[10]['codes_count'], Counter)
        self.assertIsInstance(monitor.metrics[60]['codes_count'], Counter)
        self.assertEqual(list(monitor.metrics[10]['codes_count'].keys()), [400])
        self.assertEqual(list(monitor.metrics[60]['codes_count']), [400])
        self.assertAlmostEqual(monitor.metrics[10]['codes_count'][400] / monitor.metrics[60]['codes_count'][400], 1, 2)
        self.assertTrue(1100 < monitor.metrics[10]['codes_count'][400] <= 1160)


if __name__ == '__main__':
    unittest.main()
