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

import re, os, sys, urllib.parse, hashlib, http.client, base64, dbm, binascii, datetime, zlib, functools
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
#import kern

__digest__ = base64.urlsafe_b64encode(hashlib.sha1(open(__file__, 'r', encoding='utf-8').read().encode('utf-8')).digest())[:5]

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

def application(environ, start_response):
    "wsgi server app"
    mime, o, db, today = 'text/plain; charset=utf-8', 'Error:', '/cup/bank.db', '%s' % datetime.datetime.now()
    init_db(db)
    if environ['REQUEST_METHOD'].lower() == 'post':
        raw, way = urllib.parse.unquote(environ['wsgi.input'].read().decode('utf-8')), 'post'
    else:
        raw, way = urllib.parse.unquote(environ['QUERY_STRING']), 'get'
    d = dbm.open(db[:-3], 'c')
    if len(raw) < MAX_ARG_SIZE:
        if reg(re.match(r'^\s*TEST\s*(\(\s*"([^"]{3,})"\s*\))\s*$', raw, re.U)):
            a = eval(reg.v.group(1))
            assert (a == reg.v.group(2))
            o = '1 ARG %s %s' % (way, raw)
        elif reg(re.match(r'^\s*TEST\s*(\(\s*"([^"]{3,})"\s*,\s*"([^"]{3,})"\s*\))\s*$', raw, re.U)):
            a = eval(reg.v.group(1))
            assert (a[0] == reg.v.group(2) and a[1] == reg.v.group(3)) 
            o = '2 ARGS %s %s' % (way, raw)
        elif reg(re.match(r'^\s*TEST\s*(\(\s*"([^"]{3,})"\s*,\s*"([^"]{3,})"\s*,\s*"([^"]{3,})"\s*\))\s*$', raw, re.U)):
            a = eval(reg.v.group(1))
            assert (a[0] == reg.v.group(2) and a[1] == reg.v.group(3) and a[2] == reg.v.group(4)) 
            o = '3 ARGS %s %s' % (way, raw)
        elif reg(re.match(r'^(reg|register)/([^/]+)/([^/]+)/([^/]+)/([^/]+)$', raw, re.U)):
            own, uid, pbk, sig = reg.v.group(2), reg.v.group(3), reg.v.group(4), reg.v.group(5)
            pk, bal, ovr = b'P_' + bytes(own, 'utf8'), b'B_' + bytes(own, 'utf8'), b'O_' + bytes(own, 'utf8')
            if pk in d.keys():
                o += 'public key already set!' 
            elif verify(RSA_E, b64toi(bytes(pbk, 'ascii')), ' '.join((today[:10], own, uid)), bytes(sig, 'ascii')):
                d[pk], d[bal], d[ovr], o = pbk, '0', '100', 'Public key id registration OK'
            else:
                o += 'registration!'
        elif way == 'get':
            if raw.lower() in ('source', 'src', 'download'):
                o = open(__file__, 'r', encoding='utf-8').read()
            if raw.lower() in ('help', 'about'):
                o = 'Welcome to ⊔net!\n\nHere is the Help in PDF format soon!'
            elif raw.lower() in ('log', 'transaction'):
                o, a = 'Welcome to ⊔net!\n\nPublic log of all transactions\n', []
                for x in d.keys():
                    if reg(re.match('(\d{4}.*)$', x.decode('utf-8'))):
                        dat = d[x].split()
                        a.append('%s %s...\n' % (reg.v.group(1), dat[3].decode('utf-8')))
                b = sorted(a, reverse=True)
                for x in b: o += x
            else:
                o, mime = frontpage(today), 'application/xhtml+xml; charset=utf-8'
    else:
        o += 'arg too long'
    d.close()
    start_response('200 OK', [('Content-type', mime)])
    return [o.encode('utf-8')] 

def favicon():
    "_"
    code = '<svg %s n="%s"><path stroke-width="4" fill="none" stroke="Dodgerblue" d="M3,1L3,14L13,14L13,1"/></svg>' % (_SVGNS, datetime.datetime.now())
    tmp = base64.b64encode(code.encode('utf-8'))
    return '<link rel="shortcut icon" type="image/svg+xml" xlink:href="data:image/svg+xml;base64,%s"/>\n' % tmp.decode('utf-8')

