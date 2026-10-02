"""Loopback ASGI process; external HTTPS terminates at the approved existing proxy."""
import argparse
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from runtime.store import RuntimeStore
from shell.app import MemoryApp

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True)
    parser.add_argument('--origin',required=True)
    parser.add_argument('--development',action='store_true')
    parser.add_argument('--fixture',action='store_true')
    parser.add_argument('--port',type=int,default=8766)
    parser.add_argument('--trusted-edge',choices=['cloudflare'])
    args=parser.parse_args()
    os.umask(0o077)
    import uvicorn
    store=RuntimeStore(args.root,fixture=args.fixture)
    app=MemoryApp(store,origin=args.origin,development=args.development,trusted_edge=args.trusted_edge)
    uvicorn.run(app,host='127.0.0.1',port=args.port,access_log=False,proxy_headers=False,
                limit_concurrency=16,timeout_keep_alive=5,server_header=False)

if __name__=='__main__':main()
