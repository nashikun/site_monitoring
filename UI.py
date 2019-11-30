import curses
from collections import defaultdict
from datetime import datetime


class UserInterface:

    def __init__(self, sites, screen):
        self.screen = screen
        self.h, self.w = self.screen.getmaxyx()
        self.init_curses()
        self.sites = sites
        self.stored_screens = defaultdict(list)
        self.stored_metrics = defaultdict(lambda: defaultdict(lambda: None))
        self.changed = defaultdict(lambda: True)  # This too
        self.current_page = 0
        self.header = curses.newwin(7, 18, 0, self.w // 2 - 8)
        self.cursor = 0
        self.max_cursor = len(sites)
        self.set_stop = False

    def init_curses(self):
        self.screen.keypad(1)
        self.screen.timeout(10)
        curses.noecho()
        curses.curs_set(0)
        curses.cbreak()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

    def render_screen(self, metrics):
        #  Update the stored metrics for each site
        for site, metric in metrics.items():
            for i in range(1, 2):
                self.changed[(i, site)] = True
            for delay, values in metric:
                for k, v in values.items():
                    self.stored_metrics[(site, delay)][k] = v
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
            self.resume_screen()

    def get_keypress(self):
        ch = self.screen.getch()
        if ch == curses.KEY_UP:
            self.cursor = max(self.cursor - 1, 0)
        elif ch == curses.KEY_DOWN:
            self.cursor = min(self.cursor + 1, self.max_cursor)
        elif ch == ord('q') or ch == ord('Q'):
            self.set_stop = True
            curses.endwin()
        elif ch == curses.KEY_ENTER or ch == 10 or ch == 13:
            if not self.current_page:
                self.current_page = self.cursor + 1
                self.cursor = 0


    def welcome_screen(self):
        #  If this screen has been changed (as in a new website has been added), recalculate the string
        if self.changed[0]:
            text = [" ________________", "|                |", "|                |", "| Site Monitorer |",
                    "|                |", "|________________|", "", "Please choose an option:", "0001 - Resume"]
            text.extend([f"{idx + 2:04d} - {site[0].upper()}" for idx, site in enumerate(self.sites)])
            self.changed[0] = False
            self.stored_screens[0] = text

        welcome_message = self.stored_screens[0]
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
        #  Render
        self.screen.refresh()

    def resume_screen(self):
        separator = "_" * (self.w - 10)
        full_text = []
        for site in self.sites:
            #   Recalculate the site string and store if needed
            if self.changed[(1, site)]:
                text = []
                # The header
                text.extend([f"Website : {site[0]}", "", f"Pinged every : {site[2]:10.2f} seconds", "",
                             "Over the last 2 mins:", ])
                #  The availability stats
                data = self.stored_metrics[(site, 120)]
                availability = data["availability"]
                if availability:
                    text.append(f"    Availability          : {100 * availability:10.2f}%"),
                else:
                    text.append(f"    Availability          : --,--%"),
                unavailable_since = data['unavailable_since']
                recovered_at = data['recovered_at']
                if unavailable_since:
                    t = datetime.utcfromtimestamp(int(data['unavailable_since'])).strftime('%Y-%m-%d %H:%M:%S')
                    text.append(f"    Website is down since           : {t}"),
                elif recovered_at:
                    t = datetime.utcfromtimestamp(int(data['recovered_at'])).strftime('%Y-%m-%d %H:%M:%S')
                    text.append(f"    Website is is back online since : {t}", ),

                #   The stats over the last 10 minutes
                data = self.stored_metrics[(site, 10)]

                if not data:
                    text.extend(["", "Over the last 10 minutes:", f"    Average Response Time : --",
                                 f"    Maximum Response Time : --", ])
                else:
                    text.extend([
                        "", "Over the last 10 minutes:",
                        f"    Average Response Time : {int(1000 * data['avg_elapsed'])} ms",
                        f"    Maximum Response Time : {int(1000 * data['max_elapsed'])} ms",
                        f"    Response Code Count:", ])
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
                self.changed[(1, site)] = False
                self.stored_screens[(1, site)] = text

            #  Add the string to the full text
            full_text.extend(self.stored_screens[(1, site)])
            full_text.append(separator)
        self.max_cursor = max(len(full_text) - self.h, 0)

        for i in range(self.cursor, min(self.cursor + self.h, len(full_text)-1)):
            self.screen.addstr(i-self.cursor, 5, full_text[i])
        self.screen.refresh()

# TODO remove down_since if setting recovered_at
