from twisted.internet.defer import Deferred, succeed, fail
from twisted.trial.unittest import TestCase

from txdlo import DeferredListObserver


class TestDeferredListObserver(TestCase):

    def testEmptySetHasCountsZero(self):
        """
        An empty deferred set observer must have zero counts.
        """
        dlo = DeferredListObserver()
        self.assertEqual(0, dlo.successCount)
        self.assertEqual(0, dlo.failureCount)
        self.assertEqual(0, dlo.pendingCount)

    def testAddingADeferredResultsInPendingLengthOne(self):
        """
        A deferred set with one deferred added to it must have pending length
        one.
        """
        dlo = DeferredListObserver()
        dlo.append(Deferred())
        self.assertEqual(1, dlo.pendingCount)

    def testAddingACalledDeferredResultsInSuccessLengthOne(self):
        """
        A deferred set with a called deferred added to it must have success
        length one.
        """
        dlo = DeferredListObserver()
        dlo.append(succeed(None))
        self.assertEqual(1, dlo.successCount)

    def testAddingACalledDeferredSetsHistory(self):
        """
        A history-enabled deferred list observer with a called deferred added
        to it must have a correct length one history.
        """
        dlo = DeferredListObserver(maintainHistory=True)
        dlo.append(succeed(None))
        self.assertEqual([(0, True, None)], dlo.history)

    def testAddingAFailedDeferredResultsInFailureLengthOne(self):
        """
        A deferred set with a failed deferred added to it must have falure
        length one.
        """
        dlo = DeferredListObserver()
        f = fail(42)
        dlo.append(f)
        self.assertEqual(1, dlo.failureCount)
        # Catch the failure from f so trial doesn't complain of a failing
        # deferred.
        f.addErrback(lambda value: None)

    def testAddingADeferredAndCallingItChangesCountsCorrectly(self):
        """
        A deferred set with a deferred added to it that is then called
        must adjust its lengths correctly.
        """
        dlo = DeferredListObserver()
        deferred = Deferred()
        dlo.append(deferred)
        self.assertEqual(1, dlo.pendingCount)
        deferred.callback(42)
        self.assertEqual(0, dlo.pendingCount)
        self.assertEqual(1, dlo.successCount)
        self.assertEqual(0, dlo.failureCount)

    def testAddingADeferredAndFailingItChangesCountsCorrectly(self):
        """
        A deferred set with a deferred added to it that is then failed
        must adjust its lengths correctly.
        """
        dlo = DeferredListObserver()
        deferred = Deferred()
        dlo.append(deferred)
        self.assertEqual(1, dlo.pendingCount)
        deferred.errback(42)
        self.assertEqual(0, dlo.pendingCount)
        self.assertEqual(0, dlo.successCount)
        self.assertEqual(1, dlo.failureCount)
        # Catch the error so trial doesn't complain.
        deferred.addErrback(lambda value: None)

    def testCallingAddedDeferredTriggersObserver(self):
        """
        When an added deferred is called, the observer must be called with an
        index of zero, C{True}, and the value the deferred was called with.
        """
        result = []

        def observer(index, success, value):
            result.append((index, success, value))

        dlo = DeferredListObserver()
        dlo.observe(observer)
        dlo.append(succeed(42))
        self.assertEqual((0, True, 42), result[0])

    def testCallingAddedDeferredTriggersMultipleObservers(self):
        """
        When an added deferred is called, all observers must be called with an
        index of zero, C{True}, and the value the deferred was called with.
        Observers must be called in the order they were added to the
        L{DeferredListObserver} instance.
        """
        result = []

        def observer1(index, success, value):
            result.append((index, success, value, 1))

        def observer2(index, success, value):
            result.append((index, success, value, 2))

        dlo = DeferredListObserver()
        dlo.observe(observer1)
        dlo.observe(observer2)
        dlo.append(succeed(42))
        self.assertEqual(
            [
                (0, True, 42, 1),
                (0, True, 42, 2)
            ],
            result)

    def testHistoryReplayWithNoHistoryAvailable(self):
        """
        When an observer is added with a request that the event history be
        replayed to it but the L{DeferredListObserver} is not maintaining the
        history, a C{RuntimeError} must be raised.
        """
        dlo = DeferredListObserver(maintainHistory=False)
        self.assertRaises(RuntimeError, dlo.observe, lambda: None,
                          replayHistory=True)

    def testHistoryReplay(self):
        """
        When an added deferred is called before any observer is present and
        then an observer is added, the observer must be called with the details
        of the event that occurred before it was added.
        """
        result = []

        def observer(index, success, value):
            result.append((index, success, value))

        dlo = DeferredListObserver(maintainHistory=True)
        dlo.append(succeed(42))

        dlo.observe(observer, replayHistory=True)
        self.assertEqual((0, True, 42), result[0])

    def testHistoryNotReplayed(self):
        """
        When an added deferred is called before any observer is present and
        then an observer is added but history replay is not wanted, the
        observer must not be called with the details of the event that
        occurred before it was added.
        """
        result = []

        def observer(index, success, value):
            result.append(RuntimeError('oops'))

        dlo = DeferredListObserver(maintainHistory=True)
        dlo.append(succeed(42))

        dlo.observe(observer, replayHistory=False)
        self.assertEqual([], result)

    def testErroringAddedDeferredTriggersObserver(self):
        """
        When an added deferred is errbacked, the observer is called with an
        index of zero, C{False}, and the value the deferred was called with.
        """
        result = []

        def observer(index, success, value):
            result.append((index, success, value))

        dlo = DeferredListObserver()
        dlo.observe(observer)
        f = fail(42)
        dlo.append(f)
        self.assertEqual(0, result[0][0])
        self.assertEqual(False, result[0][1])
        self.assertIdentical(42, result[0][2].value)
        # Catch the failure from f so trial doesn't complain of a failing
        # deferred.
        f.addErrback(lambda value: None)

    def testMultipleDeferredsTriggerObserverAndSetsCounts(self):
        """
        Multiple added deferreds must call the observer correctly and set the
        counts correctly.
        """
        result = []

        def observer(index, success, value):
            result.append((index, success, value))

        dlo = DeferredListObserver()
        dlo.observe(observer)

        # First deferred (will not be fired until the end).
        first = Deferred()
        dlo.append(first)

        # Second deferred is called.
        dlo.append(succeed(42))
        self.assertEqual((1, True, 42), result[0])
        del result[0]
        self.assertEqual(1, dlo.pendingCount)
        self.assertEqual(1, dlo.successCount)

        # Third deferred (will not be fired at all).
        dlo.append(Deferred())
        self.assertEqual(2, dlo.pendingCount)

        # Fourth deferred.
        dlo.append(succeed(43))
        self.assertEqual((3, True, 43), result[0])
        del result[0]
        self.assertEqual(2, dlo.successCount)

        # Fire the first deferred.
        first.callback(44)
        self.assertEqual((0, True, 44), result[0])
        del result[0]
        self.assertEqual(3, dlo.successCount)

        # The third deferred never fired.
        self.assertEqual(1, dlo.pendingCount)

    def testDeferredCallbackValuesArePropagated(self):
        """
        A deferred added to a C{DeferredListObserver} must have its callback
        value propagated correctly.
        """
        result = []

        def callback(value):
            result.append(value)

        dlo = DeferredListObserver()
        deferred = Deferred().addCallback(callback)
        dlo.append(deferred)
        value = object()
        deferred.callback(value)
        self.assertIs(value, result[0])

    def testDeferredErrbackValuesArePropagated(self):
        """
        A deferred added to a C{DeferredListObserver} must have its errback
        value propagated correctly.
        """
        result = []

        def errback(value):
            result.append(value)

        dlo = DeferredListObserver()
        deferred = Deferred().addErrback(errback)
        dlo.append(deferred)
        value = object()
        deferred.errback(value)
        self.assertIs(value, result[0].value)
