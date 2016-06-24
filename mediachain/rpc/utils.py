import time
import random
from grpc.beta.interfaces import StatusCode
from grpc.framework.interfaces.face.face import AbortionError

BACKOFF_COEFF = 50.0
MAX_ATTEMPTS = 10
RETRYABLE_ERRORS = [
    StatusCode.UNAVAILABLE,
    StatusCode.UNKNOWN
]


def with_retry(func, *args, **kwargs):
    try:
        operation = str(func._method)
    except AttributeError:
        try:
            operation = func.__name__
        except AttributeError:
            operation = 'UNKNOWN'

    attempts = 1
    while True:
        try:
            output = func(*args, **kwargs)
        except AbortionError as e:
            # pylint doesn't like grpc's crazy exception hierarchy
            # pylint: disable=raising-non-exception
            if e.code not in RETRYABLE_ERRORS:
                raise e
            if attempts >= MAX_ATTEMPTS:
                print('Operation {} failed after {} attempts'.format(
                    operation, attempts
                ))
                raise e
        else:
            return output

        base_delay = min((BACKOFF_COEFF * (2 ** attempts)) / 1000.0, 60.0)
        delay = random.uniform(0, base_delay)
        print('Operation {} failed, retrying in {}s'.format(
            operation, delay))
        time.sleep(delay)
        attempts += 1
