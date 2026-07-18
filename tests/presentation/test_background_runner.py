"""Tests for the background worker thread.

A real QThread and a real QApplication are used; Qt is never mocked. Each
test waits on a threading.Event rather than sleeping, so the suite stays fast
and does not depend on timing.
"""

import threading

import pytest

from src.presentation.workers.background_runner import BackgroundRunner, _Worker

# Generous upper bound: a queued call across threads takes microseconds, so a
# test that waits this long has genuinely failed rather than run slowly.
WAIT_TIMEOUT_SECONDS = 5.0


@pytest.fixture
def runner(qapp):
    """A started runner, stopped again when the test finishes."""
    instance = BackgroundRunner()
    yield instance
    instance.stop()


def _wait(event):
    """Wait for an event, returning whether it fired before the timeout."""
    return event.wait(WAIT_TIMEOUT_SECONDS)


def test_submitted_task_runs_on_the_worker_thread(runner):
    done = threading.Event()
    runner.submit(done.set)
    assert _wait(done) is True


def test_task_runs_off_the_calling_thread(runner):
    seen = {}
    done = threading.Event()

    def record():
        seen["thread"] = threading.current_thread().ident
        done.set()

    runner.submit(record)
    _wait(done)
    assert seen["thread"] != threading.current_thread().ident


def test_arguments_are_forwarded(runner):
    received = {}
    done = threading.Event()

    def record(first, second):
        received["args"] = (first, second)
        done.set()

    runner.submit(record, "a", 2)
    _wait(done)
    assert received["args"] == ("a", 2)


def test_a_failing_task_does_not_kill_the_worker(runner):
    def boom():
        raise RuntimeError("task exploded")

    survived = threading.Event()
    runner.submit(boom)
    runner.submit(survived.set)
    assert _wait(survived) is True


def test_tasks_run_serially_in_submission_order(runner):
    order = []
    done = threading.Event()

    runner.submit(lambda: order.append(1))
    runner.submit(lambda: order.append(2))
    runner.submit(lambda: (order.append(3), done.set()))

    _wait(done)
    assert order == [1, 2, 3]


# The worker method is also exercised directly. Qt runs it on a native thread
# that coverage cannot trace, and calling it here proves the same body handles
# both a normal task and a raising one.


def test_worker_runs_the_task(qapp):
    ran = threading.Event()
    _Worker()._run(ran.set)
    assert ran.is_set() is True


def test_worker_swallows_a_failing_task(qapp):
    def boom():
        raise RuntimeError("task exploded")

    # Must return normally rather than propagating.
    assert _Worker()._run(boom) is None


def test_stop_ends_the_thread(qapp):
    instance = BackgroundRunner()
    instance.stop()
    assert instance._thread.isRunning() is False


def test_stop_is_safe_to_call_twice(qapp):
    instance = BackgroundRunner()
    instance.stop()
    instance.stop()
    assert instance._thread.isRunning() is False
