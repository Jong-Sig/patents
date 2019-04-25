##
## common parsing tools
##

# get descendent text
def get_text(parent,tag,default=''):
    child = parent.find(tag)
    return (child.text or default) if child is not None else default

# get all text of node
def raw_text(par, sep=''):
    return sep.join(par.itertext()).strip()

# preserve memory
def clear(elem):
    elem.clear()
    while elem.getprevious() is not None:
        del elem.getparent()[0]

# parse mangled xml
def parse_wrapper(fpath, main_tag, parser):
    pp = XMLPullParser(tag=main_tag, events=['end'], recover=True)
    def parse_all():
        for _, pat in pp.read_events():
            if not parser(pat):
                return False
            clear(pat)
        return True

    with open(fpath, errors='ignore') as f:
        pp.feed('<root>\n')
        for line in f:
            if line.startswith('<?xml'):
                if not parse_all():
                    return False
            elif line.startswith('<!DOCTYPE') or line.startswith('<!ENTITY') or line.startswith(']>'):
                pass
            else:
                pp.feed(line)
        else:
            pp.feed('</root>\n')
            return parse_all()

# insert in chunks
class ChunkInserter:
    def __init__(self, con, table=None, cmd=None, cur=None, chunk_size=1000, output=False):
        if table is None and cmd is None:
            raise('Must specify either table or cmd')

        self.con = con
        self.cur = cur if cur is not None else con.cursor()
        self.table = table
        self.cmd = cmd
        self.chunk_size = chunk_size
        self.output = output
        self.items = []
        self.i = 0

    def insert(self,*args):
        self.items.append(args)
        if len(self.items) >= self.chunk_size:
            self.commit()
            return True
        else:
            return False

    def insertmany(self,args):
        self.items += args
        if len(self.items) >= self.chunk_size:
            self.com# standard way to pruce patent numbers (allows for all types)
def prune_patnum(pn):
    ret = re.match(r'([a-zA-Z]{1,2}|0)?([0-9]+)', pn)
    if ret is None:
        prefix = ''
        patnum = pn
    else:
        prefix, patnum = ret.groups()
        prefix = '' if prefix is None else prefix
    patnum = patnum[:7].lstrip('0')
    return prefix + patnum
mit()
            return True
        else:
            return False

    def commit(self):
        self.i += 1
        if len(self.items) == 0:
            return
        if self.cmd is None:
            nargs = len(self.items[0])
            sign = ','.join(nargs*'?')
            self.cmd = f'insert or replace into {self.table} values ({sign})'
        if self.output:
            print(f'Committing chunk {self.i} ({len(self.items)})')
        self.cur.executemany(self.cmd, self.items)
        self.con.commit()
        self.items = []

##
## patnum parsers
##

# standard way to pruce patent numbers (allows for all types)
def prune_patnum(pn):
    ret = re.match(r'([a-zA-Z]{1,2}|0)?([0-9]+)', pn)
    if ret is None:
        prefix = ''
        patnum = pn
    else:
        prefix, patnum = ret.groups()
        prefix = '' if prefix is None else prefix
    patnum = patnum[:7].lstrip('0')
    return prefix + patnum

##
## ipc parsers
##

# early grant only (1, 1.5)
def pad_ipc(ipc):
    if len(ipc) >= 8:
        return ipc[:4] + ipc[4:7].replace(' ', '0') + '/' + ipc[7:]
    else:
        return ipc

# grant only (1.5)
def gen15_ipc(ipcsec):
    yield pad_ipc(get_text(ipcsec, 'B511/PDAT'))
    for ipc in ipcsec.findall('B512'):
        yield pad_ipc(get_text(ipc, 'PDAT'))

# apply only (2)
def gen2_ipc(ipcsec):
    yield get_text(ipcsec, 'classification-ipc-primary/ipc')
    for ipc in ipcsec.findall('classification-ipc-secondary'):
        yield get_text(ipc, 'ipc')

# apply and grant (3)
def gen3a_ipc(ipcsec):
    yield get_text(ipcsec, 'main-classification')
    for ipc in ipcsec.findall('further-classification'):
        yield ipc.text or ''

def gen3g_ipc(ipcsec):
    yield pad_ipc(get_text(ipcsec, 'main-classification'))
    for ipc in ipcsec.findall('further-classification'):
        yield pad_ipc(ipc.text or '')

# apply and grant (3)
def gen3r_ipc(ipcsec):
    for ipc in ipcsec.findall('classification-ipcr'):
        yield get_text(ipc, 'section') + get_text(ipc, 'class') + get_text(ipc, 'subclass') \
            + get_text(ipc, 'main-group').zfill(3) + '/' + get_text(ipc, 'subgroup')
