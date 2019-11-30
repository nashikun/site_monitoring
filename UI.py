import curses


class UserInterface:

    def __init__(self, sites, screen):
        self.screen = screen
        self.h, self.w = self.screen.getmaxyx()
        self.init_curses()
        self.sites = sites
        self.current_page = 0
        self.header = curses.newwin(7, 18, 0, self.w // 2 - 8)
        self.cursor = 0
        self.set_stop = False

    def init_curses(self):
        self.screen.keypad(1)
        self.screen.timeout(10)
        curses.noecho()
        curses.curs_set(0)
        curses.cbreak()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)

    def welcome_screen(self):
        welcome_message = [" ________________",
                           "|                |",
                           "|                |",
                           "| Site Monitorer |",
                           "|                |",
                           "|________________|"]

        self.header.clear()
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
        #  Render and get the key presses.
        self.screen.refresh()
        self.header.refresh()

    def render_screen(self):
        # If screen is resized, update the height and width as well as the position of the header
        self.get_keypress()
        if curses.is_term_resized(self.h, self.w):
            self.header.mvwin(0, round(self.w / 2) - 8)
            self.screen.clear()
            self.h, self.w = self.screen.getmaxyx()
        if self.current_page == 0:
            self.welcome_screen()

    def get_keypress(self):
        ch = self.screen.getch()
        if ch == curses.KEY_UP:
            self.cursor = max(self.cursor - 1, 0)
        elif ch == curses.KEY_DOWN:
            self.cursor = min(self.cursor + 1, len(self.sites))
        elif ch == ord('q') or ch == ord('Q'):
            self.set_stop = True
            curses.endwin()
