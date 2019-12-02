# site_monitor module


#### class site_monitor.RequestScheduler(interval, url, timeout)
Bases: `threading.Thread`

This class creates a `requester.Requester` object every *interval* and stores the results in a queue.


* **Parameters**

    
    * **url** (*string*) – the url to make requests to.


    * **interval** (*float*) – the interval between requests in seconds


    * **timeout** – the time to wait in seconds before considering that the response timed-out.



* **Variables**

    **results** (*fixed_size.FixedSizeQueue*) – stores the request responses.



### run()
start making requests every **interval**


### stop()
stop making requests


#### class site_monitor.SiteMonitor(name, url, interval, timeout)
Bases: `threading.Thread`

The class to get relevant metrics over time from an url.
The methods have been implemented here instead of in `request_scheduler.RequestScheduler` to
avoid delaying the requests made periodically.


* **Variables**

    
    * **request_scheduler** (*request_scheduler*) – the scheduler making requests once per interval.


    * **availability** (*float*) – the availability of the website during the last two minutes.


    * **unavailable_since** (*Union**[**float**,**None**]*) – the unix time of the first time the url became unavailable.
    Is None if the site is available.


    * **recovered_at** (*Union**[**float**,**None**]*) – the unix time since the website recovered.
    Is None if the website is currently unavailable or the availability never went below 80%


    * **last_updates** (*dict*) – holds the time of the last updates to the metrics


    * **is_read** (*dict*) – a dict with booleans representing whether the latest metric
    on each time-frame has been retrieved or not.


    * **set_stop** (*bool*) – whether the monitor has been set to stop.



### get_metrics(end, duration, delay)
get the metrics over the specified time window ending at **end**


* **Note**

    To make sure all the responses have been received, we shift our window with **self.timeout**,
    so the window doesn’t effectively end at **end**



* **Parameters**

    
    * **end** – the end of the lookup window


    * **duration** – the duration of the window


    * **delay** – the delay between two lookups



### read_metrics()
Returns the unread metrics and marks them as read. The returned metrics are sorted for logging.


* **Returns**

    list



### run()
Starts monitoring the website. Each 10 seconds, calculate the metrics over the last 10 minutes,

    each minute calculate the metrics over the last hour, and update the availability every two minutes.


### stop()
Stops the monitoring.


### update_availability()
calculates the availability and stores it.


### update_metrics(delay, duration)
Retrieves the metrics and stores them.


* **Parameters**

    
    * **delay** – the interval between each two metric updates.


    * **duration** – the time window over which to calculate the metrics.
