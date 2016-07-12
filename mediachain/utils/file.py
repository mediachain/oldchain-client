import os
import platform
import tempfile
import errno


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def system_cache_dir(subdir=None):
    system = platform.system()
    if system == 'Linux':
        cache_dir = os.path.join(os.getenv('HOME'), '.cache')
    elif system == 'Darwin':
        cache_dir = os.path.join(os.getenv('HOME'), 'Library', 'Caches')
    elif system == 'Windows':  # it could happen :)
        cache_dir = os.getenv('LOCALAPPDATA')
    else:
        cache_dir = tempfile.gettempdir()
    if subdir is None:
        return cache_dir
    return os.path.join(cache_dir, subdir)
