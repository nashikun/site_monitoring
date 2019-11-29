from site_monitor import SiteMonitor
from fixed_size import FixedSizeList
from collections import defaultdict
import math
import time
from datetime import datetime
import curses


class MainMonitor:
    """
    The class that monitors the different websites, formats the metrics and outputs them to screen.

    :param list sites: the list of websites to monitor. Each element is of the format **(interval, utl, timeout)**
    :ivar dict site_monitors: the dict containing the different websites and their :class:``site_monitor.SiteMonitor`
    :ivar dict metrics: the latest metrics retrieved for each website, sorted by time
    :ivar dict cum_metrics: for each site contains a dict, which for each time-frame,
        contains the last 1000 of each retrieved stat
    """

    def __init__(self, sites):
        self.site_monitors = {}
        self.metrics = {}
        self.cum_metrics = {}
        self.set_stop = False
        self.screen = curses.initscr()
        for site in sites:
            self.site_monitors[site] = SiteMonitor(*site)
            self.cum_metrics[site] = {k: defaultdict(lambda: FixedSizeList(1000)) for k in [10, 60, 120]}

    def start(self):
        """
        Start monitoring the websites and show the data on the terminal.
        """
        for monitor in self.site_monitors.values():
            monitor.start()
        while not self.set_stop:
            self.update_metrics()
            time.sleep(1)

            # TODO DEBUG LOOOOOOOOOOOOOGS

    def stop(self):
        """
        Stops the monitoring.
        """
        for monitor in self.site_monitors.values():
            monitor.stop()
        self.set_stop = True

    @staticmethod
    def plot_console(array, min_val, max_val, step, repeats):
        """
        Draws an input array in ascii

        :param list array: the array to plot
        :param int min_val: the minimum value to plot. Any lower value will be clamped
        :param int max_val: the maximum value to plot. Any higher value will be clamped
        :param float step: the difference between 2 different levels in the plot.
        :param int repeats: The length of each character on the x-axis
        :return: A list containing each line as a string.
        :rtype: list
        """
        m = len(array)
        n = math.ceil((max_val - min_val) / step + 1)
        # The characters used to draw our plot
        chars = {
            0: ' ' * repeats,
            1: '|' + ' ' * (repeats - 1),
            2: '|' + '_' * (repeats - 1),
            3: '_' * repeats,
            4: ' ' + '_' * (repeats - 1)
        }
        # initial value for b
        b = min(max(round((array[0] - min_val) / step), 0), n)
        plot = [[' ' * repeats for _ in range(m)] for _ in range(n)]
        for i in range(m - 1):
            # counts the number of characters we should draw to get to the next value,
            # then clamps it not to exceed the upper edge
            a = b
            b = min(max(round((array[i + 1] - min_val) / step), 0), n)
            start, end = sorted((a, b))
            for j in range(start, end):
                plot[n - 1 - j][i] = chars[1]
            if plot[n - 1 - b][i] == chars[1]:
                plot[n - 1 - b][i] = chars[2]
            elif a == b:
                plot[n - 1 - b][i] = chars[3]
            else:
                plot[n - 1 - b][i] = chars[4]
        return [''.join(row) for row in plot]

    def update_metrics(self):
        # for every site
        for site, monitor in self.site_monitors.items():
            total_metrics = monitor.read_metrics()
            self.metrics[site] = total_metrics
            #  for every time-frame
            for duration, metric in total_metrics:
                self.log(site, duration, metric)
                # for every retrieved metric
                for key, val in metric.items():
                    self.cum_metrics[site][duration][key].add(val)

    def log(self, site, duration, metric):
        """

        :param site: the site data
        :param duration: the delay between two updates of the metric
        :param metric:
        :return:
        """
        # TODO remove the hash and replace the url by a valid name instead
        #   Delay is the (user defined) delay between two consecutive requests
        delay, url, _ = site
        with open(f'./logs/{hash(url)}_{delay}', 'a') as file:
            t = datetime.utcfromtimestamp(int(metric['time'])).strftime('%Y-%m-%d %H:%M:%S')
            if duration == 120:
                file.write(f"[{t}] Website availability is {metric['availability']}\n")
                if 'unavailable_since' in metric.keys():
                    rt = datetime.utcfromtimestamp(int(metric['unavailable_since'])).strftime('%Y-%m-%d %H:%M:%S')
                    file.write(f"[{t}] Website is unavailable since {rt}\n")
                elif 'recovered_at' in metric.keys():
                    rt = datetime.utcfromtimestamp(int(metric['recovered_at'])).strftime('%Y-%m-%d %H:%M:%S')
                    file.write(f"[{t}] Website recovered at {rt}\n")
            else:
                codes = " ,".join([f"{k} : {v}" for k, v in metric['codes_count'].items()])
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
                    f"[{t}] The response code counts for the last {duration} seconds is {codes}\n")