def frontpage(today):
    "not in html!"
    d = dbm.open('/cup/bank')
    nb, su, ck , tr, di = 0, 0, 0, int(d['NB_TR']), d['__DIGEST__']
    for x in d.keys():
        if reg(re.match('B_(.*)$', x.decode('utf-8'))):
            nb += 1
            su += abs(float(d[x])/2)
            ck += float(d[x])
    d.close()
    o = '<?xml version="1.0" encoding="utf-8"?>\n' 
    o += '<svg %s %s>\n' % (_SVGNS, _XLINKNS) + favicon()
    o += '<style type="text/css">@import url(http://fonts.googleapis.com/css?family=Schoolbell);svg{max-height:100;}text,path{stroke:none;fill:Dodgerblue;font-family:helvetica;}text.foot{font-size:16pt;fill:gray;text-anchor:middle;}text.alpha{font-family:Schoolbell;fill:#F87217;text-anchor:middle}text.note{fill:#CCC;font-size:9pt;text-anchor:end;}</style>\n'
    o += '<a xlink:href="%s"><path stroke-width="0" d="M10,10L10,10L10,70L70,70L70,10L60,10L60,60L20,60L20,10z"/></a>\n' % __url__
    o += '<text x="90" y="70" font-size="45" title="banking for intangible goods">Bank</text>\n'
    o += '<text class="alpha" font-size="16pt" x="92"  y="25" title="still in security test phase!">Beta</text>\n'
    o += '<text class="alpha" font-size="64pt" x="50%" y="40%"><tspan title="and no \'html\' either!">No \"https\", no JavaScript,</tspan><tspan x="50%" dy="100" title="better privacy also!">better security!</tspan></text>\n'
    o += '<text class="foot" x="50%%"  y="40" title="today">%s</text>\n' % today[:19]
    o += '<text class="foot" x="20%%" y="80%%" title="registered users">%04d users</text>\n' % nb
    o += '<text class="foot" x="40%%" y="80%%" title="">%06d transactions</text>\n' % tr
    o += '<text class="foot" x="60%%" y="80%%" title="absolute value">Volume: %09.2f ⊔</text>\n' % su
    o += '<text class="foot" x="80%%" y="80%%" title="number of registered Intangible Goods">%04d IG</text>\n' % (0)
    o += '<a xlink:href="bank?src" ><text class="note" x="160" y="98%" title="on GitHub (https://github.com/pelinquin/cup) hack it, share it!">Download the source code!</text></a>\n'
    o += '<a xlink:href="u?pi"     ><text class="note" x="99%" y="40"  title="at home!">Host</text></a>\n'            
    o += '<a xlink:href="bank?log" ><text class="note" x="99%" y="60"  title="log file">Log</text></a>\n'
    o += '<a xlink:href="bank?help"><text class="note" x="99%" y="20"  title="help">Help</text></a>\n'
    o += '<text class="note" x="50%%" y="98%%" title="you can use that server!">Status: <tspan fill="green">%s</tspan></text>\n' % ('OK' if (abs(ck) <= 0.00001) else 'error!')
    o += '<text class="note" x="99%%" y="95%%" title="database|program" >Digest: %s|%s</text>\n' % (di.decode('utf-8'), __digest__.decode('utf-8'))
    o += '<text class="note" x="99%%" y="98%%" title="or visit \'%s\'">Contact: %s</text>\n' % (__url__, __email__) 
    return o + '</svg>'

def register(owner, iduser='anonymous', post=False, host='localhost'):
    co, td = http.client.HTTPConnection(host), '%s' % datetime.datetime.now()
    ds = dbm.open('/u/sk')    
    ki, kb = [b64toi(x) for x in ds[owner].split()], [x for x in ds[owner].split()]
    ds.close()
    s = sign(ki[1], ki[2], ' '.join((td[:10], owner, iduser)))
    assert (verify(RSA_E, ki[2], ' '.join((td[:10], owner, iduser)), s))
    cmd = '/'.join(('reg', owner, iduser, kb[2].decode('ascii'), s.decode('ascii')))
    if post:
        co.request('POST', '/bank', urllib.parse.quote(cmd))
    else:
        co.request('GET', '/bank?' + urllib.parse.quote(cmd))
    return co.getresponse().read().decode('utf-8')
            
