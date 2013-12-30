"""
NOTE: these functions are untested. They're just here to provide an example of
      how you might use DeferredListObserver to do various things.
"""

from twisted.internet.defer import Deferred, succeed

from txdlo import DeferredListObserver


def deferredList(deferreds):
    """
    Return a deferred that fires with a list of (success, result) tuples,
    'success' being a boolean.

    @param deferreds: a C{list} of deferreds.
    @return: a L{twisted.internet.defer.Deferred} that fires as above.
    """
    if len(deferreds) == 0:
        return succeed([])

    dlo = DeferredListObserver()
    map(dlo.append, deferreds)
    deferred = Deferred()

    def observer(*ignore):
        if dlo.pendingCount == 0:
            # Everything in the list has fired.
            resultList = [None] * len(deferreds)
            for index, success, value in dlo.history:
                resultList[index] = (success, value)
            deferred.callback(resultList)

    dlo.observe(observer)

    return deferred


class DeferredList(object):
    """
    A class holding a deferred that fires with a list of (success, result)
    tuples, 'success' being a boolean.

    The use of a class allows us to provide an C{append} function that allows
    additional deferreds to be added to the observed list. This is unlike the
    above L{deferredList} function and the Twisted DeferredList class, both of
    which take a fixed list of deferreds.

    Use C{append} to add deferreds. Add callbacks to C{deferred} to be notified
    when all deferreds have fired.  Deferreds can be added at any time.
    """

    def __init__(self):
        self.deferred = Deferred()
        dlo = DeferredListObserver()

        def observer(*ignore):
            if dlo.pendingCount == 0:
                # Everything in the list has fired.
                resultList = [None] * (dlo.successCount + dlo.failureCount)
                for index, success, value in dlo.history:
                    resultList[index] = (success, value)
                self.deferred.callback(resultList)

        dlo.observe(observer)
        self.append = dlo.append


def onFirstCallback(deferreds):
    """
    Return a deferred that fires with an (index, result) tuple to
    indicate which element of C{deferreds} fired first. If any deferred
    errors, the returned deferred will be failed with an (index, error)
    value.

    @param deferreds: a C{list} of deferreds.
    @return: a L{twisted.internet.defer.Deferred} that fires as above.
    """
    if len(deferreds) == 0:
        raise ValueError('Empty list passed to onFirstCallback')

    dlo = DeferredListObserver()
    map(dlo.append, deferreds)
    deferred = Deferred()
    state = {'fired': False}

    def observer(index, success, value):
        if not state['fired']:
            state['fired'] = True
            if success:
                deferred.callback((index, value))
            else:
                deferred.errback((index, value))

    dlo.observe(observer)

    return deferred


def onNCallbacks(deferreds, n):
    """
    Return a deferred that fires with a list of C{n} (index, result)
    tuples once C{n} of the passed deferreds have fired. If any deferred
    errors, the returned deferred will be failed with an (index, error)
    value.

    @param deferreds: a C{list} of deferreds.
    @param n: an C{int} number of deferreds, as above.
    @return: a L{twisted.internet.defer.Deferred} that fires as above.
    """
    if len(deferreds) == 0:
        raise ValueError('Empty list passed to onFirstCallback')

    if n < 0:
        raise ValueError('n < 0 passed to onFirstCallback')

    if n > len(deferreds):
        raise ValueError('n > len(deferreds) passed to onFirstCallback')

    if n == 0:
        return succeed([])

    dlo = DeferredListObserver()
    map(dlo.append, deferreds)
    deferred = Deferred()

    def observer(index, success, value):
        if success:
            if dlo.successCount == n:
                resultList = []
                for _index, _success, _value in dlo.history:
                    if _success:
                        resultList.append = (_index, _value)
                        if len(resultList) == n:
                            deferred.callback(resultList)
                            return
        else:
            deferred.errback((index, value))

    dlo.observe(observer)

    return deferred


def onFirstCallbackOnlyErrbackAsALastResort(deferreds):
    """
    Return a deferred that fires with an (index, result) tuple to
    indicate which element of C{deferreds} fired first. If any deferred
    errors, we ignore it if there's still a chance that one of the
    deferreds will fire successfully. Only if all deferreds fail do we
    errback with the (index, error) value of the first error.

    @param deferreds: a C{list} of deferreds.
    @return: a L{twisted.internet.defer.Deferred} that fires as above.
    """
    if len(deferreds) == 0:
        raise ValueError('Empty list passed to '
                         'onFirstCallbackOnlyErrbackAsALastResort')

    dlo = DeferredListObserver()
    map(dlo.append, deferreds)
    deferred = Deferred()
    state = {'fired': False}

    def observer(index, success, value):
        if not state['fired']:
            if success:
                state['fired'] = True
                deferred.callback((index, value))
            else:
                if dlo.pendingCount == 0:
                    state['fired'] = True
                    # No chance of a successful callback. Send the index
                    # and value of the first error.
                    event = dlo.history[0]
                    # We could assert event[1] is False
                    deferred.errback((event[0], event[2]))

    dlo.observe(observer)

    return deferred


class DeferredPoolWithEmptyFunction(object):
    """
    A class observing a collection of deferreds that provides a
    C{notifyWhenEmpty} function that returns a deferred that fires when all
    the deferreds in the collection have fired.

    The use of a class allows us to provide an C{append} function that allows
    additional deferreds to be added to the observed deferreds.

    Use C{append} to add deferreds.
    """

    def __init__(self):
        self._deferreds = []
        dlo = DeferredListObserver()

        def observer(*ignore):
            if dlo.pendingCount == 0:
                # Everything in the list has fired.
                for deferred in self._deferreds:
                    deferred.callback(None)
                self._deferreds = []

        dlo.observe(observer)
        self.append = dlo.append

    def notifyWhenEmpty(self):
        """
        Return a deferred that will be called (with C{None}) when the observed
        pool of deferreds have all fired.
        """
        deferred = Deferred()
        self._deferreds.append(deferred)
        return deferred
