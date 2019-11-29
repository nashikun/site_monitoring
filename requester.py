from threading import Thread
import time
import requests


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
