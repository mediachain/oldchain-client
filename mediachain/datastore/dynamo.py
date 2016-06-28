import botocore
import boto3
import cbor
import copy
import functools
import time
import random
from base58 import b58encode
from boto3.dynamodb.types import Binary
from botocore.exceptions import ClientError as DynamoError
from multihash import encode as multihash_encode, SHA2_256

from mediachain.datastore.data_objects import Record, MultihashReference

__AWS_CONFIG=dict()
__DB_INSTANCE=None

def set_aws_config(cfg):
    global __AWS_CONFIG
    __AWS_CONFIG = cfg

def get_aws_config():
    global __AWS_CONFIG
    return __AWS_CONFIG

def get_db():
    global __DB_INSTANCE
    if __DB_INSTANCE is None:
        __DB_INSTANCE = DynamoDatastore()

    return __DB_INSTANCE


BACKOFF_COEFF = 50.0
MAX_ATTEMPTS = 10
RETRYABLE_ERRORS = [
    "InternalServerError",
    "ProvisionedThroughputExceededException"
]


def with_retry(func, *args, **kwargs):
    operation = func.__name__
    attempts = 1
    while True:
        try:
            output = func(*args, **kwargs)
        except DynamoError as e:
            error_code = e.response['Error']['Code']
            if error_code not in RETRYABLE_ERRORS:
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


class DynamoDatastore(object):
    def __init__(self, **kwargs):
        cfg = copy.deepcopy(get_aws_config())
        cfg.update(kwargs)
        self.mediachain_table_name = cfg.pop('mediachain_table_name')
        self.dynamo = boto3.resource('dynamodb', **cfg)

    def get_table(self, name):
        return self.dynamo.Table(name)

    def mediachain_table(self):
        return self.get_table(self.mediachain_table_name)

    def put(self, data_object):
        # TODO: implement chunked writes for large objects
        table = self.mediachain_table()
        put_with_retry = functools.partial(with_retry, table.put_item)

        if isinstance(data_object, Record):
            key = data_object.multihash_base58()
            content = data_object.to_cbor_bytes()
        else:
            hash_bytes = multihash_encode(data_object, SHA2_256)
            key = b58encode(str(hash_bytes))
            content = data_object

        put_with_retry(Item={'multihash': key,
                             'data': Binary(content)})
        return key

    def get(self, ref):
        table = self.mediachain_table()
        get_with_retry = functools.partial(with_retry, table.get_item)

        if isinstance(ref, MultihashReference):
            ref_multihash = ref.multihash_base58()
        else:
            ref_multihash = ref

        item = get_with_retry(Key={'multihash': ref_multihash})
        if item is None or 'Item' not in item:
            raise KeyError('Could not find key {} in DynamoDB'.format(ref))
        byte_string = bytes(item['Item']['data'])
        try:
            return cbor.loads(byte_string)
        except ValueError:
            return byte_string

