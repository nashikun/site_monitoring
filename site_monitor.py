from threading import Thread, Semaphore
from request_scheduler import RequestScheduler
import time
from collections import Counter
from operator import itemgetter


class SiteMonitor(Thread):
    """
    The class to get relevant metrics over time from an url.`
    The methods have been implemented here instead of in :class:`request_scheduler.RequestScheduler` to
    avoid delaying the requests made periodically.

    :ivar request_scheduler request_scheduler: the scheduler making requests once per interval.
    :ivar float availability: the availability of the website during the last two minutes.
    :ivar Union[float,None] unavailable_since: the unix time of the first time the url became unavailable.
        Is None if the site is available.
    :ivar Union[float,None] recovered_at: the unix time since the website recovered.
        Is None if the website is currently unavailable or the availability never went below 80%
    :ivar dict last_updates: holds the time of the last updates to the metrics
    :ivar dict is_read: a dict with booleans representing whether the latest metric
        on each time-frame has been retrieved or not.
    :ivar bool set_stop: whether the monitor has been set to stop.
    """

    def __init__(self, interval, url, timeout):
        super(SiteMonitor, self).__init__()
        self.request_scheduler = RequestScheduler(interval, url, timeout)
        self.timeout = timeout
        self.availability = None
        self.unavailable_since = None
        self.recovered_at = None
        t = time.time()
        self.last_updates = {10: t, 60: t, 120: t}
        self.metrics = {}
        self.is_read = {10: True, 60: True, 120: True}
        self.set_stop = False
        self.metrics_sem = Semaphore()

    def stop(self):
        """
        Stops the monitoring.
        """
        self.request_scheduler.stop()
        self.set_stop = True

    def run(self):
        """
        Starts monitoring the website. Each 10 seconds, calculate the metrics over the last 10 minutes,
            each minute calculate the metrics over the last hour, and update the availability every two minutes.
        """
        self.request_scheduler.start()
        while not self.set_stop:
            if time.time() - self.last_updates[10] > 10:
                self.update_metrics(10, 600)
            if time.time() - self.last_updates[60] > 60:
                self.update_metrics(60, 3600)
            if time.time() - self.last_updates[120] > 120:
                self.update_availability()
            time.sleep(0.01)

    def update_metrics(self, delay, duration):
        """
        Retrieves the metrics and stores them.
        :param delay: the interval between each two metric updates.
        :param duration: the time window over which to calculate the metrics.
        """
        metrics = self.get_metrics(self.last_updates[delay], duration, delay)
        if metrics:
            _, codes_count, max_elapsed, avg_elapsed = metrics
            self.metrics_sem.acquire()
            self.last_updates[delay] = time.time()
            self.metrics[delay] = {'time': time.time(), 'codes_count': codes_count, 'max_elapsed': max_elapsed,
                                   'avg_elapsed': avg_elapsed}
            self.is_read[delay] = False
            self.metrics_sem.release()

    def update_availability(self):
        """
        calculates the availability and stores it.
        """
        metrics = self.get_metrics(self.last_updates[120], 120, 120)
        if metrics:
            availability, _, _, _ = metrics
            self.metrics_sem.acquire()
            self.is_read[120] = False
            t = time.time()
            #  If it is available but was unavailable during the previous check
            if availability >= 0.8 and self.unavailable_since:
                self.unavailable_since = None
                self.recovered_at = t
            elif availability < 0.8:
                #  If it has recovered during the previous check
                if self.recovered_at:
                    self.unavailable_since = t
                    self.recovered_at = None
                #  If this is the first time it goes down
                elif not self.unavailable_since:
                    self.unavailable_since = t
            self.last_updates[120] = t
            self.metrics[120] = {'time': t, 'availability': availability}
            if self.unavailable_since:
                self.metrics[120]['unavailable_since'] = self.unavailable_since
            if self.recovered_at:
                self.metrics[120]['recovered_at'] = self.recovered_at
            self.metrics_sem.release()

    def get_metrics(self, end, duration, delay):
        """
        get the metrics over the specified time window ending at **end**

        :note: To make sure all the responses have been received, we shift our window with **self.timeout**,
            so the window doesn't effectively end at **end**


        :param end: the end of the lookup window
        :param duration: the duration of the window
        :param delay: the delay between two lookups
        """
        responses = self.request_scheduler.results.get_slice(end + delay - duration - self.timeout,
                                                             end + delay - self.timeout)
        #  If the user sets the request interval too high, responses could be empty
        if responses:
            _, status_codes, elapsed = zip(*responses)
            codes_count = Counter(status_codes)
            max_elapsed = max(elapsed)
            avg_elapsed = sum(elapsed) / len(elapsed)
            availability = sum([codes_count[k] for k in codes_count.keys() if k < 400]) / len(responses)
            return availability, codes_count, max_elapsed, avg_elapsed

    def read_metrics(self):
        """
        Returns the unread metrics and marks them as read. The returned metrics are sorted for logging.

        :return: list
        """
        self.metrics_sem.acquire()
        metrics_dict = {}
        for k in [10, 60, 120]:
            if not self.is_read[k]:
                metrics_dict[k] = self.metrics[k]
                self.is_read[k] = True
        self.metrics_sem.release()
        metrics = sorted(metrics_dict.items(), key=lambda x: x[1]['time'])
        return metrics
