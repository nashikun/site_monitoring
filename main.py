import argparse
import curses
import logging
import os
import time
from src.global_monitor import GlobalMonitor
from src.utils import get_local_time, get_sites

logger = logging.getLogger()
os.makedirs("logs", exist_ok=True)
file_log_handler = logging.FileHandler(
    "logs/logfile {}.log".format(get_local_time(time.time()).strftime("%d-%m-%Y %Hh%Mm%Ss"))
)

logger.addHandler(file_log_handler)
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_log_handler.setFormatter(formatter)

if __name__ == '__main__':
    logger.info("Program started")
    parser = argparse.ArgumentParser(usage='A program to monitor websites uptime and response time.')
    parser.add_argument("-f", "--file", type=str, help="The path to the input file.", required=True)
    parser.add_argument("-l", "--logs", type=str, help="The path to store the logs in.")
    args = parser.parse_args()
    input_file = args.file
    sites = get_sites(input_file)
    if not args.logs:
        print('No folder has been specified to save logs. They will be saved at ./logfiles')
        logs_path = './logfiles'
        time.sleep(1)
    else:
        logs_path = args.logs
    logger.info("Main Monitorer created")
    mon = GlobalMonitor(sites, logs_path)
    curses.wrapper(mon.start)
