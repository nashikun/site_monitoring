import time
from collections import defaultdict

from fixed_size import FixedSizeQueue, FixedSizeList
from site_monitor import SiteMonitor


class MainMonitor:

    def __init__(self, sites):
        self.site_monitors = {}
        self.metrics = {}
        self.cum_metrics = {}
        self.set_stop = False
        for site in sites:
            self.site_monitors[site] = SiteMonitor(*site)
            self.cum_metrics[site] = defaultdict(lambda: FixedSizeList(1000))

    def start(self):
        for monitor in self.site_monitors.values():
            monitor.start()
        while not self.set_stop:
            for site, monitor in self.site_monitors.items():
                metrics = monitor.read_metrics()
                self.metrics[site] = metrics
                for key, val in metrics.items():
                    self.cum_metrics[site][key].add(val)
            print(self.metrics)
            time.sleep(0.1)

    def stop(self):
        for monitor in self.site_monitors.values():
            monitor.stop()
        self.set_stop = True


if __name__ == '__main__':
    from asciichartpy import plot

    mon = MainMonitor([(0.1, 'http://cdiscount.com', 5)])
    t = time.time()
    mon.start()

# TODO Add documentation. Don't forget params
#
