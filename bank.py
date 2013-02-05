#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Welcome to ⊔net!
#-----------------------------------------------------------------------------
#  © Copyright 2013 ⊔Foundation
#    This file is part of ⊔net.
#
#    ⊔net is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    ⊔net is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with ⊔net.  If not, see <http://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------------
"_"

import re, os, sys, urllib.parse, hashlib, http.client, base64, dbm, binascii, datetime, zlib, functools, subprocess
#from Crypto.Cipher import AES

__digest__ = base64.urlsafe_b64encode(hashlib.sha1(open(__file__, 'r', encoding='utf8').read().encode('utf8')).digest())[:5]

__embedded_fonts__ = ('cmr10', 'cmr17')
__fonts__ = ('Helvetica', 'Times-Roman', 'Courier', 'Times-Bold', 'Helvetica-Bold', 'Courier-Bold', 'Times-Italic', 'Helvetica-Oblique', 
             'Courier-Oblique', 'Times-BoldItalic', 'Helvetica-BoldOblique', 'Courier-BoldOblique', 'Symbol') + __embedded_fonts__

__email__ = 'laurent.fournier@cupfoundation.net'
__url__   = 'http://cupfoundation.net'

_SVGNS    = 'xmlns="http://www.w3.org/2000/svg"'
_XLINKNS  = 'xmlns:xlink="http://www.w3.org/1999/xlink"'
RSA_E = 65537
MAX_ARG_SIZE = 2000

def reg(value):
    " function attribute is a way to access matching group in one line test "
    reg.v = value
    return value

def init_db(db):
    "_"
    if not os.path.isfile(db):
        d = dbm.open(db[:-3], 'c')
        d['__DIGEST__'], d['NB_TR'] = __digest__, '0'
        d.close()

def log(s, ip=''):
    "Append to head log file"
    logf, now = '/cup/log', '%s' % datetime.datetime.now()
    if not os.path.isfile(logf): open(logf, 'w', encoding='utf8').write('%s|%s Log file Creation\n' % (now[:-7], ip) )     
    cont = open(logf, 'r', encoding='utf8').read()
    open(logf, 'w', encoding='utf8').write('%s|%s|%s\n%s' % (now[:-7], ip, s, cont))


def pdf_receipt(td, byr, slr, prc, tr):
    "_"
    content = [[(100, 300, '32F1', 'Invoice'),
                (420, 18, '12F1', td), 
                (20, 400, '14F1', 'Buyer: %s' % byr), 
                (20, 450, '14F1', 'Seller: %s' % slr), 
                (20, 500, '14F1', 'Intangible Good: example'), 
                (480, 600, '12F1', 'Price: %s' % prc),
                (10, 782, '10F1', 'Transaction: %s' % tr),
                ]]
    a = updf(595, 842)
    return a.gen(content)