def application_old(environ, start_response):
    "wsgi server app"
    mime = 'text/plain; charset=utf-8'
    if not os.path.isfile('/u/bank.db'):
        d = dbm.open('/u/bank', 'c')
        d['__DIGEST__'], d['NB_TR'] = __digest__, '0'
        d.close()
    if environ['REQUEST_METHOD'].lower() == 'post':
        today = '%s' % datetime.datetime.now()
        raw, o = urllib.parse.unquote(environ['wsgi.input'].read().decode('utf-8')), 'error!'
        o = 'error! %s' % raw
        d = dbm.open('/u/bank', 'c')
        # TRANSACTION
        if reg(re.match(r'^TR(\(\s*"([^"]{3,30})"\s*,\s*"([^"]{3,30})".*)$', raw, re.U)): 
            t, byr, slr = eval(reg.v.group(1)), b'BAL_' + bytes(reg.v.group(2), 'utf-8') , b'BAL_' + bytes(reg.v.group(3), 'utf-8')
            if (len(t) == 5) and (type(t[2]).__name__ in  ('float', 'int')) and (type(t[0]).__name__ == 'str') and (type(t[1]).__name__ == 'str'):
                pk = bytes('PUB_%s' % t[0], 'utf-8')
                if pk in d.keys() and len(raw) < MAX_ARG_SIZE:
                    if t[3] not in d.keys():
                        if verify(RSA_E, b64toi(d[pk]), '%s %s %s %s' % tuple(t[0:4]), t[4]):
                            if float(d[byr]) - float(t[2]) > -float(d[b'OVR_' + bytes(t[0], 'utf-8')]):
                                d[byr] = '%f' % (float(d[byr]) - t[2] if byr in d.keys() else -t[2])
                                d[slr] = '%f' % (float(d[slr]) + t[2] if slr in d.keys() else  t[2])
                                d['NB_TR'] = '%d' % (int(d['NB_TR'])+1)
                                d[t[3]] = bytes(t[0], 'utf-8') + b' ' + bytes(t[1], 'utf-8') + b' ' + bytes('%s' % t[2], 'ascii') + b' ' + t[4][:8]
                                o = 'Transaction OK %s' % float(t[2])
                            else:
                                o = 'Unfunded account! (limit: -%s)' % d[b'OVR_' + bytes(t[0], 'utf-8')]
                        else:
                            o = 'Wrong buyer signature!'
                    else:
                        o = 'Duplicate transaction!'
                else:
                    o = 'Unknown public key!'
        # USER REGISTRATION
        elif reg(re.match(r'^PK(\(\s*"([^\"]{3,30})".*)$', raw, re.U)): 
            t, name = eval(reg.v.group(1)), b'PUB_' + bytes(reg.v.group(2), 'utf8')
            assert (t[0] == reg.v.group(2))
            if name in d.keys():
                o = 'Public key already set!' 
            elif (len(t) == 3) and verify(RSA_E, b64toi(bytes(t[1], 'utf-8')), '%s %s' % (today[:10], t[0]), t[2]):
                d[name], d['BAL_'+t[0]], o = t[1], '0', 'Public key anonymous registration OK'
                d[b'OVR_' + bytes(t[0], 'utf-8')] = '10'
            elif (len(t) == 4) and verify(RSA_E, b64toi(bytes(t[1], 'utf-8')), '%s %s %s' % (today[:10], t[0], t[2]), t[3]):
                d[name], d['BAL_'+t[0]], o = t[1], '0', 'Public key id registration OK'
                d[b'OVR_' + bytes(t[0], 'utf-8')] = '100'
            else:
                o = 'Error in registration!'
        # IG REGISTRATION
        elif reg(re.match(r'^IG(\(\s*"([^\"]{3,30})".*)$', raw, re.U)): 
            t = eval(reg.v.group(1))
            nameig = b'IG_' + bytes(t[1], 'utf8')
            assert (t[0] == reg.v.group(2))
            if nameig in d.keys():
                o = 'IG already registered!' 
            elif len(t) == 5: 
                pk = bytes('PUB_%s' % t[0], 'utf-8')
                if verify(RSA_E, b64toi(d[pk]), '%s %s %s %s %s' % (today[:10], t[0], t[1], t[2], t[3]), t[4]):
                    d[nameig] = '%s %s %s' % (t[0], t[2], t[3])
                    o = 'IG registration OK'
                else:
                    o = 'Verrif fail in IG registration!'
            else:
                o = 'Error in IG registration!'
        # READ BALANCE
        elif reg(re.match(r'^BAL(\(\s*"([^\"]{3,30})".*)$', raw, re.U)): 
            t, name = eval(reg.v.group(1)), b'BAL_' + bytes(reg.v.group(2), 'utf8')
            assert (t[0] == reg.v.group(2))
            if name in d.keys():
                pk = bytes('PUB_%s' % t[0], 'utf-8')
                if verify(RSA_E, b64toi(d[pk]), today[:10], t[2]):
                    if t[1]:
                        o, a = '%s balance: %s ⊔\n' % (today, d[name].decode('utf-8')), []
                        for x in d.keys():
                            if reg(re.match('(\d{4}.*)$', x.decode('utf-8'))):
                                tab = d[x].split()
                                if bytes(t[0], 'utf-8') in (tab[0], tab[1]):
                                    a.append('%s %s...\n' % (reg.v.group(1), d[x].decode('utf-8')))
                        b = sorted(a, reverse=True)
                        for x in b: o += x
                    else:
                        o = '%s' % d[name].decode('utf-8')                        
                else:
                    o = 'Bad signature!'
        elif reg(re.match(r'^UPDATE$', raw)):
            o = 'provision update from Github'
        else:
            o = 'Test! %s' % raw
        d.close()
    else:
        arg = urllib.parse.unquote(environ['QUERY_STRING'])
        if arg.lower() in ('source', 'src', 'download'):
            o = open(__file__, 'r', encoding='utf-8').read()
        elif arg.lower() in ('stat', 'statistics'):
            d = dbm.open('/u/bank',)
            nb, su, ck = 0, 0, 0
            for x in d.keys():
                if reg(re.match('BAL_(.*)$', x.decode('utf-8'))):
                    nb += 1
                    su += abs(float(d[x])/2)
                    ck += float(d[x])
            o =  'Number of login: %d\n' % nb
            o += 'Total transactions: %f\n' % su
            o += 'Check integrity (should be zero): %f\n' % ck
            o += 'Number of transactions: %d\n' % int(d['NB_TR'])
            o += 'Digest :%s-%s\n' % (d['__DIGEST__'].decode('utf-8'), __digest__.decode('ascii'))
            d.close()
        elif arg.lower() in ('log', 'transaction'):
            d, o, a = dbm.open('/u/bank',), '', []
            for x in d.keys():
                if reg(re.match('(\d{4}.*)$', x.decode('utf-8'))):
                    dat = d[x].split()
                    a.append('%s %s...\n' % (reg.v.group(1), dat[3].decode('utf-8')))
            b = sorted(a, reverse=True)
            for x in b: o += x
            d.close()
        elif arg.lower() in ('about', 'help'):
            o = 'Welcome to ⊔net!\n\n'
            o += 'First you need your own 4096 bits long RSA key (used GPG or sshgen to generate it)\n\n'
            o += '! You will never have to send us your private key; keep it secure, out of Internet access\n\n'
            o += 'The main integrity rule is that the sum of all acounts balance is always null.\n\n'
            o += 'HTTP POST only request:\n'
            o += '\tPK(agent, public_key)\n'
            o += '\tTR(buyer, seller, price, current_date, buyer_signature) with signed message = \'seller|price|\' returns status (OK,KO)\n'
            o += '\tBAL(owner, owner_signature) with signed message = \'date_of_the_day\' returns balance\n'
            o += 'HTTP GET request:\n\tstat\n\tsource\n\tlog\n'
    start_response('200 OK', [('Content-type', mime)])
    return [o.encode('utf-8')] 

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
    return int(hashlib.sha1(b''.join(bytes('%s' % i, 'utf-8') for i in tab)).hexdigest(), 16)
 
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

