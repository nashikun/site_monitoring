# fixed_size module


#### class fixed_size.FixedSizeQueue(capacity, key)
Bases: `object`

A fixed size queue where items are kept in ascending order when compared by key.


* **Parameters**

    
    * **capacity** (*int*) – the maximum number of elements kept in the queue


    * **key** – the function to use to compare the elements



* **Variables**

    
    * **sem** – a semaphore to make the queue multi-thread safe


    * **h** (*list*) – the inner list to store elements



### add(e)
adds an element to the queue, while keeping it increasing with respect to **key**


* **Note**

    A binary heap might have been better for insertion, but I opted for a regular
    list as heaps mess up the order of the elements, and we need it.
    Additionally the items to be added should be pretty much in order
    most of the time so very little comparisons are done



* **Parameters**

    **e** – the element to add to the queue



### get_slice(min_value, max_value)
gets the list of all values in lust whose **key** value is between **min_value** and **max_value**.


* **Parameters**

    
    * **min_value** (*int*) – the maximum value.


    * **max_value** (*int*) – the minimum value.



* **Return type**

    list
