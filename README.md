# site monitoring

A program to easily monitor the performance of multiple websites at once on a console.\
![demo](http://g.recordit.co/XvfIa7Fwl0.gif)
## Table of contenents
 - [Installation](#installation)
 - [Features](#features)
 - [Usage](#usage)
 - [Testing](#testing)
 - [Documentation](#documentation)
 
 ## Installation
 - In the program's folder, run:
 ```shell
$ pip install .
```
- If you are in windows and get a pip error, you might want to consider downgrading your pip version, or manually installing [windows-curses](https://pypi.org/project/windows-curses/).

## Features
 - Monitor multiple websites at once, with different settings.
 - See a summary of the websites' performance.
 - For every website, see details on the performance as well as an evolution plot.
 - See the historics of when all websites went down or back online.
 - The possibility to store all ping results in a file for analysis.

## Usage
In the projet directory, eun
```shell
python -f input_file -l logs_file
```
Where input_file is the file with websites to monitor. Every line of the file should be
> website_name, url, ping_interval, timeout
With:
 - website_name: a unique usen defined identifier for each url
 - url: the url to monitor
 - ping_interval: the interval between each ping to the url.
 - timeout: the time to wait before a request is considered as timed out and return a 408 error.

Once the website is running, you will find yourself in the main menu. You can navigate using the up and down arrows and enter. You can press **h** any time to return to the main menu.\
The application will save the metrics in 
> logs_file/{website_name}_{ping_interval}.txt 

And the response for each request in
> logs_file/{website_name}_{ping_interval}_raw.txt 

To exit the program, press **q**

## Testing

A simple [test server](tests/test_server.py) is present in [tests](tests) to simulate latency and availability.
\ You can run it using
```shell
python tests/test_server.py
``` 
Once the test server is up, you can either run the program and check the metrics are coherent, or run [tests.py](tests/tests.py)
using :
```
python -m unittest tests.tests
```

## Documentation

To see a detailed documentation for each module:
 - [global_monitor module](https://nashikun.github.io/site_monitoring/global_monitor.html) : Contains **GlobalMonitor** main module that monitors the different websites, formats the metrics and outputs them to screen.
 - [site_monitor module](https://nashikun.github.io/site_monitoring/site_monitor.html) : Contains **SiteMonitor**, class to get relevant metrics over time from an url. 
 - [user_interface module](https://nashikun.github.io/site_monitoring/user_interface.html)  : The class that renders everything on screen. 
 - [fixed_size module](https://nashikun.github.io/site_monitoring/fixed_size.html) : Contains the classes that will be used to store data. 
 - [utils module](https://nashikun.github.io/site_monitoring/utils.html) : Miscellaneous functions and classes. 
