from twisted.internet.defer import Deferred, succeed, fail
from twisted.trial.unittest import TestCase

from txdlo import DeferredListObserver

_result = None


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
        When an added deferred is called, the observer is called with an
        index of zero, C{True}, and the value the deferred was called with.
        """
        global _result
        _result = None

        def observer(index, success, value):
            global _result
            _result = (index, success, value)

        dlo = DeferredListObserver()
        dlo.observe(observer)
        dlo.append(succeed(42))
        self.assertEqual((0, True, 42), _result)

    def testErroringAddedDeferredTriggersObserver(self):
        """
        When an added deferred is errbacked, the observer is called with an
        index of zero, C{False}, and the value the deferred was called with.
        """
        global _result
        _result = None

        def observer(index, success, value):
            global _result
            _result = (index, success, value)

        dlo = DeferredListObserver()
        dlo.observe(observer)
        f = fail(42)
        dlo.append(f)
        self.assertEqual(0, _result[0])
        self.assertEqual(False, _result[1])
        self.assertIdentical(42, _result[2].value)
        # Catch the failure from f so trial doesn't complain of a failing
        # deferred.
        f.addErrback(lambda value: None)

    def testMultipleDeferredsTriggerObserverAndSetCounts(self):
        """
        Multiple added deferreds must call the observer correctly and set the
        counts correctly.
        """
        global _result

        def observer(index, success, value):
            global _result
            _result = (index, success, value)

        dlo = DeferredListObserver()
        dlo.observe(observer)

        # First deferred (will not be fired until the end).
        first = Deferred()
        dlo.append(first)

        # Second deferred is called.
        _result = None
        dlo.append(succeed(42))
        self.assertEqual((1, True, 42), _result)
        self.assertEqual(1, dlo.pendingCount)
        self.assertEqual(1, dlo.successCount)

        # Third deferred (will not be fired at all).
        dlo.append(Deferred())
        self.assertEqual(2, dlo.pendingCount)

        # Fourth deferred.
        _result = None
        dlo.append(succeed(43))
        self.assertEqual((3, True, 43), _result)
        self.assertEqual(2, dlo.successCount)

        # Fire the first deferred.
        _result = None
        first.callback(44)
        self.assertEqual((0, True, 44), _result)
        self.assertEqual(3, dlo.successCount)

        # The third deferred never fired.
        self.assertEqual(1, dlo.pendingCount)
