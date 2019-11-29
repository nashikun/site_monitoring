from threading import Thread
from fixed_size import FixedSizeQueue
from operator import itemgetter
from requester import Requester
import time


class RequestScheduler(Thread):

    """
    This class creates a :class:`requester.Requester` object every *interval* and stores the results in a queue.

    :param string url: the url to make requests to.
    :param float interval: the interval between requests
    :param timeout: the time to wait before considering that the response timed-out.
    :ivar fixed_size.FixedSizeQueue results: stores the request responses.
    """

    def __init__(self, interval, url, timeout):
        super(RequestScheduler, self).__init__()
        self.url = url
        self.interval = interval
        self.results = FixedSizeQueue(int(600 / interval), key=itemgetter(0))
        self.timeout = timeout
        self.set_stop = False

    def run(self):
        """
        start making requests every **interval**
        """
        t = time.time()
        while not self.set_stop:
            #   Used this instead of time.sleep(self.interval) to reduce the number of iterations 'lost'
            if time.time() - t > self.interval:
                req = Requester(self.url, self.results, self.timeout)
                req.start()
                t = time.time()
            time.sleep(self.interval / 1000)

    def stop(self):
        """
        stop making requests
        """
        self.set_stop = True
