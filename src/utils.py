from tzlocal import get_localzone
from datetime import datetime
import time
import requests
import math
from threading import Thread

"""
This module is for the different simple reusable classes and functions 
"""

local_tz = get_localzone()


def get_local_time(timestamp):
    """
    Converts time from unix time to a :class:`datetime` object representing time in the current time-zone

    :param timestamp: the unix time stamp
    :return: the time in the current timezone
    """
    return local_tz.localize(datetime.fromtimestamp(timestamp))


def get_sites(file_path):
    """
    Reads the sites from an input file and returns the list of websites if no exceptions are raise.

    :param file_path: The path to read from
    :return: The list of websites to monitor
    """
    s = []
    names = set()
    try:
        with open(file_path, 'r') as file:
            lines = file.read().splitlines()
        for idx, line in enumerate(lines):
            name, url, delay, timeout = line.split(',')
            if name in names:
                raise Exception('Names should be unique')
            names.add(name)
            s.append((name, url.strip(), float(delay), float(timeout)))
        return s
    except FileNotFoundError:
        raise Exception('Could not find the file at the specified path. Please enter a valid location')
    except (TypeError, ValueError):
        raise Exception(f"Error at line {idx} of the input file. Format should be 'name, url, delay, timeout'")


def array_to_plot(array, min_val, max_val, step, repeats):
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
        0: '#' * repeats,
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
        |  If connection to the site fails, the status code is 503
        |  If the connection succeeds but times out, the status code is 408

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
