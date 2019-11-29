from main_monitor import MainMonitor
import time

import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    mon = MainMonitor([(0.1, 'http://cdiscount.com', 5)])
    mon.start()

# TODO Add documentation. Don't forget params
#
