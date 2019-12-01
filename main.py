from main_monitor import MainMonitor
import argparse
import curses
import logging
import os
import time
from utils import get_local_time

logger = logging.getLogger()
os.makedirs("logfiles", exist_ok=True)
file_log_handler = logging.FileHandler(
    "logfiles/logfile {}.log".format(get_local_time(time.time()).strftime("%d-%m-%Y %Hh%Mm%Ss"))
)

logger.addHandler(file_log_handler)
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_log_handler.setFormatter(formatter)


def get_sites(file_path):
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


if __name__ == '__main__':
    logger.info("Program started")
    parser = argparse.ArgumentParser(usage='A program to monitor websites uptime and response time.')
    parser.add_argument("-f", "--file", type=str, help="The path to the input file.", required=True)
    parser.add_argument("-l", "--logs", type=str, help="The path to store the logs in.")
    args = parser.parse_args()
    input_file = args.file
    sites = get_sites(input_file)
    if not args.logs:
        print('No folder has been specified to save logs. They will be saved at ./logs')
        logs_path = './logs'
    else:
        logs_path = args.logs
    logger.info("Main Monitorer created")
    mon = MainMonitor(sites, logs_path)
    curses.wrapper(mon.start)
