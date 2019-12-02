# utils module


#### class utils.Requester(url, queue, timeout)
Bases: `threading.Thread`

The base class that sends requests and adds relevant data to the queue in the right order.


* **Parameters**

    
    * **url** – the url to make requests to


    * **queue** – the queue to which add the gathered data


    * **timeout** – the time to wait before considering the request timed-out



### run()
Runs the `Requester` and adds the result to the queue before exiting.
|  If connection to the site fails, the status code is 503
|  If the connection succeeds but times out, the status code is 408


* **Return type**

    None



#### utils.array_to_plot(array, min_val, max_val, step, repeats)
Draws an input array in ascii


* **Parameters**

    
    * **array** (*list*) – the array to plot


    * **min_val** (*int*) – the minimum value to plot. Any lower value will be clamped


    * **max_val** (*int*) – the maximum value to plot. Any higher value will be clamped


    * **step** (*float*) – the difference between 2 different levels in the plot.


    * **repeats** (*int*) – The length of each character on the x-axis



* **Returns**

    A list containing each line as a string.



* **Return type**

    list



#### utils.get_local_time(timestamp)
Converts time from unix time to a `datetime` object representing time in the current time-zone


* **Parameters**

    **timestamp** – the unix time stamp



* **Returns**

    the time in the current timezone



#### utils.get_sites(file_path)