def application(environ, start_response):
    "wsgi server app"
    mime, o, db, today = 'text/plain; charset=utf8', 'Error:', '/cup/bank.db', '%s' % datetime.datetime.now()
    init_db(db)
    if environ['REQUEST_METHOD'].lower() == 'post':
        raw, way = urllib.parse.unquote(environ['wsgi.input'].read().decode('utf8')), 'post'
    else:
        raw, way = urllib.parse.unquote(environ['QUERY_STRING']), 'get'
    log(raw[:10] + '...', environ['REMOTE_ADDR'])
    d = dbm.open(db[:-3], 'c')
    if len(raw) < MAX_ARG_SIZE:
        if reg(re.match(r'^(reg|register)/([^/]{3,50})/([^/]{9,17})/([^/]{680,685})/([^/]{680,685})$', raw, re.U)):
            # checks both id and public key not already used and local id is valid
            own, uid, pbk, sig = reg.v.group(2), reg.v.group(3), reg.v.group(4), reg.v.group(5)
            Por, Bor, Oor, Uid = b'P_' + bytes(own, 'utf8'), b'B_' + bytes(own, 'utf8'), b'O_' + bytes(own, 'utf8'), b'U_' + bytes(uid, 'utf8')
            if Por in d.keys():
                o += 'public key already exists for %s !' % own 
            elif (uid != 'anonymous') and (Uid in d.keys()):
                o += 'user id already registered for %s !' % own 
            elif verify(RSA_E, b64toi(bytes(pbk, 'ascii')), ' '.join((today[:10], own, uid)), bytes(sig, 'ascii')):
                d[Oor] = '100' if uid != 'anonymous' and uid[:2] == 'fr' and int(uid[-2:]) == (97 - int(uid[2:-2])%97) else '0' # french id!
                d[Por], d[Bor], d[Uid], o = pbk, '0', own, 'Public key id registration OK for \'%s\'' % own 
            else:
                o += ' something wrong in user registration!'
        elif reg(re.match(r'^(ig|immaterial|good)/([^/]{3,50})/([^/]{3,80})/([^/]{1,12})/([^/]{1,12})/([^/]{680,685})$', raw, re.U)):
            # checks
            own, iid, p1, pf, sig = reg.v.group(2), reg.v.group(3), reg.v.group(4), reg.v.group(5), reg.v.group(6)
            Iig, Ppk = b'I_' + bytes(iid, 'utf8'), bytes('P_%s' % own, 'utf8')
            if Iig in d.keys():
                o += 'IG id already set!' 
            elif verify(RSA_E, b64toi(d[Ppk]), ' '.join((today[:10], own, iid, p1, pf)), bytes(sig, 'ascii')):
                d[Iig], o = '/'.join((today[:10], p1, pf, own)), 'IG id registration OK from \'%s\'' % own
            else:
                o += 'ig registration fail!'
        elif reg(re.match(r'^(tr|trans|transaction)/([^/]{3,50})/([^/]{3,50})/([^/]{1,12})/([^/]{26})/([^/]{680,685})$', raw, re.U)):
            # checks that price is positive, transaction not replicated, and that account is funded
            byr, slr, prc, td, sig = reg.v.group(2), reg.v.group(3), float(reg.v.group(4)), reg.v.group(5), reg.v.group(6)
            Bby, Bsr, Pby, Oby, Ttr = b'B_'+bytes(byr, 'utf8'), b'B_' + bytes(slr, 'utf8'), b'P_' + bytes(byr, 'utf8'), b'O_' + bytes(byr, 'utf8'), b'T_' + bytes(sig[:20], 'ascii'), 
            if (prc > 0) and \
                    not (Ttr in d.keys()) and \
                    verify(RSA_E, b64toi(d[Pby]), ' '.join((byr, slr, '%s' % prc, td)), bytes(sig, 'ascii')) and \
                    float(d[Bby]) - prc > - float(d[Oby]):
                d[Bby], d[Bsr] = '%f' % (float(d[Bby]) - prc), '%f' % (float(d[Bsr]) + prc)
                d['NB_TR'] = '%d' % (int(d['NB_TR'])+1)
                d[Ttr] = '/'.join((td, byr, slr, '%s' % prc)) 
                o, mime = pdf_receipt(td[:19], bytes(byr,'utf8'), bytes(slr,'utf8'), prc, Ttr[2:].decode('ascii')), 'application/pdf'
            else:
                o += 'transaction!'
        elif reg(re.match(r'^(buy)/([^/]{3,50})/([^/]{3,80})/([^/]{26})/([^/]{680,685})$', raw, re.U)):
            # checks 
            byr, ig, td, sig = reg.v.group(2), reg.v.group(3), reg.v.group(4), reg.v.group(5)
            Bby, Pby, Oby, Ttr = b'B_'+bytes(byr, 'utf8'), b'P_' + bytes(byr, 'utf8'), b'O_' + bytes(byr, 'utf8'), b'T_' + bytes(sig[:20], 'ascii'), 
            Iig = b'I_' + bytes(ig, 'utf8')
            if verify(RSA_E, b64toi(d[Pby]), ' '.join((byr, ig, td)), bytes(sig, 'ascii')) and Iig in d.keys():
                tab = d[Iig].decode('utf8').split('/')
                prc, slr = float(tab[1]), tab[3]
                o = 'bought ig OK from %s at price %f' % (slr, prc)
            else:
                o += 'ig transaction!'
        elif reg(re.match(r'^(receipt)/([^/]{10,100})$', raw, re.U)):
            tid = reg.v.group(2)
            Ttr = b'T_' + bytes(tid, 'ascii')
            if Ttr in d.keys():
                #o, mime = pdf_receipt(td[:19], bytes(byr,'utf8'), bytes(slr,'utf8'), prc, Ttr[2:].decode('ascii')), 'application/pdf'
                o, mime = pdf_receipt(today[:19], 'jhjhjghg', 'blable', '0', Ttr[2:].decode('ascii')), 'application/pdf'
            else:
                o += 'receipt not found!'
        elif reg(re.match(r'^(state|statement|balance)/([^/]{3,50})/([^/]{680,685})$', raw, re.U)):
            own, sig = reg.v.group(2), reg.v.group(3)
            Bow, Pow = b'B_'+bytes(own, 'utf8'), b'P_' + bytes(own, 'utf8') 
            if verify(RSA_E, b64toi(d[Pow]), ' '.join((own, today[:10])), bytes(sig, 'ascii')):
                o, a = '%s\towner: %s\t\t         balance: \t%9.2f⊔\n' % (today[:19], own, float(d[Bow].decode('ascii'))), []
                for x in d.keys():
                    if reg(re.match('T_(.*)$', x.decode('ascii'))):
                        tab = d[x].decode('utf8').split('/')
                        if own in (tab[1], tab[2]):
                            (t, tg) = ('\t', tab[2]) if own == tab[1] else ('\t'*3, tab[1])
                            a.append('%s %s %25s%s%9.2f⊔\n' % (tab[0][:19], x[2:].decode('ascii'), tg, t, float(tab[3])))
                o += ''.join(sorted(a, reverse=True))
            else:
                o += 'statement reading!'            
        elif way == 'get':
            if raw.lower() in ('source', 'src', 'download'):
                o = open(__file__, 'r', encoding='utf8').read()
            elif raw.lower() in ('help', 'about'):
                o = 'Welcome to ⊔net!\n\nHere is the Help in PDF format soon!'
            elif raw.lower() == 'reset':
                subprocess.Popen(('rm', '/cup/bank.db')).communicate() # Of course this is temporary available for testing!
                o = 'RESET DATABASE OK!'
            elif raw.lower() in ('log',):
                o = open('/cup/log', 'r', encoding='utf8').read()                
            elif raw.lower() in ('list',):
                o = ''
                for x in d.keys():
                    if reg(re.match('I_(.*)$', x.decode('utf8'))):
                        tab = d[x].decode('utf8').split('/')
                        o += '%s\t%s\t%7.2f⊔%9.2f\n' % (tab[0], x[2:].decode('utf8'), float(tab[1]), float(tab[2]))
            elif reg(re.match(r'^secret_url(.*)$', raw, re.U)):
                o, mime = open('/cup/sample.pdf', 'rb').read(), 'application/pdf'
            else:
                o, mime = frontpage(today, environ['REMOTE_ADDR']), 'application/xhtml+xml; charset=utf8'
    else:
        o += 'arg too long'
    d.close()
    start_response('200 OK', [('Content-type', mime)])
    return [o if mime == 'application/pdf' else o.encode('utf8')] 

