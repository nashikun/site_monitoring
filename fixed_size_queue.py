from threading import Semaphore

#  A binary heap might have been better for insertion, but I opted for a regular
# list as heaps mess up the order of the elements, and we need it
# Additionally the items to be added should be much in order
# most of the time so very little comparisons are done


class FixedSizeQueue(list):

    """A fixed size queue where items are kept in ascending order when compared by key.

    :param int capacity: the maximum number of elements kept in the queue
    :param key: the function to use to compare the elements
    :ivar sem: a semaphore to make the queue multi-thread safe
    """

    def __init__(self, capacity, key):
        super(list, self).__init__()
        self.capacity = capacity
        self.h = []
        self.sem = Semaphore()
        self.key = key

    def add(self, e):
        """
        adds an element to the queue, while keeping it increasing with respect to **key**
        :param e: the element to add to the queue
        """
        self.sem.acquire()
        # Adds item to its place
        val = self.key()
        for i in range(len(self.h) - 1, -1, -1):
            if val >= self.key(self.h[i]):
                self.h.insert(i + 1, e)
                break
        else:
            self.h.insert(0, e)
        # Ensures the length is below capacity
        if len(self.h) > self.capacity:
            self.h = self.h[-self.capacity:]
        self.sem.release()

    def get_slice(self, min_value, max_value):
        """
        gets the list of all values in lust whose **key** value is between **min_value** and **max_value**
        :param int min_value:
        :param int max_value:
        :return:
        """
        if min_value > max_value:
            return []
        self.sem.acquire()
        min_slice = max_slice = 0
        # Get the index of the smallest value that is gt min_value
        for i in range(len(self.h)):
            if self.key(self.h[i]) >= min_value:
                min_slice = i
                break
        # Get the index of the greater value that is lt both min_slice and max_value
        for i in range(len(self.h)-1, min_slice-1, -1):
            if self.key(self.h[i]) <= max_value:
                max_slice = i + 1
                break
        h_slice = self.h[min_slice:max_slice]
        self.sem.release()
        return h_slice
