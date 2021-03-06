from threading import Thread
from src.site_monitor import SiteMonitor, EXCEPTION_RAISED
import time
from src.user_interface import UserInterface
from src.utils import get_local_time
import os
import logging

logger = logging.getLogger()


class GlobalMonitor:
    """
    The class that monitors the different websites, formats the metrics and outputs them to screen.

    :param list sites: the list of websites to monitor. Each element is of the format **(interval, utl, timeout)**
    :ivar dict site_monitors: the dict containing the different websites and their :class:`site_monitor.SiteMonitor`
    :ivar dict metrics: the latest metrics retrieved for each website, sorted by time
        contains the last 1000 of each retrieved stat
    """

    def __init__(self, sites, logs_path="./logfiles"):
        self.site_monitors = {}
        self.metrics = {}
        self.cum_metrics = {}
        self.set_stop = False
        self.logs_path = logs_path
        self.sites = sites
        self.ui = None
        for site in sites:
            self.site_monitors[site] = SiteMonitor(*site)
        self.writer = Writer(self.site_monitors, logs_path)
        if not os.path.isdir(logs_path):
            os.mkdir(logs_path)

    def start(self, screen):
        """
        Start monitoring the websites and show the data on the terminal.
        :param screen: reference to the curses screen
        """
        logger.info("Main Started created")
        t = time.time()
        self.ui = UserInterface(self.sites, screen)
        self.writer.start()
        for monitor in self.site_monitors.values():
            monitor.start()
        try:
            while not self.set_stop:
                # Stops the execution if one of the children thread has an exception
                if EXCEPTION_RAISED:
                    self.stop()
                else:
                    metrics = {}
                    if time.time() - t > 1:
                        self.update_metrics()
                        self.log()
                        metrics = self.metrics
                        t = time.time()
                    # We could the returned value to add more features, like adding/removing sites to monitor at runtime
                    val = self.ui.update_and_display(metrics)
                    if val == 'q':
                        self.stop()
                    time.sleep(0.01)
        except Exception as e:
            self.stop()
            raise e

    def stop(self):
        """
        Stops the monitoring.
        """
        self.ui.stop()
        self.writer.stop()
        for monitor in self.site_monitors.values():
            monitor.stop()
        self.set_stop = True
        logger.info("Main Monitorer set to stop")

    def update_metrics(self):
        logger.info("Metrics updated")
        # for every site
        for site, monitor in self.site_monitors.items():
            self.metrics[site] = monitor.read_metrics()

    def log(self):
        """
        Logs the metrics in the appropriate file after formatting it
        """
        for site, monitor in self.site_monitors.items():
            total_metrics = monitor.read_metrics()
            for duration, metric in total_metrics:
                name, _, interval, _ = site
                interval = str(interval).replace('.', '')
                path = os.path.join(self.logs_path, name + '_' + str(interval) + '.txt')
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


class Writer(Thread):
    """
    A class to write the detailed stats to disk
    """

    def __init__(self, site_monitors, logs_path):
        super().__init__()

        self.site_monitors = site_monitors
        self.logs_path = logs_path
        self.set_stop = False

    def run(self):
        global EXCEPTION_RAISED
        t = time.time()
        try:
            while not self.set_stop:
                if EXCEPTION_RAISED:
                    self.stop()
                else:
                    if time.time() - t > 10:
                        for site, monitor in self.site_monitors.items():
                            responses = monitor.request_scheduler.results.get_slice(t - 10, t)
                            t = time.time()
                            name = os.path.join(self.logs_path, site[0] + '_raw.txt')
                            with open(name, 'a') as f:
                                f.writelines(["%s %s %s\n" % x for x in responses])
                    time.sleep(1)
        except Exception as e:
            EXCEPTION_RAISED = True
            raise e

    def stop(self):
        self.set_stop = True
