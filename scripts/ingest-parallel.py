import sys
import os
import subprocess
import time
import argparse

def ingest_dirs(top):
    for (dirpath, dirnames, filenames) in os.walk(top):
        if len(dirnames) == 0 and len(filenames) > 0:
            yield dirpath

def ingest(ns):
    procs = dict()
    def spawn(adir):
        print "Ingest %s" % adir
        proc = subprocess.Popen([ns.script, adir])
        procs[proc.pid] = proc
    
    def reap_some():
        done = []
        while True:
            for (pid, proc) in procs.items():
                if proc.poll() is not None:
                    done.append(pid)
            
            if len(done) > 0:
                for pid in done:
                    del procs[pid]
                break
            else:
                time.sleep(1)
        
    for adir in ingest_dirs(ns.dir):
        if (len(procs) < ns.procs):
            spawn(adir)
        else:
            reap_some()
            spawn(adir)
    
    while len(procs) > 0:
        reap_some()

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