def read_balance(owner, verbose, host='localhost'):
    "_"
    co = http.client.HTTPConnection(host)
    ds = dbm.open('/u/sk')    
    td = '%s' % datetime.datetime.now()
    k = [b64toi(x) for x in ds[owner].split()]
    s = sign(k[1], k[2], td[:10])
    co.request('POST', '/bank', 'BAL("%s", %s, %s)' % (urllib.parse.quote(owner), verbose, s))
    ds.close()
    return co.getresponse().read().decode('utf-8')

def register_ig(owner, idig, p1, pf, host='localhost'):
    "_"
    co = http.client.HTTPConnection(host)
    td = '%s' % datetime.datetime.now()
    ds = dbm.open('/u/sk')
    k = [b64toi(x) for x in ds[owner].split()]
    s = sign(k[1], k[2], '%s %s %s %s %s' % (td[:10], owner, idig, p1, pf))
    co.request('POST', '/bank', 'IG("%s", "%s", %s, %s, %s)' % (urllib.parse.quote(owner), urllib.parse.quote(idig), p1, pf, s))
    ds.close()
    return co.getresponse().read().decode('utf-8')

def transaction(byr, slr, prc, host='localhost'):
    "_"
    co = http.client.HTTPConnection(host)
    ds = dbm.open('/u/sk')    
    td = '%s' % datetime.datetime.now()
    k = [b64toi(x) for x in ds[byr].split()]
    s = sign(k[1], k[2], '%s %s %s %s' %(byr, slr, prc, td))
    co.request('POST', '/bank', 'TR("%s", "%s", %s, "%s", %s)' % (urllib.parse.quote(byr), urllib.parse.quote(slr), prc, td, s))
    ds.close()
    return co.getresponse().read().decode('utf-8')

