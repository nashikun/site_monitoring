import curses
import math
from collections import defaultdict
from datetime import datetime
import logging

logger = logging.getLogger()


class UserInterface:
    """
    The class that renders everything on screen.

    :ivar screen: a reference to the curses screen object.
    :ivar list sites: stores the monitored websites
    :ivar defaultdict stored_info: contains the string containing the metrics for each pair site
    :ivar defaultdict stored_plot: contains the plot for each pair (site, delay)
    :ivar defaultdict cum_metrics: contains the last few retrieved metrics
    :ivar defaultdict changed: remembers whether a (site, delay) s plot and info have been changed since the last update
    :ivar int cursor: the number of the page to render
    :ivar int max_cursor: the maximum value the cursor could have
    :ivar bool set_stop: whether the program should quit
    """

    def __init__(self, sites, screen):
        # Used defaultdict instead of dicts to allow adding / removing sites at run time later without much issues
        self.screen = screen
        self.h, self.w = self.screen.getmaxyx()
        self.init_curses()
        self.sites = sites
        self.stored_info = defaultdict(list)
        self.stored_plot = defaultdict(list)
        self.stored_metrics = defaultdict(lambda: defaultdict(lambda: None))
        self.cum_metrics = defaultdict(lambda: defaultdict(list))
        self.changed = defaultdict(lambda: True)
        self.current_page = 0
        self.cursor = 0
        self.max_cursor = len(sites)
        self.set_stop = False

    def init_curses(self):
        """
        Initiates the screen with the right settings.
        """
        self.screen.keypad(1)
        self.screen.timeout(10)
        curses.noecho()
        curses.curs_set(0)
        curses.cbreak()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

    def update_and_display(self, metrics):
        """
        Updates the UI's data and renders the screen
        :param metrics:
        """
        for site, metric in metrics.items():
            self.changed[(1, site)] = True
            self.changed[(2, site)] = True
            for delay, values in metric:
                # This is to avoid having both unavailable_since and recovered_at set at the same time
                self.stored_metrics[(site, delay)]['unavailable_since'] = None
                self.stored_metrics[(site, delay)]['recovered_at'] = None
                for k, v in values.items():
                    self.stored_metrics[(site, delay)][k] = v
                    self.cum_metrics[(site, delay)][k].append(v)
        #  Clears the screen and reads key presses
        self.get_keypress()
        self.screen.erase()
        # If screen is resized, update the height and width
        if curses.is_term_resized(self.h, self.w):
            self.h, self.w = self.screen.getmaxyx()
        # renders the current page
        if self.current_page == 0:
            self.welcome_screen()
        elif self.current_page == 1:
            self.summary_screen()
        else:
            self.site_info()

    def get_keypress(self):
        """
        Reads the user input and initiates the right actions
        """
        ch = self.screen.getch()
        if ch == curses.KEY_UP:
            self.cursor = max(self.cursor - 1, 0)
        elif ch == curses.KEY_DOWN:
            self.cursor = min(self.cursor + 1, self.max_cursor)
        elif ch == ord('q') or ch == ord('Q'):
            self.set_stop = True
            curses.endwin()
        elif ch == ord('h') or ch == ord('H'):
            self.cursor = 0
            self.current_page = 0
        elif ch == curses.KEY_ENTER or ch == 10 or ch == 13:
            if not self.current_page:
                self.current_page = self.cursor + 1
                self.cursor = 0

    def welcome_screen(self):
        """
        Renders the screen for the main menu
        """
        #  If this screen has been changed (as in a new website has been added), recalculate the string
        if self.changed[0]:
            text = [" ________________", "|                |", "|                |", "| Site Monitorer |",
                    "|                |", "|________________|", "", "Please choose an option:", "0001 - Summary"]
            text.extend([f"{idx + 2:04d} - {site[0].upper()}" for idx, site in enumerate(self.sites)])
            self.changed[0] = False
            self.stored_info[0] = text

        welcome_message = self.stored_info[0]
        for idx, line in enumerate(welcome_message):
            #  If part of the header
            if idx < 7:
                self.screen.addstr(idx, round(self.w / 2) - 8, line)
            #   Print the instruction
            elif idx == 7:
                self.screen.addstr(idx, 5, line)
            #   Print the list
            else:
                if self.cursor + 8 == idx:
                    self.screen.addstr(1 + idx, 7, line, curses.color_pair(1))
                else:
                    self.screen.addstr(1 + idx, 7, line)
        self.max_cursor = len(self.sites)
        #  Render
        self.screen.refresh()

    def summary_screen(self):
        """
        Renders the summary screen
        """
        separator = "_" * (self.w - 10)
        full_text = []
        for site in self.sites:
            #   Recalculate the site string and store if needed
            if self.changed[(1, site)]:
                self.update_site_info(site)
            #  Add the string to the full text
            full_text.extend(self.stored_info[site])
            full_text.append(separator)

        self.max_cursor = max(len(full_text) - self.h, 0)

        for i in range(self.cursor, min(self.cursor + self.h, len(full_text) - 1)):
            self.screen.addstr(i - self.cursor, 5, full_text[i])
        self.screen.refresh()

    def site_info(self):
        """
        Renders the infos screen
        """
        site = self.sites[self.current_page - 2]
        if self.changed[(1, site)]:
            self.update_site_info(site)
        if self.changed[(2, site)]:
            self.update_plot(site)
        #  text = self.stored_info[site] + self.stored_plot[(site, 10)]
        text = self.stored_plot[(site, 10)]
        self.max_cursor = max(len(text) - self.h, 0)

        for i in range(self.cursor, min(self.cursor + self.h, len(text) - 1)):
            self.screen.addstr(i - self.cursor, 5, text[i])
        self.screen.refresh()

    def update_plot(self, site):
        """
        Updates the plots stored in memory

        :param site: the site to update
        """
        for delay in [10, 60]:
            metrics = self.cum_metrics[(site, delay)]['max_elapsed']
            if metrics:
                min_val = max(metrics)
                max_val = min(metrics)
                if len(metrics) < 5 or min_val == max_val:
                    self.stored_plot[(site, delay)] = self.array_to_plot([0] + metrics, 0, 1, 0.1, 3)
                else:
                    step = (max_val - min_val) / 10
                    self.stored_plot[(site, delay)] = self.array_to_plot(metrics, min_val, max_val, step, 3)
        self.changed[(2, site)] = False

    def update_site_info(self, site):
        """
        Updates the info string stored in memory

        :param site: the site to update
        """
        text = []
        # The header
        text.extend([f"Website : {site[0]}", "", f"Pinged every : {site[2]:10.2f} seconds", "",
                     "Over the last 2 minutes   :", ])
        #  The availability stats
        data = self.stored_metrics[(site, 120)]
        availability = data["availability"]
        if availability is None:
            text.append(f"    Availability          : --,--%"),
        else:
            text.append(f"    Availability          : {100 * availability:10.2f}%"),
        unavailable_since = data['unavailable_since']
        recovered_at = data['recovered_at']
        if unavailable_since:
            t = datetime.utcfromtimestamp(int(data['unavailable_since'])).strftime('%Y-%m-%d %H:%M:%S')
            text.append(f"    Website is down since : {t}"),
        elif recovered_at:
            t = datetime.utcfromtimestamp(int(data['recovered_at'])).strftime('%Y-%m-%d %H:%M:%S')
            text.append(f"    Website recovered at  : {t}", ),

        #   The stats over the last 10 minutes
        data = self.stored_metrics[(site, 10)]

        if not data:
            text.extend(["", "Over the last 10 minutes  :", f"    Average Response Time : --",
                         f"    Maximum Response Time : --", ])
        else:
            text.extend([
                "", "Over the last 10 minutes:",
                f"    Average Response Time : {int(1000 * data['avg_elapsed'])} ms",
                f"    Maximum Response Time : {int(1000 * data['max_elapsed'])} ms",
                f"    Response Code Count   :", ])
            text.extend([f"         {k} : {v}" for k, v in data['codes_count'].items()])

        #   The stats over the last hour
        data = self.stored_metrics[(site, 60)]
        if not data:
            text.extend(["", "Over the last 60 minutes:", f"    Average Response Time : --",
                         f"    Maximum Response Time : --"])
        else:
            text.extend(["", "Over the last 60 minutes:",
                         f"    Average Response Time : {int(1000 * data['avg_elapsed'])} ms",
                         f"    Maximum Response Time : {int(1000 * data['max_elapsed'])} ms",
                         f"    Response Code Count:", ])
            text.extend([f"         {k} : {v}" for k, v in data['codes_count'].items()])
        self.stored_info[site] = text
        self.changed[(1, site)] = False

    @staticmethod
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

# TODO Add a semaphore or something to protect access to data
#   Add scrolling to the main menu
