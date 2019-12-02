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

Once the website is running, you will find yourself in the main menu. You can navigate using the up and down arrows and enter. You can press *h* any time to return to the main menu.\
To exit the program, press **q**

## Testing

## Documentation

To see a detailed documentation for each module:
[test](docs/index.html)
