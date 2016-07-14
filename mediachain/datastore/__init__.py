from ipfs import IpfsDatastore
from rpc import get_db

__USE_IPFS_FOR_RAW_DATA = True


def set_use_ipfs_for_raw_data(use):
    global __USE_IPFS_FOR_RAW_DATA
    __USE_IPFS_FOR_RAW_DATA = use


def get_raw_datastore():
    global __USE_IPFS_FOR_RAW_DATA
    if __USE_IPFS_FOR_RAW_DATA:
        return IpfsDatastore()

    return get_db()
