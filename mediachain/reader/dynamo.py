import boto3
import cbor

def get_table(name, aws_config):
    dynamo = boto3.resource('dynamodb', **aws_config)
    return dynamo.Table(name)

def get_object(reference, aws_config):
    table = get_table('Mediachain', aws_config)
    obj = table.get_item(Key={'multihash': reference})

    if obj is None:
        raise KeyError('Could not find key <%s> in Dynamo'.format(reference))

    byte_string = obj['Item']['data'].value
    return cbor.loads(byte_string)