def buy(byr, ig, host='localhost'):
    "_"
    co = http.client.HTTPConnection(host)
    ds = dbm.open('/u/sk')    
    td = bytes('%s' % datetime.datetime.now(), 'ascii')
    k = [b64toi(x) for x in ds[byr].split()]
    s = sign(k[1], k[2], '%s %s %s' %(byr, ig, td))
    co.request('POST', '/bank', 'BUY("%s", "%s", %s, %s)' % (urllib.parse.quote(byr), urllib.parse.quote(ig), td, s))
    ds.close()
    return co.getresponse().read().decode('utf-8')

class updf:
    def __init__(self, pagew, pageh, binary=True):
        self.pw = pagew
        self.ph = pageh
        self.mx, self.my = 25, 25
        self.binary = binary
        self.i = 0
        self.pos = []
        self.o = b'%PDF-1.4\n%'
        #afmpath = pfbpath = '/usr/share/fonts/type1/gsfonts/' 
        afmpath, pfbpath = '/home/laurent/afm/', '/home/laurent/pfb/'
        self.afm = [kern.AFM(open(afmpath + '%s.afm' % f)) for f in __fonts__]
        self.pfb = [open(pfbpath + '%s.pfb' % f, 'rb').read() for f in __embedded_fonts__]
    
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
        for m in re.compile(r'(/(\d+)F(\d+)\{([^\}]*)\}|([^\n/]+))').finditer(par[3]):
            if m.group(5):
                o += '%s[(%s)]TJ ' % ('T* ' if other else '', self.kern(m.group(5), self.afm[int(ff[1])-1])) 
                other = True
            if m.group(2) and m.group(4) and m.group(3):
                other = False
                o += '/F%s %s Tf [(%s)]TJ /F%s %s Tf ' % (m.group(3), m.group(2), self.kern(m.group(4), self.afm[int(ff[1])-1]), ff[1], ff[0])
        return o

    def gen(self, document):
        "generate a valid binary PDF file, ready for printing!"
        np = len(document)
        self.o += b'\xBF\xF7\xA2\xFE\n' if self.binary else b'ASCII!\n'
        self.add('/Linearized 1.0/L 1565/H [570 128]/O 11/E 947/N 111/T 1367')
        ref, kids, seenall, fref, h, firstp = [], '', {}, [], {}, 0
        for p, page in enumerate(document):
            t = bytes('BT 1 w 0.9 0.9 0.9 RG %s %s %s %s re S 0 0 0 RG 0 Tc ' % (self.mx, self.my, self.pw-2*self.mx, self.ph-2*self.my), 'ascii')
            for par in page: t += bytes(self.sgen(par), 'ascii')
            t += b'ET\n'
            t1 = bytes('/P <</MCID 0>> BDC BT 1 0 0 1 10 20 Tm /F1 12 Tf (HELLO)Tj ET EMC /Link <</MCID 1>> BDC BT 1 0 0 1 100 20 Tm /F1 16 Tf (With a link)Tj ET EMC', 'ascii')
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
            if int(f) > len(__fonts__)-1:
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
        nba = ['www.google.com']
        for a in nba:
            #self.add('/Type/Annot/Subtype/Link/Border[16 16 1]/Rect[150 600 270 640]/Dest[10 0 R/Fit]')
            self.add('/Type/Annot/Subtype/Link/Border[16 16 1]/Rect[150 600 270 640]/A<</Type/Action/S/URI/URI(http://pelinquin/u?beamer)>> ')
            #self.add('/Type/Annot/Subtype/Link/Border[16 16 1]/Rect[150 600 270 640]/A<</S/URL/URL(./u?beamer)>> ')
            #self.add('/Type/Annot/Subtype/Link/Border[16 16 1]/K<</Type/MCR/MCID 0/Pg 10 0 R>>/A<</S/URL/URL(http://pelinquin/u?beamer)>> ')
        aref = self.i
        pref = np + self.i + 1
        for p, page in enumerate(document):
            fo = functools.reduce(lambda y, i: y+'/F%s %d 0 R' % (i, h[i]), fref[p].split(), '')
            self.add('/Type/Page/Parent %d 0 R/Contents %s/Annots[%d 0 R]/Resources<</Font<<%s>> >> ' % (pref, ref[p], aref, fo))
            kids += '%s 0 R ' % self.i
            if p == 1: firstp = self.i
        self.add('/Type/Pages/MediaBox[0 0 %s %s]/Count %d/Kids[%s]' % (self.pw, self.ph, np, kids[:-1]))
        pagesid = self.i
        self.add('/Type/Outlines/First %s 0 R/Last %s 0 R/Count 1' % (self.i+2, self.i+2))
        self.add('/Title (Document)/Parent %d 0 R/Dest [%d 0 R /Fit]' % (self.i, firstp)) 
        self.add('/FS /URL /F (http://www.google.com)')
        self.add('/URLS[%s 0 R]' % self.i)
        self.add('/Type/Catalog/Pages %d 0 R/Outlines %d 0 R/Names %d 0 R' % (pagesid, self.i-3, self.i))  
        n, size = len(self.pos), len(self.o)
        self.o += functools.reduce(lambda y, i: y+bytes('%010d 00000 n \n' % i, 'ascii'), self.pos, bytes('xref\n0 %d\n0000000000 65535 f \n' % (n+1), 'ascii'))
        self.o += bytes('trailer<</Size %d/Root %d 0 R>>startxref %s\n' % (n+1, self.i, size), 'ascii') + b'%%EOF'
        return self.o

