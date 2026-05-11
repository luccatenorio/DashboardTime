import os
from supabase import create_client
URL = 'https://werkiwmegzqdsgfhcglb.supabase.co'
KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indlcmtpd21lZ3pxZHNnZmhjZ2xiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM1OTQxMDksImV4cCI6MjA4OTE3MDEwOX0.xHztZ38cpcaMop97PFwSqDQXg92AXWCEDgjBmC3xV7E'
sb = create_client(URL, KEY)
clients = sb.table('clients').select('id, cliente, observacoes').execute()
from collections import Counter
hashes = [c['observacoes'] for c in clients.data if c.get('observacoes')]
counts = Counter(hashes)
dups = {k: v for k, v in counts.items() if v > 1}
if dups:
    print('WARNING: Duplicates found!')
    for h, count in dups.items():
        print(f'Hash: {h} (Count: {count})')
        dup_clients = [c['cliente'] for c in clients.data if c.get('observacoes') == h]
        print(f'Clientes usando o mesmo hash: {dup_clients}')
else:
    print('No duplicate hashes found.')
