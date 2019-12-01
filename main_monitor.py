from site_monitor import SiteMonitor
import time

from UI import UserInterface
from utils import get_local_time
import os
import logging

logger = logging.getLogger()


class MainMonitor:
    """
    The class that monitors the different websites, formats the metrics and outputs them to screen.

    :param list sites: the list of websites to monitor. Each element is of the format **(interval, utl, timeout)**
    :ivar dict site_monitors: the dict containing the different websites and their :class:``site_monitor.SiteMonitor`
    :ivar dict metrics: the latest metrics retrieved for each website, sorted by time
        contains the last 1000 of each retrieved stat
    """

    def __init__(self, sites, logs_path="./logs"):
        self.site_monitors = {}
        self.metrics = {}
        self.cum_metrics = {}
        self.set_stop = False
        self.logs_path = logs_path
        self.sites = sites
        self.ui = None
        for site in sites:
            self.site_monitors[site] = SiteMonitor(*site)
        if not os.path.isdir(logs_path):
            os.mkdir(logs_path)

    def start(self, screen):
        """
        Start monitoring the websites and show the data on the terminal.
        """
        logger.info("Main Started created")
        t = time.time()
        self.ui = UserInterface(self.sites, screen)
        for monitor in self.site_monitors.values():
            monitor.start()
        while not self.set_stop:
            metrics = {}
            if time.time() - t > 1:
                self.update_metrics()
                metrics = self.metrics
                t = time.time()
            logger.error(str(metrics))
            self.ui.update_and_display(metrics)
            if self.ui.set_stop:
                self.stop()
            time.sleep(0.01)

    def stop(self):
        """
        Stops the monitoring.
        """
        for monitor in self.site_monitors.values():
            monitor.stop()
        self.set_stop = True

    def update_metrics(self):
        logger.info("Metrics updated")
        # for every site
        for site, monitor in self.site_monitors.items():
            total_metrics = monitor.read_metrics()
            self.metrics[site] = total_metrics
            #  for every time-frame
            for duration, metric in total_metrics:
                self.log(site, duration, metric)

    def log(self, site, duration, metric):
        """

        :param site: the site data
        :param duration: the delay between two updates of the metric
        :param metric:
        """
        #   Delay is the (user defined) delay between two consecutive requests
        name, _, delay, _ = site
        delay = str(delay).replace('.', '')
        path = os.path.join(self.logs_path, name + '_' + str(delay) + '.txt')
        with open(path, 'a') as file:
            t = get_local_time(metric['time']).strftime('%Y-%m-%d %H:%M:%S')
            if duration == 120:
                file.write(f"[{t}] Website availability is {100 * metric['availability']:10.0f}%\n")
                if 'unavailable_since' in metric.keys():
                    rt = get_local_time(metric['unavailable_since']).strftime('%Y-%m-%d %H:%M:%S')
                    file.write(f"[{t}] Website is unavailable since {rt}\n")
                elif 'recovered_at' in metric.keys():
                    rt = get_local_time(metric['recovered_at']).strftime('%Y-%m-%d %H:%M:%S')
                    file.write(f"[{t}] Website recovered at {rt}\n")
            else:
                codes = "{" + " ,".join([f"{k} : {v}" for k, v in metric['codes_count'].items()]) + " }"
                if duration == 10:
                    wait = 60
                elif duration == 60:
                    wait = 600
                else:
                    raise ValueError("Unexpected Error. Duration is either 10, 60 or 120 seconds")
                file.write(
                    f"[{t}] The average response time for the last {wait} seconds is {metric['avg_elapsed']:10.2f}\n")
                file.write(
                    f"[{t}] The maximum response time for the last {wait} seconds is {metric['max_elapsed']:10.2f}\n")
                file.write(
                    f"[{t}] The response codes counts for the last {wait} seconds is {codes}\n")
