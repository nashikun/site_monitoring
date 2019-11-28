import time
from collections import Counter
from threading import Thread
import requests
from operator import itemgetter
from FixedSizeQueue import FixedSizeQueue


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


class Requester(Thread):

    def __init__(self, url, queue, timeout):
        super(Requester, self).__init__()
        self.url = url
        self.queue = queue
        self.timeout = timeout

    def run(self):
        t = time.time()
        try:
            response = requests.get(self.url, timeout=self.timeout)
            self.queue.add((t, response.status_code, time.time() - t))
        except requests.exceptions.ConnectionError:
            self.queue.add((t, 503, time.time() - t))
        except requests.exceptions.ReadTimeout:
            self.queue.add((t, 408, self.timeout))


class SiteMonitor(Thread):

    def __init__(self, interval, url, timeout):
        super(SiteMonitor, self).__init__()
        self.request_scheduler = RequestScheduler(interval, url, timeout)
        self.timeout = timeout
        self.availability = []
        self.codes_count = [{} for _ in range(3)]
        self.max_elapsed = [-1 for _ in range(3)]
        self.avg_elapsed = [-1 for _ in range(3)]
        self.unavailable_since = None
        self.recovered_at = None
        self.last_updates = []
        self.set_stop = False

    def stop(self):
        self.request_scheduler.stop()
        self.set_stop = True

    def run(self):
        self.request_scheduler.start()
        self.last_updates = [time.time()] * 3
        while not self.set_stop:
            if time.time() - self.last_updates[0] > 10:
                self.update_metrics(0, 600, 10)
            if time.time() - self.last_updates[1] > 60:
                self.update_metrics(1, 3600, 60)
            if time.time() - self.last_updates[2] > 120:
                self.update_availability()
            time.sleep(0.01)

    def update_metrics(self, idx, duration, delay):
        _, codes_count, max_elapsed, avg_elapsed = self.get_metrics(self.last_updates[idx], duration, delay)
        self.last_updates[idx] = time.time()
        self.codes_count[idx] = codes_count
        self.max_elapsed[idx] = max_elapsed
        self.avg_elapsed[idx] = avg_elapsed

    def update_availability(self):
        availability, _, _, _ = self.get_metrics(self.last_updates[2], 120, 120)
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
        self.last_updates[2] = t
        self.availability.append(availability)

    def get_metrics(self, end, duration, delay):
        # print(end + delay - duration - self.timeout, end + delay - self.timeout, time.time())
        responses = self.request_scheduler.results.get_slice(end + delay - duration - self.timeout,
                                                             end + delay - self.timeout)
        _, status_codes, elapsed = zip(*responses)
        codes_count = Counter(status_codes)
        max_elapsed = max(elapsed) / 1000000
        avg_elapsed = sum(elapsed) / len(elapsed) / 1000000
        availability = sum([codes_count[k] for k in codes_count.keys() if k < 400]) / len(responses)
        return availability, codes_count, max_elapsed, avg_elapsed


if __name__ == '__main__':
    from asciimatics.screen import Screen
    from asciimatics.scene import Scene
    from asciimatics.effects import Cycle, Stars
    from asciimatics.renderers import FigletText


    def demo(screen):
        i = 0
        while i < 10:
            screen.print_at('Hello world!, time is %s' % time.time(), 0, 0)
            screen.refresh()
            time.sleep(1)
            i += 1


    Screen.wrapper(demo)

# TODO Add documentation. Don't forget params
##