if __name__ == '__main__':
    popu = {
        'Pelinquin': 'fr167071927202809', 
        'Alice':     'fr267070280099999', 
        'Valérie':   'fr264070287098888', 
        'Bob':       'fr161070280095555', 
        'Carl⊔':     'fr177070284098888', 
        }
    
    ds = dbm.open('/u/sk', 'c')
    for a in popu:
        if bytes(a,'utf-8') not in ds.keys():
            print ('generate key for', a)
            k = RSA.generate(4096, os.urandom)
            ds[a] = bytes(' '.join([itob64(x).decode('ascii') for x in (k.e, k.d, k.n)]), 'ascii')
    ds.close()

    #host = 'pi.pelinquin.fr'
    #print (register_ig('Alice', 'toto您tata', 0.56, 100000, host))
    #print (transaction('Alice',   'Bob', 1.65, host))
    #print (transaction('Valérie', 'Carl⊔', 4.65, host))
    #print (transaction('Bob',     'Valérie', 2.15, host))
    #print (transaction('Bob',     'Daniel', 4.65, host))
    #print (buy('Bob', 'toto您tata', host))
    #print (read_balance('Daniel', False, host))
    #print (transaction('Daniel', 'Valérie', 44.65, host))
    #print (read_balance('Valérie', False, host))

    man = 'Pelinquin'
    #print (register(man, popu[man], True,  'localhost'))
    #print (register(man, popu[man], False, 'localhost'))
    #print (register(man, popu[man], False, '192.168.1.24'))

    man = 'Valérie'
    #print (register(man, popu[man], True,  'localhost'))
    #print (register(man, popu[man], False, 'localhost'))
    #print (register(man, popu[man], False, '192.168.1.24'))
    
    #print('http://pi.pelinquin.fr/bank?' + urllib.parse.quote('reg/totoé/tata⊔/1.4'))

    test, content = 'The Quick Brown\nFox Jumps Over\nThe Lazy Dog',[]
    page = [(10, 50, '50F1', 'F1 LaTeX\n'+ test),(10, 300, '50F2', 'F2 LaTeX\n'+test), (10, 550, '50F1', 'F3 LaTeX\n'+test)]
    content.append(page)
    #a = updf(595, 842)
    #open('toto.pdf', 'wb').write(a.gen(content))  


    sys.exit()

# End ⊔net!
