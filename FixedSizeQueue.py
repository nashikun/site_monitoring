from threading import Semaphore

#  A binary heap might have been better for insertion, but I opted for a regular
# list as heaps mess up the order of the elements, and we need it
# Additionally the items to be added should be much in order
# most of the time so very little comparisons are done


class FixedSizeQueue(list):
    def __init__(self, capacity, key):
        super(list, self).__init__()
        self.capacity = capacity
        self.h = []
        self.sem = Semaphore()
        self.key = key

    def add(self, e):
        self.sem.acquire()
        for i in range(len(self.h) - 1, -1, -1):
            if self.key(e) >= self.key(self.h[i]):
                self.h.insert(i + 1, e)
                break
        else:
            self.h.insert(0, e)
        if len(self.h) > self.capacity:
            self.h = self.h[-self.capacity:]
        self.sem.release()

    def get_slice(self, min_value, max_value):
        self.sem.acquire()
        min_slice = max_slice = 0
        for i in range(len(self.h)):
            if self.key(self.h[i]) >= min_value:
                min_slice = i
                break
        for i in range(len(self.h)-1, min_slice-1, -1):
            if self.key(self.h[i]) <= max_value:
                max_slice = i + 1
                break
        h_slice = self.h[min_slice:max_slice]
        self.sem.release()
        return h_slice