def favicon():
    "_"
    code = '<svg %s n="%s"><path stroke-width="4" fill="none" stroke="Dodgerblue" d="M3,1L3,14L13,14L13,1"/></svg>' % (_SVGNS, datetime.datetime.now())
    tmp = base64.b64encode(code.encode('utf8'))
    return '<link xmlns="http://www.w3.org/1999/xhtml" rel="shortcut icon" type="image/svg+xml" href="data:image/svg+xml;base64,%s"/>\n' % tmp.decode('utf8')

def frontpage(today, ip):
    "not in html!"
    d = dbm.open('/cup/bank')
    nb, su, ck , tr, di, ni = 0, 0, 0, int(d['NB_TR']), d['__DIGEST__'], 0
    for x in d.keys():
        if reg(re.match('B_(.*)$', x.decode('utf8'))):
            nb += 1
            su += abs(float(d[x])/2)
            ck += float(d[x])
        if reg(re.match('I_', x.decode('utf8'))):
            ni += 1
    d.close()
    o = '<?xml version="1.0" encoding="utf8"?>\n' 
    o += '<svg %s %s>\n' % (_SVGNS, _XLINKNS) + favicon()
    o += '<style type="text/css">@import url(http://fonts.googleapis.com/css?family=Schoolbell);svg{max-height:100;}text,path{stroke:none;fill:Dodgerblue;font-family:helvetica;}text.foot{font-size:18pt;fill:gray;text-anchor:middle;}text.alpha{font-family:Schoolbell;fill:#F87217;text-anchor:middle}text.note{fill:#CCC;font-size:9pt;text-anchor:end;}</style>\n'
    o += '<a xlink:href="%s"><path stroke-width="0" d="M10,10L10,10L10,70L70,70L70,10L60,10L60,60L20,60L20,10z"/></a>\n' % __url__
    o += '<text x="80" y="70" font-size="45" title="banking for intangible goods">Bank</text>\n'
    o += '<text class="alpha" font-size="16pt" x="92"  y="25" title="still in security test phase!">Beta</text>\n'
    o += '<text class="alpha" font-size="64pt" x="50%" y="33%"><tspan title="only http GET or POST!">No https, no html,</tspan><tspan x="50%" dy="100" title="only SVG and PDF!">no JavaScript,</tspan><tspan x="50%" dy="120" title="better privacy also!">better security!</tspan></text>\n'
    o += '<text class="foot" x="50%%" y="50" title="today">%s</text>\n' % today[:19]
    o += '<text class="foot" x="16%%" y="80%%" title="registered users">%04d users</text>\n' % nb
    o += '<text class="foot" x="38%%" y="80%%" title="">%06d transactions</text>\n' % tr
    o += '<text class="foot" x="62%%" y="80%%" title="number of registered Intangible Goods">%04d IGs</text>\n' % ni
    o += '<text class="foot" x="84%%" y="80%%" title="absolute value">Volume: %09.2f ⊔</text>\n' % su
    o += '<a xlink:href="bank?src" ><text class="note" x="160" y="98%" title="on GitHub (https://github.com/pelinquin/cup) hack it, share it!">Download the source code!</text></a>\n'
    if ip == '127.0.0.1': 
        o += '<text class="note" x="160" y="90"  title="my ip adress">local server</text>\n'
    o += '<a xlink:href="bank?help"><text class="note" x="99%" y="20"  title="help">Help</text></a>\n'
    o += '<a xlink:href="u?pi"     ><text class="note" x="99%" y="40"  title="at home!">Host</text></a>\n'            
    o += '<a xlink:href="bank?log" ><text class="note" x="99%" y="60"  title="log file">Log</text></a>\n'
    o += '<a xlink:href="bank?list"><text class="note" x="99%" y="80"  title="ig list">List</text></a>\n'
    o += '<text class="note" x="50%%" y="98%%" title="you can use that server!">Status: <tspan fill="%s</tspan></text>\n' % ('green">OK' if (abs(ck) <= 0.00001) else 'red">Error!')
    o += '<text class="note" x="99%%" y="95%%" title="database|program" >Digest: %s|%s</text>\n' % (di.decode('utf8'), __digest__.decode('utf8'))
    o += '<text class="note" x="99%%" y="98%%" title="or visit \'%s\'">Contact: %s</text>\n' % (__url__, __email__) 
    return o + '</svg>'

