import time
from site_monitor import SiteMonitor


class MainMonitor:

    def __init__(self, sites):
        self.site_monitors = []
        for site in sites:
            self.site_monitors.append(SiteMonitor(*site))

    def start(self):
        for monitor in self.site_monitors:
            monitor.start()


if __name__ == '__main__':
    from asciichartpy import plot

    monitor = SiteMonitor(0.1, 'http://localhost:4444/delay?increment=0.1&reset_after=60', 5)
    t = time.time()
    monitor.start()
    res_1 = []
    res_2 = []
    for _ in range(30):
        time.sleep(11)
        print(monitor.avg_elapsed)
        res_1.append(int(10 * monitor.avg_elapsed[0]))
        res_2.append(int(10 * monitor.max_elapsed[0]))
    monitor.stop()
    time.sleep(5)
    print(plot(res_1))

# TODO Add documentation. Don't forget params
##
