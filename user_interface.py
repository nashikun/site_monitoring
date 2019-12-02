import curses
from collections import defaultdict
from operator import itemgetter
from utils import get_local_time, array_to_plot
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
    :ivar defaultdict availability_changes: for each website, stores when it went down or recovered
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
        self.availability_changes = defaultdict(list)
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
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

    def stop(self):
        """
        Stops the user interface and restores the terminal
        """
        self.set_stop = True
        curses.endwin()

    def update_and_display(self, metrics):
        """
        Updates the UI's data and renders the screen

        :param metrics:
        """
        for site, metric in metrics.items():
            self.changed[(1, site)] = True
            self.changed[(2, site)] = True
            self.changed[(3, site)] = True
            for delay, values in metric:
                # This is to avoid having both unavailable_since and recovered_at set at the same time
                self.stored_metrics[(site, delay)]['unavailable_since'] = None
                self.stored_metrics[(site, delay)]['recovered_at'] = None
                for k, v in values.items():
                    self.stored_metrics[(site, delay)][k] = v
                    self.cum_metrics[(site, delay)][k].append(v)
        #  Clears the screen and reads key presses
        res = self.get_keypress()
        self.screen.erase()
        # If screen is resized, update the height and width
        if curses.is_term_resized(self.h, self.w):
            self.h, self.w = self.screen.getmaxyx()
        # renders the current page
        if self.current_page == 0:
            self.welcome_screen()
        elif self.current_page == 1:
            self.summary_screen()
        elif self.current_page == 2:
            self.log_screen()
        else:
            self.site_info()
        return res

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
            return 'q'
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
        The text is as follow:

        .. aafig::
            :textual:

                 ________________
                |                |
                |                |
                | Site Monitorer |
                |                |
                |________________|

        Please choose an option:

        |  0001 - Summary
        |  0002 - Logs
        |  0003 - site 1
        |  0004 - site 2

        """
        #  If this screen has been changed (as in a new website has been added), recalculate the string
        if self.changed[0]:
            text = [" ________________", "|                |", "|                |", "| Site Monitorer |",
                    "|                |", "|________________|", "", "Please choose an option:", "", "0001 - Summary",
                    "0002 - Logs"]
            text.extend([f"{idx + 3:04d} - {site[0]}" for idx, site in enumerate(self.sites)])
            self.changed[0] = False
            self.stored_info[0] = text
        welcome_message = self.stored_info[0]
        curs = max(self.cursor - self.h + 10, 0)
        for i in range(curs, min(curs + self.h, len(welcome_message))):
            #  If part of the header
            if i < 7:
                self.screen.addstr(i - curs, round(self.w / 2) - 8, welcome_message[i])
            #   Print the instruction
            elif i == 7:
                self.screen.addstr(i - curs, 5, welcome_message[i])
            #   Print the list
            else:
                if self.cursor + 9 == i:
                    self.screen.addstr(i - curs, 7, welcome_message[i], curses.color_pair(1))
                else:
                    self.screen.addstr(i - curs, 7, welcome_message[i])
        self.max_cursor = max(len(self.sites) + 1, 0)
        #  Render
        self.screen.refresh()

    def summary_screen(self):
        """
        Renders the summary screen.
        The layout is as follows:

        .. aafig::
            :textual:

            site 1 info block
            _________________________

            site 2 info block
            _________________________

            site 3 info block


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
        Renders the infos screen.
        """
        # Updates the info
        site = self.sites[self.current_page - 3]
        if self.changed[(1, site)]:
            self.update_site_info(site)
        if self.changed[(2, site)]:
            self.update_plot(site)
        if self.changed[(3, site)]:
            self.update_availability(site)
        # Add the info text
        text = self.stored_info[site][:]
        # Add the plots
        if self.stored_plot[(site, 10)]:
            text.extend(["", "", "The maximum response time over the last 60 s", "", *self.stored_plot[(site, 10)][0],
                         "", "The average response time over the last 60 s", "", *self.stored_plot[(site, 10)][1], ""])
        if self.stored_plot[(site, 60)]:
            text.extend(
                ["", "", "The maximum response time over the last 60 min", "", *self.stored_plot[(site, 60)][0],
                 "", "The average response time over the last 60 min", "", *self.stored_plot[(site, 60)][1], ""])
        if self.stored_plot[(site, 120)]:
            text.extend(
                ["", "", "The availability evolution:", "", *self.stored_plot[(site, 120)][0]])
        #  Add the logs
        availability = sorted(self.availability_changes[site], key=itemgetter(2))
        if not availability:
            text.append("The website didn't go down.")
        else:
            for data in availability:
                site, stat, res = data
                if res:
                    if stat == 'unavailable_since':
                        text.append(f"""site "{site[0]}" is unavailable since"""
                                    f" {get_local_time(res).strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        text.append(f"""site "{site[0]}" recovered at"""
                                    f" {get_local_time(res).strftime('%Y-%m-%d %H:%M:%S')}")

        self.max_cursor = max(len(text) - self.h, 0)
        for i in range(self.cursor, min(self.cursor + self.h, len(text))):
            self.screen.addstr(i - self.cursor, 5, text[i])
        self.screen.refresh()

    def log_screen(self):
        """
        Renders the log screen
        """
        for site in self.sites:
            if self.changed[(3, site)]:
                self.update_availability(site)
        availability = sorted([x for v in self.availability_changes.values() for x in v], key=itemgetter(2))
        self.max_cursor = max(len(availability) - self.h, 0)
        if not availability:
            self.screen.addstr(0, 5, "No website went down.", curses.color_pair(2))
        else:
            for i in range(self.cursor, min(self.cursor + self.h, len(availability))):
                site, stat, res = availability[i]
                if res:
                    if stat == 'unavailable_since':
                        self.screen.addstr(i - self.cursor, 5,
                                           f"""site "{site[0]}" is unavailable since"""
                                           f" {get_local_time(res).strftime('%Y-%m-%d %H:%M:%S')}",
                                           curses.color_pair(3))
                    else:
                        self.screen.addstr(i - self.cursor, 5,
                                           f"""site "{site[0]}" recovered at"""
                                           f" {get_local_time(res).strftime('%Y-%m-%d %H:%M:%S')}",
                                           curses.color_pair(2))

    def update_plot(self, site):
        """
        Updates the plots stored in memory

        :param site: the site to update
        """
        for delay in [10, 60, 120]:
            max_size = 10
            timestamps = self.cum_metrics[(site, delay)]['time'][-max_size:]
            if timestamps:
                if delay == 120:
                    metrics = self.cum_metrics[(site, delay)]['availability'][-max_size:]
                    self.stored_plot[(site, 120)] = [self.get_plot(timestamps, metrics, True, max_size)]
                else:
                    self.stored_plot[(site, delay)] = []
                    for stat in ['max_elapsed', 'avg_elapsed']:
                        metrics = self.cum_metrics[(site, delay)][stat][-max_size:]
                        self.stored_plot[(site, delay)].append(self.get_plot(timestamps, metrics, False, max_size))

        self.changed[(2, site)] = False

    # noinspection PyTypeChecker
    def update_site_info(self, site):
        """
        Updates the info string stored in memory.
        The layout is as follows:

        .. aafig::

            `Website:`
            `Url : `
            `Pinged every :`
            `Timeout:`
            `Over the last 2 mins:`
               `Availability                    : --,--%`
               `Website is down since           : ------------`
               `Website is is back online since : ------------`
            `Over the last 10 mins:`
               `Average Response Time : -----`
               `Maximum Response Time : -----`
               `Response Code Count:`
                    `--- : -----`
                    `--- : -----`
                    `--- : -----`
            `Over the last 60 mins:`
               `Average Response Time : -----`
               `Maximum Response Time : -----`
               `Response Code Count:`
                    `--- : -----`
                    `--- : -----`

        :param site: the site to update
        """
        # This is very unreadable. I just wrote a pattern in text editor and filled up the blanks as appropriate.
        # Not sure if there is a better way to do it

        text = []
        # The header
        text.extend([f"Website : {site[0]}", "", f"Pinged every : {site[2]:10.2f} seconds", f"Url : {site[1]}",
                     f"Timeout : {site[3]}", "",
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
            t = get_local_time(data['unavailable_since']).strftime('%Y-%m-%d %H:%M:%S')
            text.append(f"    Website is down since : {t}"),
        elif recovered_at:
            t = get_local_time(data['recovered_at']).strftime('%Y-%m-%d %H:%M:%S')
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

    def update_availability(self, site):
        for stat in ['unavailable_since', 'recovered_at']:
            res = self.stored_metrics[(site, 120)][stat]
            if res and (not self.availability_changes[site] or res != self.availability_changes[site][-1][2]):
                self.availability_changes[site].append((site, stat, res))
        self.changed[(3, site)] = False

    @staticmethod
    def get_plot(timestamps, metrics, is_availability, max_size):
        """
        Transforms an array to an ascii plot that can be shown on screen.
            For example, the array [6, 8, 16] with timestamps of [13:04:03 ,13:04:13, 13:04:23],
            a max_size of 10 where the y values represent time is printed as:

        .. aafig::

             `0016 ms` |                     _________
             `0015 ms` |                    |
             `0014 ms` |                    |
             `0013 ms` |                    |
             `0012 ms` |                    |
             `0011 ms` |                    |
             `0010 ms` |                    |
             `0009 ms` |                    |
             `0008 ms` |           _________|
             `0007 ms` |          |
             `0006 ms` |__________|
                       |______________________________
                   13:04:03        13:04:13        13:04:23

        :param list[float] timestamps: the timestamps for each value
        :param list metrics: the values to plot
        :param bool is_availability: whether the values should be interpreted as percentages or not,
            in which case they'll be interpreted as seconds
        :param max_size: the maximum number of values to plot.
        :return: the ascii plot where each element represents a line
        :rtype: list[str]
        """
        n = len(metrics)
        #  Get the settings for the plot
        max_val = max(metrics)
        min_val = min(metrics)
        if n < max_size:
            repeats = round(3 * max_size / n)
        else:
            repeats = 3
        if n < 2 or min_val == max_val:
            min_val = 0
            if not max_val:
                max_val = 1
            step = max_val / 10
        else:
            step = (max_val - min_val) / 10
        #  Get the plot
        plot = array_to_plot([metrics[0]] + metrics, min_val, max_val, step, repeats)
        m = len(plot)
        #   If we're plotting the availability evolution
        if is_availability:
            plot.append(" " * 11 + "|" + "_" * (3 * max_size))
            for i in range(m):
                plot[i] = f"{100 * (min_val + (m - 1 - i) * step) :5.1f} %    |" + plot[i]
        #  If we're plotting the response time evolution
        else:
            plot.append(" " * 10 + "|" + "_" * (3 * max_size))
            for i in range(m):
                plot[i] = f"{(1000 * (min_val + (m - 1 - i) * step)) :6.1f} ms |" + plot[i]
        if n == 1:
            time_axis = " " * (5 + 3 * max_size) + get_local_time(timestamps[0]).strftime('%H:%M:%S')
        elif n == 2:
            time_axis = " " * (2 + 3 * max_size // 2) + get_local_time(timestamps[0]).strftime(
                '%H:%M:%S') + " " * (3 * max_size // 2 - 2) + get_local_time(timestamps[-1]).strftime(
                '%H:%M:%S')
        else:
            time_axis = "   " + (" " * (3 + max_size // 2)).join(
                [get_local_time(timestamps[idx]).strftime('%H:%M:%S') for idx in [0, n // 2, -1]])
        plot.append(time_axis)
        return plot