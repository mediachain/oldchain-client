import boto3
import cbor

def get_table(name):
    dynamo = boto3.resource('dynamodb',
                            endpoint_url='http://localhost:8000',
                            region_name='us-east-1',
                            aws_access_key_id='',
                            aws_secret_access_key='')
    return dynamo.Table(name)

def get_object(reference):
    table = get_table('Mediachain')
    obj = table.get_item(Key={'multihash': reference})

    if obj is None:
        raise KeyError('Could not find key <%s> in Dynamo'.format(reference))

    byte_string = obj['Item']['data'].value
    return cbor.loads(byte_string)
