import time
import random
from mediachain.utils.log import get_logger
from grpc.beta.interfaces import StatusCode
from grpc.framework.interfaces.face.face import AbortionError

BACKOFF_COEFF = 50.0
MAX_ATTEMPTS = 10
RETRYABLE_ERRORS = [
    StatusCode.UNAVAILABLE,
    StatusCode.UNKNOWN
]


def with_retry(func, *args, **kwargs):
    logger = get_logger(__name__)
    max_attempts = kwargs.pop('max_retry_attempts', MAX_ATTEMPTS)
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
            if attempts >= max_attempts:
                logger.error('Operation {} failed after {} attempts'.format(
                    operation, attempts
                ))
                raise e
        else:
            return output

        base_delay = min((BACKOFF_COEFF * (2 ** attempts)) / 1000.0, 60.0)
        delay = random.uniform(0, base_delay)
        logger.info('Operation {} failed, retrying in {}s'.format(
            operation, delay))
        time.sleep(delay)
        attempts += 1
