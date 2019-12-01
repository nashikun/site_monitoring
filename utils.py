from tzlocal import get_localzone
from datetime import datetime
import time
import requests
from threading import Thread
from fixed_size import FixedSizeQueue
from operator import itemgetter

local_tz = get_localzone()
"""
This module is for the different simple reusable classes and functions 
"""


def get_local_time(timestamp):
    """
    Converts time from unix time to a :class:`datetime.datetime` object repreesnting time in the current time-zone
    :param timestamp: the unix time stamp
    :return: the time in the current timezone
    """
    return local_tz.localize(datetime.fromtimestamp(timestamp))


class Requester(Thread):
    """
    The base class that sends requests and adds relevant data to the queue in the right order.

    :param url: the url to make requests to
    :param queue: the queue to which add the gathered data
    :param timeout: the time to wait before considering the request timed-out
    """

    def __init__(self, url, queue, timeout):
        super(Requester, self).__init__()
        self.url = url
        self.queue = queue
        self.timeout = timeout

    def run(self):
        """
        Runs the :class:`Requester` and adds the result to the queue before exiting.
        If connection to the site fails, the status code is 503
        If the connection succeeds but times out, the status code is 408

        :rtype: None
        """
        t = time.time()
        try:
            response = requests.get(self.url, timeout=self.timeout)
            self.queue.add((t, response.status_code, time.time() - t))
        except requests.exceptions.ConnectionError:
            self.queue.add((t, 503, time.time() - t))
        except requests.exceptions.ReadTimeout:
            self.queue.add((t, 408, self.timeout))


class RequestScheduler(Thread):
    """
    This class creates a :class:`requester.Requester` object every *interval* and stores the results in a queue.

    :param string url: the url to make requests to.
    :param float interval: the interval between requests in seconds
    :param timeout: the time to wait in seconds before considering that the response timed-out.
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
