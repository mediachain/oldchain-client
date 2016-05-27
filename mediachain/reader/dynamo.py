import boto3

def get_table(name):
    dynamo = boto3.resource('dynamo')
    return dynamo.Table(name)

def get_object(reference):
    table = get_table('mediachain')
    byte_string = table.get_item(Key={'multihash': reference})

    if byte_string is None:
        raise KeyError('Could not find key <%s> in Dynamo'.format(reference))

    return cbor.loads(byte_string)
