from main_monitor import MainMonitor
import argparse


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
            s.append((name, url, float(delay), float(timeout)))
        return s
    except FileNotFoundError:
        raise Exception('Could not find the file at the specified path. Please enter a valid location')
    except (TypeError, ValueError):
        raise Exception(f"Error at line {idx} of the input file. Format should be 'name, url, delay, timeout'")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    logs_path = './logs'
    input_file = './sites.txt'
    sites = get_sites(input_file)
    mon = MainMonitor(sites, logs_path)
    mon.start()
