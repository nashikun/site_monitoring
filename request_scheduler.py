from threading import Thread
from fixed_size_queue import FixedSizeQueue
from operator import itemgetter
from requester import Requester
import time


class RequestScheduler(Thread):

    def __init__(self, interval, url, timeout):
        super(RequestScheduler, self).__init__()
        self.url = url
        self.interval = interval
        self.results = FixedSizeQueue(int(600 / interval), key=itemgetter(0))
        self.timeout = timeout
        self.set_stop = False

    def run(self):
        t = time.time()
        while not self.set_stop:
            #   Used this instead of time.sleep(self.interval) to reduce the number of iterations 'lost'
            if time.time() - t > self.interval:
                req = Requester(self.url, self.results, self.timeout)
                req.start()
                t = time.time()
            time.sleep(self.interval / 1000)

    def stop(self):
        self.set_stop = True
