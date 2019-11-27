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
        while not self.set_stop:
            req = Requester(self.url, self.results, self.timeout)
            req.start()
            time.sleep(self.interval)

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
            self.queue.add((t, response.status_code, time.time()-t))
        except requests.exceptions.ConnectionError:
            self.queue.add((t, 503, time.time()-t))
        except requests.exceptions.ReadTimeout:
            self.queue.add((t, 408, self.timeout))


class SiteMonitor:

    def __init__(self, interval, url, timeout):
        self.request_scheduler = RequestScheduler(interval, url, timeout)
        self.availability = []
        self.codes_count = [{} for _ in range(3)]
        self.max_elapsed = [-1 for _ in range(3)]
        self.avg_elapsed = [-1 for _ in range(3)]
        t = time.time()
        self.last_updates = [t] * 3

    def run(self):
        self.request_scheduler.start()
        while True:
            t = time.time()
            time.sleep(0.1)
            if time.time() - t > 10:
                self.update_metrics(0, 600)
            if time.time() - t > 60:
                self.update_metrics(0, 3600)

            if time.time() - t > 120:
                self.update_metrics(1, t)
            if time.time() - t > 600:
                self.update_metrics(2, t)

    def update_metrics(self, idx, duration):
        availability, codes_count, max_elapsed, avg_elapsed = self.get_metrics(self.last_updates[idx], duration)
        self.last_updates[idx] = time.time()
        if duration == 120:
            self.availability.append(availability)
        self.codes_count[idx] = codes_count
        self.max_elapsed[idx] = max_elapsed
        self.avg_elapsed[idx] = avg_elapsed

    def get_metrics(self, start, duration):
        responses = self.request_scheduler.results.get_slice(start, start + duration)
        _, status_codes, elapsed = zip(*responses)
        codes_count = Counter(status_codes)
        max_elapsed = max(elapsed) / 1000000
        avg_elapsed = sum(elapsed) / len(elapsed) / 1000000
        availability = sum([codes_count[k] for k in codes_count.keys() if k < 400]) / len(responses)
        return availability, codes_count, max_elapsed, avg_elapsed


if __name__ == '__main__':
    scheduler = RequestScheduler(1, 'http://google.com', 5)
    t = time.time()
    scheduler.start()
    time.sleep(6)
    scheduler.stop()
    time.sleep(6)
    time_slice = scheduler.results.get_slice(t, t + 6)
    print(time_slice)



##
