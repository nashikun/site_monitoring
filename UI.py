import curses
from collections import defaultdict
from datetime import datetime


class UserInterface:

    def __init__(self, sites, screen):
        self.screen = screen
        self.h, self.w = self.screen.getmaxyx()
        self.init_curses()
        self.sites = sites
        self.stored_metrics = {site: {delay: defaultdict(lambda: None) for delay in [10, 60, 120]} for site in sites}
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
        for site in self.sites:
            if site in metrics.keys():
                for delay, values in metrics[site]:
                    for k, v in values.items():
                        self.stored_metrics[site][delay][k] = v
        #  Clears the screen and reads key presses
        self.get_keypress()
        self.header.clear()
        self.screen.clear()
        # If screen is resized, update the height and width as well as the position of the header
        if curses.is_term_resized(self.h, self.w):
            self.header.mvwin(0, round(self.w / 2) - 8)
            self.h, self.w = self.screen.getmaxyx()
        # renders the current page
        if self.current_page == 1:
            self.welcome_screen()
        elif self.current_page == 0:
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
        elif ch == curses.KEY_BACKSPACE:
            self.current_page = self.cursor + 1

    def welcome_screen(self):
        welcome_message = [" ________________",
                           "|                |",
                           "|                |",
                           "| Site Monitorer |",
                           "|                |",
                           "|________________|"]

        #  Draw the header
        for idx, line in enumerate(welcome_message):
            self.header.addstr(idx, 0, line)
        #   Print the menu
        self.screen.addstr(10, 5, "Please choose an option:")
        if not self.cursor:
            self.screen.addstr(11, 5, "0001 - Resume", curses.color_pair(1))
        else:
            self.screen.addstr(11, 5, "0001 - Resume")
        for idx, site in enumerate(self.sites):
            title = f"{idx + 2:04d} - {site[0].upper()}"
            if self.cursor - 1 == idx:
                self.screen.addstr(12 + idx, 5, title, curses.color_pair(1))
            else:
                self.screen.addstr(12 + idx, 5, title)
        #  Render
        self.screen.refresh()
        self.header.refresh()

    def resume_screen(self):
        separator = "_" * (self.w - 10)
        full_text = []
        for site in self.sites:

            #  The header
            full_text.extend([
                f"Website : {site[0]}",
                "",
                f"Pinged every : {site[2]:10.2f} seconds",
                "",
                "Over the last 2 mins:",
            ])

            #  The availability stats
            data = self.stored_metrics[site][120]
            availability = data["availability"]
            if availability:
                full_text.append(f"    Availability          : {100 * availability:10.2f}%"),
            else:
                full_text.append(f"    Availability          : --,--%"),
            unavailable_since = data['unavailable_since']
            recovered_at = data['recovered_at']
            if unavailable_since:
                t = datetime.utcfromtimestamp(int(data['unavailable_since'])).strftime('%Y-%m-%d %H:%M:%S')
                full_text.append(f"    Website is down since           : {t}"),
            elif recovered_at:
                t = datetime.utcfromtimestamp(int(data['recovered_at'])).strftime('%Y-%m-%d %H:%M:%S')
                full_text.append(f"    Website is is back online since : {t}", ),

            #   The stats over the last 10 minutes
            data = self.stored_metrics[site][10]

            if not data:
                full_text.extend([
                    "",
                    "Over the last 10 minutes:",
                    f"    Average Response Time : --",
                    f"    Maximum Response Time : --",
                ])
            else:
                full_text.extend([
                    "",
                    "Over the last 10 minutes:",
                    f"    Average Response Time : {int(1000 * data['avg_elapsed'])} ms",
                    f"    Maximum Response Time : {int(1000 * data['max_elapsed'])} ms",
                    f"    Response Code Count:",
                ])
                full_text.extend([f"         {k} : {v}" for k, v in data['codes_count'].items()])

            #   The stats over the last hour
            data = self.stored_metrics[site][60]
            if not data:
                full_text.extend([
                    "",
                    "Over the last 60 minutes:",
                    f"    Average Response Time : --",
                    f"    Maximum Response Time : --",
                ])
            else:
                full_text.extend([
                    "",
                    "Over the last 60 minutes:",
                    f"    Average Response Time : {int(1000 * data['avg_elapsed'])} ms",
                    f"    Maximum Response Time : {int(1000 * data['max_elapsed'])} ms",
                    f"    Response Code Count:",
                ])
                full_text.extend([f"         {k} : {v}" for k, v in data['codes_count'].items()])
            full_text.append(separator)

        self.max_cursor = max(len(full_text) - self.h, 0)

        for i in range(30):
            self.screen.addstr(i, 5, full_text[i])
        self.screen.refresh()

# TODO remove down_since if setting recovered_at
#  Make sure the text doesn't get recalculated every time
