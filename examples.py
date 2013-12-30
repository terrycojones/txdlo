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


def onFirstCallback(deferreds):
    """
    Return a deferred that fires with an (index, result) tuple to indicate
        which element of C{deferreds} fired first. If any deferred errors,
        the returned deferred will be failed with an (index, error) value.

    @param deferreds: a C{list} of deferreds.
    @return: a L{twisted.internet.defer.Deferred} that fires as above.
    """
    if len(deferreds) == 0:
        raise ValueError('Empty list passed to onFirstCallback')

    dlo = DeferredListObserver()
    map(dlo.append, deferreds)
    deferred = Deferred()
    fired = False

    def observer(index, success, value):
        if not fired:
            if success:
                deferred.callback((index, value))
            else:
                deferred.errback((index, value))

    dlo.observe(observer)

    return deferred
