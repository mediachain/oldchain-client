import sys
import os
import subprocess
import argparse

def ingest_dirs(top):
    for (dirpath, dirnames, filenames) in os.walk(top):
        if len(dirnames) == 0 and len(filenames) > 0:
            yield dirpath

def ingest(ns):
    pids = set()
    for adir in ingest_dirs(ns.dir):
        if (len(pids) >= ns.procs):
            (pid, status) = os.wait()
            pids.remove(pid)
        print "Ingest %s" % adir
        proc = subprocess.Popen([ns.script, adir])
        pids.add(proc.pid)
    
    while len(pids) > 0:
        try:
            (pid, status) = os.wait()
            pids.remove(pid)
        except OSError, e:
            break

def main(args):
    parser = argparse.ArgumentParser(
        prog = "ingest-parallel.py",
        description = "run parallel ingestion scripts in the leaf directories of a dataset"
    )
    parser.add_argument('-n', '--processes',
                        type = int,
                        default = 10,
                        dest = 'procs',
                        help = "Number of parallel ingestion processes")
    parser.add_argument('script',
                        type = str,
                        help = "Ingest script; must accept a directory and be nice!")
    parser.add_argument('dir',
                        type = str,
                        help = "Top dataset directory")
    ns = parser.parse_args(args)
    ingest(ns)
                        
    
if __name__ == '__main__':
    main(sys.argv[1:])
