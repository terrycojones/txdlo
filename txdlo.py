class DeferredListObserver(object):
    """
    Calls an observer function with information about firing events that occur
    on a set of deferreds.

    @ivar history: a C{list} of (index, success, value) tuples, in the order
        that the deferreds in the set fired (this will generally not be the
        order in which the deferreds are added to the set).
    @ivar successCount: the number of observed deferreds that have been called
        successfully.
    @ivar failureCount: the number of observed deferreds that have been
        errored.
    @ivar pendingCount: the number of observed deferreds that have not yet been
        called or errored.
    """

    def __init__(self):
        self._observers = []
        self.history = []
        self.successCount = self.failureCount = self.pendingCount = 0

    def _makeCallbacks(self, index):

        def callback(value):
            self.pendingCount -= 1
            self.successCount += 1
            event = (index, True, value)
            self.history.append(event)
            for observer in self._observers:
                observer(*event)
            return value

        def errback(value):
            self.pendingCount -= 1
            self.failureCount += 1
            event = (index, False, value)
            self.history.append(event)
            for observer in self._observers:
                observer(*event)
            return value

        return (callback, errback)

    def append(self, deferred):
        """
        Monitor a deferred.

        @param deferred: An instance of L{twisted.internet.defer.Deferred}.
        @return: the passed deferred.
        """
        index = self.successCount + self.failureCount + self.pendingCount
        callback, errback = self._makeCallbacks(index)
        self.pendingCount += 1
        return deferred.addCallbacks(callback, errback)

    def addObserver(self, observer, replayHistory=True):
        """
        @param observer: a C{function} that will be called with 3 arguments
            each time one of the observed deferreds in the set fires. The
            arguments will be:
                - The index of the deferred that fired.
                - C{True} if the deferred was called, C{False} if it errored.
                - The value passed to the callback or errback.
        @param replayHistory: if C{True}, the history of deferred firings
            that occurred prior to this observer being added will be sent
            to the observer.
        """
        if replayHistory:
            # Replay history so far.
            for event in self.history:
                observer(*event)

        self._observers.append(observer)
