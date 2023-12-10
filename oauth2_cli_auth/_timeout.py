import signal


class TimeoutException(Exception):
    pass


def _timeout_handler(signum, frame):
    raise TimeoutException("Operation timed out")


def _method_with_timeout(your_method, timeout_seconds=5, *args, **kwargs):
    signal.signal(signal.SIGALRM, _timeout_handler)
    signal.alarm(timeout_seconds)

    try:
        result = your_method(*args, **kwargs)
    except TimeoutException as te:
       raise te
    finally:
        signal.alarm(0)  # Reset the alarm

    return result
