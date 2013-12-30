## txdlo

Here's a quick Python class called `DeferredListObserver` that lets you do various things with a list of [Twisted](http://twistedmatrix.com) deferreds. You can add observers that get passed information about the deferreds firing. You can also add deferreds to the observed list at any time (this is very useful if you're dynamically creating deferreds that you want to monitor).

The class can be used to easily build things like Twisted's `DeferredList` or simple variants of it, or can let you separate the various behaviors of `DeferredList` into simpler functions. You can also do other things that I've occasionally wanted.  E.g., get a deferred that fires when N of the observed deferreds have fired. Or ignore errors until one deferred succeeds, only firing with an error if all deferreds fail.

Or (a more involved example), suppose you have 3 methods that can return you a user's avatar: a fast local cache, a filesystem, and a slow network call to Gravatar. You want to launch all three lookups at once and use the first answer. But if the cache and/or filesystems fails first, you don't want an error you instead want to take the result from Gravatar and add it to the cache and/or filesystem, as well firing a deferred with the result (wherever it comes from). Only if all three lookups fail do you want to receive an error.

## Notes

* The code in `examples.py` is not yet tested.
* Saving the event history (in `txdlo.py`) could be made optional, seeing as most use cases are likely to be simple, with a single observer added immediately.
