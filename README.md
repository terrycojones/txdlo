## txdlo - a (Twisted) deferred list observer

`txdlo` is a Python package that provides a class called `DeferredListObserver`.

As you might guess, `DeferredListObserver` lets you observe callback and
errback events from a list of [Twisted](http://twistedmatrix.com)
[deferreds](http://twistedmatrix.com/documents/current/core/howto/defer.html). You
can add observers that will be passed information about deferreds firing.
You can add deferreds to the observed list at any time, which is very
useful if you're dynamically creating deferreds that you want to monitor.

The class can be used to easily build functions or classes that provide
deferreds that fire when arbitrary combinations of events from the observed
deferreds have occurred.

For example you can write functions or classes that support deferreds that

* Implement Twisted's `DeferredList` or simple variants of it, or that let
  you separate the various behaviors of `DeferredList` into simpler
  functions.
* Provide a deferred that fires when N of the observed deferreds have fired.
* Provide a deferred that ignores errors until one of the observed deferred
  succeeds, only firing with an error if all the observed deferreds fail.
* Or (a more involved example), suppose you have 3 methods that can return
  you a user's avatar: a fast local cache, a filesystem, and a slow network
  call to Gravatar. You want to write a deferred-returning function that
  launches all three lookups at once and fires its deferred with the first
  answer. But if the cache and/or filesystems fails first, you don't want
  to trigger an error, you instead want to take the result from Gravatar
  and add it to the cache and/or filesystem, as well firing the returned
  deferred with the result (wherever it comes from). Only if all three
  lookups fail do you want to errback the deferred you returned.

## Usage

Here's a simplified version of
[Twisted's DeferredList](http://twistedmatrix.com/documents/current/api/twisted.internet.defer.DeferredList.html)
class, written as a function.

```python
from twisted.internet.defer import Deferred
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

    dlo = DeferredListObserver(maintainHistory=True)
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
```

A `DeferredListObserver` maintains three counts:

* `successCount`: the number of observed deferreds that have had fired successfully.
* `failureCount`: the number of observed deferreds that have errored.
* `pendingCount`: the number of observed deferreds that have not yet fired.

As in the example above, you can arrange for your observer function to
examine the `DeferredListObserver` to see its state and act accordingly.

A `DeferredListObserver` can maintain the history of events it has seen (as
in the example above). This can serve two purposes: (1) it can be useful
for an observer function to have easy access to the results of the
deferreds without having to store the results itself (as above), and (2) if
you add an observer after some deferreds have already fired you may want
your observer to be called with the events it missed.

Observer functions must take 3 arguments:

* `index`: the index of the deferred that fired. The index is the
  zero-based order in which deferreds were added to the
  `DeferredListObserver` via its `append` function.
* `success`: `True` if the deferred in question was fired via its
  `callback`, `False` if it was fired via `errback`.
* `value`: the value the deferred was fired with.

To cause an added observer to immediately be called with the event history
(if any), you must instantiate the `DeferredListObserver` with
`maintainHistory=True` and pass `replayHistory=True` to `observe`. If you
add an observer and request that the event history is replayed to it but
the `DeferredListObserver` is not maintaining a history, a `RuntimeError`
will be raised.

Observers added to a `DeferredListObserver` will be called in the order
they were added.

The (untested) code in `examples.py` gives some example usages.

The unit tests in `txdlo/test/test_txdlo.py` may also be instructive.

## Testing

To run the unit tests, either use `make test` or `trial txdlo`.

## A subtlety

Note that the `DeferredListObserver` adds transparent callback and errback
functions to the deferreds it is observing. The functions will see the
state of the firing deferred at that point in its callback chain. If you
add additional callbacks or errbacks to a deferred after passing it to
`DeferredListObserver.append`, what goes on in those callbacks and errbacks
will not be seen. For example, consider this code:

```python
from twisted.internet.defer import Deferred, succeed, fail
from txdlo import DeferredListObserver

def die(value):
    raise Exception()

def observer(index, success, value):
    if success:
        print 'The deferred succeeded!'

dlo = DeferredListObserver()
dlo.observe(observer)

deferred = succeed(42)
dlo.append(deferred)  # dlo adds a transparent callback & errback to deferred.

deferred.addCallback(die)
```

The callback added by the `DeferredListObserver` (in the `.append` call)
will receive the succesful (42) value and report that the deferred fired
successfully. But the later callback (`die`) for `deferred` will cause the
deferred to transition into a failed state.

There's nothing that can be done about this (depending on your needs, it
can be an advantage).  That's just the way Twisted deferreds work. If it's
a problem for you, you can avoid it by not adding callbacks to deferreds
after you begin observing them.

You'll see a similar warnings on the documentation for
[Twisted's DeferredList](http://twistedmatrix.com/documents/current/api/twisted.internet.defer.DeferredList.html)

If you don't understand this warning, you should probably spend more
quality time alone with Twisted deferreds!
