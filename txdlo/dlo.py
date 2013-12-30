class DeferredListObserver(object):
    """
    Call a list of observer functions with information about firing events
    that occur on a set of deferreds. Observers are called with event
    information in the order they are added (via C{observe}).

    @param maintainHistory: if C{True} a history of all events is maintained.
        This can be replayed to newly added observers and is accessible to
        class instances. If C{False}, the default, no history is kept.
    @ivar history: a C{list} of (index, success, value) tuples, in the order
        that the deferreds in the set fired (this will generally not be the
        order in which the deferreds are added to the set). The history
        attribute will only exist if C{maintainHistory} (above) is C{True}.
    @ivar successCount: the number of observed deferreds that have been called
        successfully.
    @ivar failureCount: the number of observed deferreds that have been
        errored.
    @ivar pendingCount: the number of observed deferreds that have not yet been
        called or errored.
    """

    def __init__(self, maintainHistory=False):
        self._maintainHistory = maintainHistory
        if maintainHistory:
            self.history = []
        self.successCount = self.failureCount = self.pendingCount = 0
        self._observers = []

    def _makeCallbacks(self, index):

        def callback(value):
            self.pendingCount -= 1
            self.successCount += 1
            event = (index, True, value)
            if self._maintainHistory:
                self.history.append(event)
            for observer in self._observers:
                observer(*event)
            return value

        def errback(value):
            self.pendingCount -= 1
            self.failureCount += 1
            event = (index, False, value)
            if self._maintainHistory:
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

    def observe(self, observer, replayHistory=False):
        """
        Add an observer function that will be called (as below) with details
        of deferred firings.

        @param observer: a C{function} that will be called with 3 arguments
            each time one of the observed deferreds in the set fires. The
            arguments will be:
                - The index of the deferred that fired.
                - C{True} if the deferred was called, C{False} if it errored.
                - The value passed to the callback or errback.
        @param replayHistory: if C{True}, the history of deferred firings
            that occurred prior to this observer being added will be sent
            to the observer. If no history is being maintained, C{RuntimeError}
            will be raised.
        """
        if replayHistory:
            if self._maintainHistory:
                for event in self.history:
                    observer(*event)
            else:
                raise RuntimeError('Cannot replay non-existent event history '
                                   'to new observer')

        self._observers.append(observer)
