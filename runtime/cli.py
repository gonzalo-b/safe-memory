"""Local operator commands. Owner password is read interactively, never an argument."""
import argparse
import getpass
from pathlib import Path
import sys
from runtime.store import RuntimeStore

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',required=True)
    parser.add_argument('--fixture',action='store_true')
    sub=parser.add_subparsers(dest='command',required=True)
    owner=sub.add_parser('create-owner');owner.add_argument('--username',required=True);owner.add_argument('--name',required=True)
    backup=sub.add_parser('backup');backup.add_argument('destination')
    restore=sub.add_parser('restore');restore.add_argument('backup')
    args=parser.parse_args()
    if args.command=='restore':RuntimeStore.restore(args.backup,args.root);print('Restore complete. Sessions revoked; sources require reauthorization.');return
    store=RuntimeStore(args.root,fixture=args.fixture)
    if args.command=='create-owner':
        password=getpass.getpass('Memory password (12+ characters): ')
        if password!=getpass.getpass('Repeat password: '):raise SystemExit('Passwords do not match.')
        print('Owner created:',store.create_owner(args.username,password,args.name))
    else:store.backup(args.destination);print('Private backup completed.')

if __name__=='__main__':main()