def format_cmd(post, cmd):
    co = http.client.HTTPConnection(host)    
    if post:
        co.request('POST', '/bank', urllib.parse.quote(cmd))
    else:
        co.request('GET', '/bank?' + urllib.parse.quote(cmd))
    return co.getresponse().read().decode('utf8')    

def format_pdf(post, cmd, f):
    co = http.client.HTTPConnection(host)    
    if post:
        co.request('POST', '/bank', urllib.parse.quote(cmd))
    else:
        co.request('GET', '/bank?' + urllib.parse.quote(cmd))
    res = co.getresponse().read()
    #return res
    open('%s.pdf' % f, 'wb').write(res)
    return 'OK'

def register(owner, iduser='anonymous', host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')    
    ki, kb = [b64toi(x) for x in ds[owner].split()], [x for x in ds[owner].split()]
    ds.close()
    s = sign(ki[1], ki[2], ' '.join((td[:10], owner, iduser)))
    assert (verify(RSA_E, ki[2], ' '.join((td[:10], owner, iduser)), s))
    cmd = '/'.join(('reg', owner, iduser, kb[2].decode('ascii'), s.decode('ascii')))
    return format_cmd(post, cmd)

def register_ig(owner, idig, p1, pf, host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')
    ki = [b64toi(x) for x in ds[owner].split()]
    ds.close()
    s = sign(ki[1], ki[2], ' '.join((td[:10], owner, idig, '%s' % p1, '%s' % pf)))
    cmd = '/'.join(('ig', owner, idig, '%s' % p1, '%s' % pf, s.decode('ascii')))
    return format_cmd(post, cmd)    

def transaction(byr, slr, prc, host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')
    ki = [b64toi(x) for x in ds[byr].split()]
    ds.close()
    s = sign(ki[1], ki[2], ' '.join((byr, slr, '%s' % prc, td)))
    cmd = '/'.join(('transaction', byr, slr, '%s' % prc, td, s.decode('ascii')))
    return format_pdf(post, cmd, 'tata')

def buy(byr, ig, host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')
    ki = [b64toi(x) for x in ds[byr].split()]
    ds.close()
    s = sign(ki[1], ki[2], ' '.join((byr, ig, td)))
    cmd = '/'.join(('buy', byr, ig, td, s.decode('ascii')))
    return format_cmd(post, cmd)

def prep_transaction(byr, slr, prc, host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')
    ki = [b64toi(x) for x in ds[byr].split()]
    ds.close()
    s = sign(ki[1], ki[2], ' '.join((byr, slr, '%s' % prc, td)))
    cmd = '/'.join(('transaction', byr, slr, '%s' % prc, td, s.decode('ascii')))
    return 'http://%s/bank?%s' % (host, urllib.parse.quote(cmd))

def prep_receipt(tid, host='localhost', post=False):
    "_"
    cmd = '/'.join(('receipt', tid))
    return 'http://%s/bank?%s' % (host, urllib.parse.quote(cmd))

def statement(own, host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')
    ki = [b64toi(x) for x in ds[own].split()]
    ds.close()
    s = sign(ki[1], ki[2], ' '.join((own, td[:10])))
    cmd = '/'.join(('statement', own, s.decode('ascii')))
    return format_cmd(post, cmd)
            
def itob64(n):
    "utility to transform int to base64"
    c = hex(n)[2:]
    if len(c)%2: c = '0'+c
    return re.sub(b'=*$', b'', base64.urlsafe_b64encode(bytes.fromhex(c)))

def b64toi(c):
    "transform base64 to int"
    if c == '': return 0
    return int.from_bytes(base64.urlsafe_b64decode(c + b'='*((4-(len(c)%4))%4)), 'big')

def H(*tab):
    "hash"
    return int(hashlib.sha1(b''.join(bytes('%s' % i, 'utf8') for i in tab)).hexdigest(), 16)
 
def sign(d, n, msg):
    "_"
    return itob64(pow(H(msg), d, n))

def verify(e, n, msg, s):
    "_"
    return (pow(b64toi(s), e, n) == H(msg)) 

def encrypt(e, n, msg):
    "_"
    skey = os.urandom(16)
    iskey = int(binascii.hexlify(skey), 16)
    print("KEY", len(skey), iskey)
    aes = AES.new(skey, AES.MODE_ECB)
    c, r = itob64(pow(iskey, e, n)), len(msg)
    print ("CR", len(c), r)
    raw = bytes(((r)&0xff, (r>>8)&0xff, (r>>16)&0xff, (r>>24)&0xff, (len(c))&0xff, (len(c)>>8)&0xff))
    return raw + c + aes.encrypt(msg+b'\0'*(16-len(msg)%16))

def decrypt(d, n, raw):
    "_"
    lmsg, l2 = raw[0]+(raw[1]<<8)+(raw[2]<<16)+(raw[3]<<24), raw[4]+(raw[5]<<8)
    ckey, cmsg = raw[6:l2+6], raw[l2+6:]
    c = hex(pow(b64toi(ckey), d, n))[2:]
    if len(c)%2: c = '0'+c
    aes2 = AES.new(bytes.fromhex(c), AES.MODE_ECB)
    return aes2.decrypt(cmsg)[:lmsg]

class updf:
    def __init__(self, pagew, pageh, binary=True):
        self.pw = pagew
        self.ph = pageh
        self.mx, self.my = 25, 25
        self.binary = binary
        self.i = 0
        self.pos = []
        self.o = b'%PDF-1.4\n%'
        fpath = '/cup/fonts/'
        self.afm = [AFM(open(fpath + '%s.afm' % f)) for f in __fonts__]
        self.pfb = [open(fpath + '%s.pfb' % f, 'rb').read() for f in __embedded_fonts__]
    
    def add(self, line):
        self.pos.append(len(self.o))
        self.i += 1
        self.o += bytes('%d 0 obj<<%s>>endobj\n' % (self.i, line), 'ascii')
    
    def addnull(self):
        self.pos.append(len(self.o))
        self.i += 1
        self.o += bytes('%d 0 obj 0 endobj\n' % (self.i), 'ascii')
    
    def addarray(self, a):
        self.pos.append(len(self.o))
        self.i += 1
        self.o += bytes('%d 0 obj [%s] endobj\n' % (self.i, ''.join(['%s '%i for i in a])), 'ascii')
    
    def adds(self, stream):
        self.pos.append(len(self.o))
        self.i += 1
        if self.binary: stream = zlib.compress(stream) 
        fil = '/Filter/FlateDecode' if self.binary else ''
        self.o += bytes('%d 0 obj<</Length %d%s>>stream\n' % (self.i, len(stream), fil), 'ascii')
        self.o += stream
        self.o += b'endstream endobj\n'

    def adds3(self, stream):
        self.pos.append(len(self.o))
        self.i += 1
        fil = '/Filter/FlateDecode' if self.binary else ''
        len1, len2, len3 = 0, 0, 0
        m = re.search(b'currentfile eexec', stream)
        if m: len1 = m.start()+18
        m = re.search(b'0000000000', stream)
        if m: len2 = m.start() - len1
        len3 = len(stream) - len1 - len2
        if self.binary: stream = zlib.compress(stream) 
        ltot = len(stream)
        self.o += bytes('%d 0 obj<</Length1 %d/Length2 %d/Length3 %d/Length %d%s>>stream\n' % (self.i, len1, len2, len3, ltot, fil), 'ascii')
        self.o += stream
        self.o += b'endstream endobj\n'

    def kern(self, s, a):
        ""
        return ')-338('.join([a.k(l) for l in s.split()])

    def sgen(self, par):
        "stream parser"
        ff, other = par[2].split('F'), False
        o = '1 0 0 1 %s %s Tm /F%s %s Tf %s TL ' % (par[0]+self.mx, self.ph-par[1]-self.my, ff[1], ff[0], 1.2*int(ff[0]))
        o += '(%s)Tj ' % par[3]
        
        #for m in re.compile(r'(/(\d+)F(\d+)\{([^\}]*)\}|([^\n/]+))').finditer(par[3]):
        #    if m.group(5):
        #        o += '%s[(%s)]TJ ' % ('T* ' if other else '', self.kern(m.group(5), self.afm[int(ff[1])-1])) 
        #        other = True
        #    if m.group(2) and m.group(4) and m.group(3):
        #        other = False
        #        o += '/F%s %s Tf [(%s)]TJ /F%s %s Tf ' % (m.group(3), m.group(2), self.kern(m.group(4), self.afm[int(ff[1])-1]), ff[1], ff[0])
        return o

    def gen(self, document):
        "generate a valid binary PDF file, ready for printing!"
        np = len(document)
        self.o += b'\xBF\xF7\xA2\xFE\n' if self.binary else b'ASCII!\n'
        self.add('/Linearized 1.0/L 1565/H [570 128]/O 11/E 947/N 111/T 1367')
        ref, kids, seenall, fref, h, firstp = [], '', {}, [], {}, 0
        for p, page in enumerate(document):
            t = bytes('BT 1 w 0.9 0.9 0.9 RG %s %s %s %s re S 0 0 0 RG 0 Tc ' % (self.mx, self.my, self.pw-2*self.mx, self.ph-2*self.my), 'ascii')
            t += b'1.0 1.0 1.0 RG 0.8 0.9 1.0 rg 44 600 505 190 re B 0.0 0.0 0.0 rg '
            t += b'1.0 1.0 1.0 rg 1 0 0 1 60 680 Tm /F1 60 Tf (Put your Ads here)Tj 0.0 0.0 0.0 rg '
            for par in page: t += bytes(self.sgen(par), 'ascii')
            t += b'ET\n'
            #t1 = bytes('/P <</MCID 0>> BDC BT 1 0 0 1 10 20 Tm /F1 12 Tf (HELLO)Tj ET EMC /Link <</MCID 1>> BDC BT 1 0 0 1 100 20 Tm /F1 16 Tf (With a link)Tj ET EMC', 'ascii')
            self.adds(t)
            ref.append('%s 0 R' % self.i)
        for p, page in enumerate(document):
            seen = {}
            for par in page:
                for m in re.compile('/\d+F(\d+)\{').finditer('/%s{%s' % (par[2], par[3])):
                    seen[m.group(1)] = True
            fref.append(' '.join(seen))
            seenall.update(seen)
        fc, lc = 0, 255 
        for f in seenall:
            #print (f, len(__fonts__)-3)
            if int(f) > len(__fonts__)-1:
            #if int(f) > len(__fonts__)-3:
                print (f)
                self.addarray([self.afm[int(f)-1].w(i) for i in range(fc, lc+1)])
                indice = int(f)-len(__fonts__)+2
                self.adds3(self.pfb[int(f)-len(__fonts__)+2])
                bb = self.afm[int(f)-1]._header[b'FontBBox']
                self.add('/Type/FontDescriptor/FontName/%s/Flags 4/FontBBox[%s]/Ascent 704/CapHeight 674/Descent -194/ItalicAngle 0/StemV 109/FontFile %s 0 R' % (__fonts__[int(f)-1], ''.join(['%s '% i for i in bb]), self.i))
                self.add('/Type/Font/Subtype/Type1/BaseFont/%s/FirstChar %d/LastChar %s/Widths %s 0 R/FontDescriptor %d 0 R'% (__fonts__[int(f)-1], fc, lc, self.i-2 , self.i))
            else:
                self.addnull()
                self.addnull()
                self.addnull()
                self.add('/Type/Font/Subtype/Type1/BaseFont/%s' % (__fonts__[int(f)-1]))
            h[f] = self.i
        #nba = ['www.google.com']
        nba = []
        for a in nba:
            #self.add('/Type/Annot/Subtype/Link/Border[16 16 1]/Rect[150 600 270 640]/Dest[10 0 R/Fit]')
            self.add('/Type/Annot/Subtype/Link/Border[16 16 1]/Rect[150 600 270 640]/A<</Type/Action/S/URI/URI(http://pelinquin/u?beamer)>> ')
            #self.add('/Type/Annot/Subtype/Link/Border[16 16 1]/Rect[150 600 270 640]/A<</S/URL/URL(./u?beamer)>> ')
            #self.add('/Type/Annot/Subtype/Link/Border[16 16 1]/K<</Type/MCR/MCID 0/Pg 10 0 R>>/A<</S/URL/URL(http://pelinquin/u?beamer)>> ')
        aref = self.i
        pref = np + self.i + 1
        for p, page in enumerate(document):
            fo = functools.reduce(lambda y, i: y+'/F%s %d 0 R' % (i, h[i]), fref[p].split(), '')
            #self.add('/Type/Page/Parent %d 0 R/Contents %s/Annots[%d 0 R]/Resources<</Font<<%s>> >> ' % (pref, ref[p], aref, fo))
            self.add('/Type/Page/Parent %d 0 R/Contents %s/Resources<</Font<<%s>> >> ' % (pref, ref[p], fo))
            kids += '%s 0 R ' % self.i
            if p == 1: firstp = self.i
        self.add('/Type/Pages/MediaBox[0 0 %s %s]/Count %d/Kids[%s]' % (self.pw, self.ph, np, kids[:-1]))
        pagesid = self.i
        self.add('/Type/Outlines/First %s 0 R/Last %s 0 R/Count 1' % (self.i+2, self.i+2))
        self.add('/Title (Document)/Parent %d 0 R/Dest [%d 0 R /Fit]' % (self.i, firstp)) 
        #self.add('/FS /URL /F (http://www.google.com)')
        #self.add('/URLS[%s 0 R]' % self.i)
        self.add('/Type/Catalog/Pages %d 0 R/Outlines %d 0 R/Names %d 0 R' % (pagesid, self.i-3, self.i))  
        n, size = len(self.pos), len(self.o)
        self.o += functools.reduce(lambda y, i: y+bytes('%010d 00000 n \n' % i, 'ascii'), self.pos, bytes('xref\n0 %d\n0000000000 65535 f \n' % (n+1), 'ascii'))
        self.o += bytes('trailer<</Size %d/Root %d 0 R>>startxref %s\n' % (n+1, self.i, size), 'ascii') + b'%%EOF'
        return self.o

## AFM PARSING

def _to_int(x):
    return int(float(x))

def _to_str(x):
    return x.decode('utf8')

def _to_list_of_ints(s):
    s = s.replace(b',', b' ')
    return [_to_int(val) for val in s.split()]

def _to_list_of_floats(s):
    return [float(val) for val in s.split()]

def _to_bool(s):
    if s.lower().strip() in (b'false', b'0', b'no'): return False
    else: return True

def _sanity_check(fh):
    """Check if the file at least looks like AFM. If not, raise :exc:`RuntimeError`."""
    pos = fh.tell()
    try:
        line = bytes(fh.readline(), 'ascii')
    finally:
        fh.seek(pos, 0)
    # AFM spec, Section 4: The StartFontMetrics keyword [followed by a version number] must be the first line in the file, and the
    # EndFontMetrics keyword must be the last non-empty line in the file. We just check the first line.
    if not line.startswith(b'StartFontMetrics'): raise RuntimeError('Not an AFM file')

def _parse_header(fh):
    """Reads the font metrics header (up to the char metrics) and returns
    a dictionary mapping *key* to *val*.  *val* will be converted to the
    appropriate python type as necessary; eg:
        * 'False'->False
        * '0'->0
        * '-168 -218 1000 898'-> [-168, -218, 1000, 898]
    Dictionary keys are
      StartFontMetrics, FontName, FullName, FamilyName, Weight,ItalicAngle, IsFixedPitch, FontBBox, UnderlinePosition, UnderlineThickness, Version, Notice, EncodingScheme, CapHeight, XHeight, Ascender, Descender, StartCharMetrics"""
    headerConverters = {
        b'StartFontMetrics': float,
        b'FontName': _to_str,
        b'FullName': _to_str,
        b'FamilyName': _to_str,
        b'Weight': _to_str,
        b'ItalicAngle': float,
        b'IsFixedPitch': _to_bool,
        b'FontBBox': _to_list_of_ints,
        b'UnderlinePosition': _to_int,
        b'UnderlineThickness': _to_int,
        b'Version': _to_str,
        b'Notice': _to_str,
        b'EncodingScheme': _to_str,
        b'CapHeight': float, # Is the second version a mistake, or
        b'Capheight': float, # do some AFM files contain 'Capheight'? -JKS
        b'XHeight': float,
        b'Ascender': float,
        b'Descender': float,
        b'StdHW': float,
        b'StdVW': float,
        b'StartCharMetrics': _to_int,
        b'CharacterSet': _to_str,
        b'Characters': _to_int,
        }
    d = {}
    while 1:
        line = bytes(fh.readline(), 'ascii')
        if not line: break
        line = line.rstrip()
        if line.startswith(b'Comment'): continue
        lst = line.split(b' ', 1 )
        key = lst[0]
        if len( lst ) == 2:
            val = lst[1]
        else:
            val = b''
        #key, val = line.split(' ', 1)
        try: d[key] = headerConverters[key](val)
        except ValueError:
            continue
        except KeyError:
            continue
        if key==b'StartCharMetrics': return d
    raise RuntimeError('Bad parse')

def _parse_char_metrics(fh):
    """Return a character metric dictionary.  Keys are the ASCII num of
    the character, values are a (*wx*, *name*, *bbox*) tuple, where
    *wx* is the character width, *name* is the postscript language
    name, and *bbox* is a (*llx*, *lly*, *urx*, *ury*) tuple.
    This function is incomplete per the standard, but thus far parses all the sample afm files tried."""
    ascii_d = {}
    name_d  = {}
    while 1:
        line = bytes(fh.readline(), 'ascii')
        if not line: break
        line = line.rstrip()
        if line.startswith(b'EndCharMetrics'): return ascii_d, name_d
        vals = line.split(b';')[:4]
        if len(vals) !=4 : raise RuntimeError('Bad char metrics line: %s' % line)
        num = _to_int(vals[0].split()[1])
        wx = float(vals[1].split()[1])
        name = vals[2].split()[1]
        name = name.decode('ascii')
        bbox = _to_list_of_floats(vals[3][2:])
        bbox = list(map(int, bbox))
        # Workaround: If the character name is 'Euro', give it the corresponding
        # character code, according to WinAnsiEncoding (see PDF Reference).
        if name == 'Euro':
            num = 128
        if num != -1:
            ascii_d[num] = (wx, name, bbox)
        name_d[name] = (wx, bbox)
    raise RuntimeError('Bad parse')

def _parse_kern_pairs(fh):
    """Return a kern pairs dictionary; keys are (*char1*, *char2*) tuples and values are the kern pair value.  For example, a kern pairs line like
    ``KPX A y -50`` will be represented as:: d[ ('A', 'y') ] = -50"""
    line = bytes(fh.readline(), 'ascii')
    if not line.startswith(b'StartKernPairs'): raise RuntimeError('Bad start of kern pairs data: %s'%line)
    d = {}
    while 1:
        line = bytes(fh.readline(), 'ascii')
        if not line: break
        line = line.rstrip()
        if len(line)==0: continue
        if line.startswith(b'EndKernPairs'):
            fh.readline()  # EndKernData
            return d
        vals = line.split()
        if len(vals)!=4 or vals[0]!=b'KPX':
            raise RuntimeError('Bad kern pairs line: %s'%line)
        c1, c2, val = _to_str(vals[1]), _to_str(vals[2]), float(vals[3])
        d[(c1,c2)] = val
    raise RuntimeError('Bad kern pairs parse')

def _parse_composites(fh):
    """Return a composites dictionary.  Keys are the names of the
    composites.  Values are a num parts list of composite information,
    with each element being a (*name*, *dx*, *dy*) tuple.  Thus a
    composites line reading: CC Aacute 2 ; PCC A 0 0 ; PCC acute 160 170 ;
    will be represented as:: d['Aacute'] = [ ('A', 0, 0), ('acute', 160, 170) ]"""
    d = {}
    while 1:
        line = fh.readline()
        if not line: break
        line = line.rstrip()
        if len(line)==0: continue
        if line.startswith(b'EndComposites'):
            return d
        vals = line.split(b';')
        cc = vals[0].split()
        name, numParts = cc[1], _to_int(cc[2])
        pccParts = []
        for s in vals[1:-1]:
            pcc = s.split()
            name, dx, dy = pcc[1], float(pcc[2]), float(pcc[3])
            pccParts.append( (name, dx, dy) )
        d[name] = pccParts
    raise RuntimeError('Bad composites parse')

def _parse_optional(fh):
    """Parse the optional fields for kern pair data and composites
    return value is a (*kernDict*, *compositeDict*) which are the
    return values from :func:`_parse_kern_pairs`, and
    :func:`_parse_composites` if the data exists, or empty dicts
    otherwise"""
    optional = { b'StartKernData' : _parse_kern_pairs, b'StartComposites' :  _parse_composites}
    d = {b'StartKernData':{}, b'StartComposites':{}}
    while 1:
        line = bytes(fh.readline(), 'ascii')
        if not line: break
        line = line.rstrip()
        if len(line)==0: continue
        key = line.split()[0]
        if key in optional: d[key] = optional[key](fh)
    l = ( d[b'StartKernData'], d[b'StartComposites'] )
    return l

def parse_afm(fh):
    """Parse the Adobe Font Metics file in file handle *fh*. Return value is a (*dhead*, *dcmetrics*, *dkernpairs*, *dcomposite*) tuple where
    *dhead* is a :func:`_parse_header` dict, *dcmetrics* is a
    :func:`_parse_composites` dict, *dkernpairs* is a
    :func:`_parse_kern_pairs` dict (possibly {}), and *dcomposite* is a
    :func:`_parse_composites` dict (possibly {}) """
    _sanity_check(fh)
    dhead =  _parse_header(fh)
    dcmetrics_ascii, dcmetrics_name = _parse_char_metrics(fh)
    doptional = _parse_optional(fh)
    return dhead, dcmetrics_ascii, dcmetrics_name, doptional[0], doptional[1]

class AFM:

    def __init__(self, fh):
        """Parse the AFM file in file object *fh*"""
        (dhead, dcmetrics_ascii, dcmetrics_name, dkernpairs, dcomposite) = parse_afm(fh)
        self._header = dhead
        self._kern = dkernpairs
        self._metrics = dcmetrics_ascii
        self._metrics_by_name = dcmetrics_name
        self._composite = dcomposite

    def stw(self, s):
        """ Return the string width (including kerning) """
        totalw = 0
        namelast = None
        for c in s:
            wx, name, bbox = self._metrics[ord(c)]
            l,b,w,h = bbox
            try: kp = self._kern[ (namelast, name) ]
            except KeyError: kp = 0
            totalw += wx + kp
            namelast = name
        return totalw 

    def w(self, c):
        """ Return the string width (including kerning) """
        try: w = self._metrics[c][0]
        except KeyError: w = 0
        return w

    def k0(self, s):
        """ Return PDF kerning string """
        o, l = '(', None
        for c in s + ' ':
            try: kp = - self._kern[(l, c)]
            except KeyError: kp = 0
            if l: o += '%s)%d(' % (l, kp) if kp else l
            l = c
        return o + ')'

    def k(self, s):
        """ Return PDF kerning string """
        o, l = '', None
        for c in s + ' ':
            try: kp = - self._kern[(l, c)]
            except KeyError: kp = 0
            if l: o += '%s)%d(' % (l, kp) if kp else l
            l = c
        return o 

if __name__ == '__main__':
    popu = {
        'Pelinquin':        'fr167071927202809', 
        'Laurent Fournier': 'fr167071927202809', 
        'Alice':            'fr267070280099999', 
        'Valérie':          'fr264070287098888', 
        'Bob':              'fr161070280095555', 
        'Carl⊔':            'fr177070284098888', 
        }
    
    man, woman, ig, host = 'Laurent Fournier', 'Valérie', 'toto您tata', 'localhost'
    #host = 'pi.pelinquin.fr'
    print (register(man, popu[man], host))
    print (register('Alice', 'anonymous', host))
    print (register(woman, 'anonymous', host))    
    print (register('Bob', 'anonymous', host))    
    print (transaction(man, woman, 2.15, host))
    #print (prep_transaction(man, woman, 2.15, host))
    #print (prep_receipt('jHoUFfy4BuW283hsOpnZ', host))
    print (transaction(woman, man,  3.2, host))
    print (transaction(woman, man,  2.2, host))
    print (register_ig(man, ig, 0.56, 100000, host))    
    print (register_ig(woman, 'mon album', 1.5, 200000, host))    
    print (buy(man, ig, host))
    #print (statement(woman), host)    

    sys.exit()

# End ⊔net!
