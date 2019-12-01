import curses
from collections import defaultdict
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
                    if isinstance(v, float):
                        self.cum_metrics[(site, delay)][k].append(round(v, 3))
                    else:
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
        |  0002 - site 1
        |  0003 - site 2

        """
        #  If this screen has been changed (as in a new website has been added), recalculate the string
        if self.changed[0]:
            text = [" ________________", "              |", "              |", "| Site Monitorer |",
                    "              |", "|________________|", "", "Please choose an option:", "0001 - Summary"]
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
        Renders the summary screen.
        The layout is as follows:

        .. aafig::
            :textual:

            site 1 info block
            _________________________

            site 2 info block
            _________________________

            site 3 info block
            _________________________


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
        site = self.sites[self.current_page - 2]
        if self.changed[(1, site)]:
            self.update_site_info(site)
        if self.changed[(2, site)]:
            self.update_plot(site)
        text = self.stored_info[site][:]
        if self.stored_plot[(site, 10)]:
            text.extend(["", "", "The maximum response time over the last 60 s", "", *self.stored_plot[(site, 10)][0],
                         "", "The average response time over the last 60 s", "", *self.stored_plot[(site, 10)][1], ""])
        if self.stored_plot[(site, 60)]:
            text.extend(
                ["", "", "The maximum response time over the last 60 min", "", *self.stored_plot[(site, 60)][0],
                 "", "The average response time over the last 60 min", "", *self.stored_plot[(site, 60)][1], ""])
        if self.stored_plot[(site, 120)]:
            text.extend(
                ["", "", "The availability over the last 120 min", "", self.stored_plot[(site, 120)]][0])
        self.max_cursor = max(len(text) - self.h, 0)
        for i in range(self.cursor, min(self.cursor + self.h, len(text))):
            self.screen.addstr(i - self.cursor, 5, text[i])
        self.screen.refresh()

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
                    self.stored_plot[(site, 120)] = [self.get_plot(timestamps, metrics, delay, max_size)]
                else:
                    self.stored_plot[(site, delay)] = []
                    for stat in ['max_elapsed', 'avg_elapsed']:
                        metrics = self.cum_metrics[(site, delay)][stat][-max_size:]
                        self.stored_plot[(site, delay)].append(self.get_plot(timestamps, metrics, delay, max_size))

        self.changed[(2, site)] = False

    def update_site_info(self, site):
        """
        Updates the info string stored in memory.
        The layout is as follows:

        .. aafig::

            `Website:`
            `Pinged every :`
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

    def get_plot(self, timestamps, metrics, delay, max_size):
        n = len(metrics)
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
        plot = array_to_plot([metrics[0]] + metrics, min_val, max_val, step, repeats)
        m = len(plot)
        if delay == 120:
            plot.append(" " * 9 + "_" * (3 * max_size))
            for i in range(m - 1):
                plot[i] = f"{100 * (min_val + (m - 1 - i) * step) :0.0f} %  |" + plot[i]
        else:
            plot.append(" " * 9 + "_" * (3 * max_size))
            for i in range(m):
                plot[i] = f"{int(1000 * (min_val + (m - 1 - i) * step)) :04d} ms |" + plot[i]
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

# TODO Add a semaphore or something to protect access to data
#   Add scrolling to the main menu
#   for some reason response time can be bigger than timeout? gotta look into this
