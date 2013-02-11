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

__owner__ = 'Laurent Fournier'

import re, os, sys, urllib.parse, hashlib, http.client, base64, dbm, binascii, datetime, zlib, functools, subprocess
from Crypto.Cipher import AES

__digest__ = base64.urlsafe_b64encode(hashlib.sha1(open(__file__, 'r', encoding='utf8').read().encode('utf8')).digest())[:5]
__user__ = os.path.basename(__file__)[:-3]

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
        d.close()
        os.chmod(db, 511)

def log(s, ip=''):
    "Append to head log file"
    logf, now = '/cup/%s/log' % __user__, '%s' % datetime.datetime.now()
    if not os.path.isfile(logf): open(logf, 'w', encoding='utf8').write('%s|%s Log file Creation\n' % (now[:-7], ip) )     
    cont = open(logf, 'r', encoding='utf8').read()
    open(logf, 'w', encoding='utf8').write('%s|%s|%s\n%s' % (now[:-7], ip, s, cont))

def application(environ, start_response):
    "wsgi server app"
    mime, o, db, today, fname = 'text/plain; charset=utf8', 'Error:', '/cup/%s/keys.db' % __user__, '%s' % datetime.datetime.now(), 'default.txt'
    init_db(db)
    if environ['REQUEST_METHOD'].lower() == 'post':
        raw, way = urllib.parse.unquote(environ['wsgi.input'].read().decode('utf8')), 'post'
    else:
        raw, way = urllib.parse.unquote(environ['QUERY_STRING']), 'get'
    log(raw, environ['REMOTE_ADDR'])
    d = dbm.open(db[:-3], 'c')
    values = [d[k].decode('utf8') for k in d.keys()]
    if len(raw) < MAX_ARG_SIZE:
        if raw[:8].lower() == 'download':
            arg = raw.split('/')
            if len(arg)>2:
                byr = arg[1]
                if bytes(arg[2], 'utf8') in d.keys():
                    ig = d[bytes(arg[2], 'utf8')].decode('utf8')
                    ncl = isclient(__owner__, byr, ig, 'localhost')
                    igname = '%s.pdf' % re.sub('[\s/]','_', ig)
                    if ncl[:5] != b'Error':
                        fpdf = '/cup/%s/' % __user__ + igname
                        content = open(fpdf.encode('utf8'), 'rb').read()
                        td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')
                        ki = [b64toi(x) for x in ds[byr].split()]
                        ds.close()
                        # add here watermark
                        s = sign(ki[1], ki[2], '/'.join((byr, today[:10], '%s' % content)))
                        if len(arg) == 4:
                            sig = re.sub('(.{80})', '\\1\n', s.decode('ascii'), re.DOTALL)
                            url = 'http://localhost/%s?%s' % (__user__, urllib.parse.quote(raw))
                            #if arg[3] == 'plain':
                            #o = 'Intangible Good:\t\'%s\'\ncreated by:\t\t\'%s\'\npurchased by:\t\t\'%s\'\ndate:\t\t\t%s\nurl: %s\n\ndigital signature of dedicated IG (RSA 4096 bits):\n\n%s' % (ig, __owner__, byr, today[:10], url[:-6], sig)
                            o, mime, fname = ncl, 'application/pdf', 'receipt_' + igname           
                            #o, mime, fname = receipt(td[:19], ig, __owner__, byr, url[:-4], ncl, sig), 'application/pdf', 'receipt_' + igname
                        else:
                            o, mime, fname = content, 'application/pdf', igname                 
        elif raw[:9].lower() == 'statement':
            ncl = statement(__owner__)
            o, mime, fname = ncl, 'application/pdf', 'statement' 
        else:
            o, mime = frontpage(today, environ['REMOTE_ADDR'], d), 'application/xhtml+xml; charset=utf8'
    else:
        o += 'arg too long'
    d.close()
    start_response('200 OK', [('Content-type', mime), ('Content-Disposition', 'filename={}'.format(fname))])
    return [o if mime == 'application/pdf' else o.encode('utf8')] 

def favicon():
    "_"
    code = '<svg %s n="%s"><path stroke-width="4" fill="none" stroke="Dodgerblue" d="M3,1L3,14L13,14L13,1"/></svg>' % (_SVGNS, datetime.datetime.now())
    tmp = base64.b64encode(code.encode('utf8'))
    return '<link xmlns="http://www.w3.org/1999/xhtml" rel="shortcut icon" type="image/svg+xml" href="data:image/svg+xml;base64,%s"/>\n' % tmp.decode('utf8')

def frontpage(today, ip, d):
    "not in html!"
    o = '<?xml version="1.0" encoding="utf8"?>\n' 
    o += '<svg %s %s>\n' % (_SVGNS, _XLINKNS) + favicon()
    o += '<style type="text/css">@import url(http://fonts.googleapis.com/css?family=Schoolbell);svg{max-height:100;}text,path{stroke:none;fill:Dodgerblue;font-family:helvetica;}a{fill:Dodgerblue;}text.foot{font-size:18pt;fill:gray;text-anchor:start;}text.foot1{font-size:12pt;fill:gray;}text.alpha{font-family:Schoolbell;fill:#F87217;text-anchor:middle}text.note{fill:#CCC;font-size:9pt;text-anchor:end;}</style>\n'
    o += '<a xlink:href="%s"><path stroke-width="0" d="M10,10L10,10L10,70L70,70L70,10L60,10L60,60L20,60L20,10z"/></a>\n' % __url__
    o += '<text x="80" y="70" font-size="45">%s</text>\n' % __user__
    o += '<text class="alpha" font-size="50pt" x="50%%" y="70">IGs by %s</text>\n' % __owner__
    if ip == '127.0.0.1': 
        o += '<text class="note" x="160" y="90"  title="my ip adress">local server</text>\n'
    i, dirl = 0, [f.decode('utf8')[:-4] for f in os.listdir(bytes('/cup/%s' % __user__, 'utf8'))]
    for x in d.keys():
        i += 1
        o += '<text class="foot" x="60" y="%s">%s</text>\n' % (110 + 30*i, d[x].decode('utf8'))
        if ip == '127.0.0.1' and d[x].decode('utf8') in dirl:
            url = 'http://cup/%s?download/%s/%s' % (__user__, urllib.parse.quote(__owner__), x.decode('ascii'))            
            o += '<text class="foot" x="460" y="%s"><a xlink:href="%s">pdf</a></text>\n' % (110 + 30*i, url)
            o += '<text class="foot1" x="600" y="%s">receipt: <a xlink:href="%s/plain">plain</a>, <a xlink:href="%s/pdf">pdf</a></text>\n' % (110 + 30*i, url, url)
    o += '<text class="note" x="99%%" y="98%%" title="or visit \'%s\'">Contact: %s</text>\n' % (__url__, __email__) 
    return o + '</svg>'

def isclient(slr, byr, ig, host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')
    ki = [b64toi(x) for x in ds[slr].split()]
    ds.close()
    s = sign(ki[1], ki[2], '/'.join((slr, byr, ig, td[:10])))
    cmd = '/'.join(('isclient', slr, byr, ig, s.decode('ascii')))
    return format_cmd(post, cmd, True, host)

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
    aes = AES.new(skey, AES.MODE_ECB)
    c, r = itob64(pow(iskey, e, n)), len(msg)
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

def format_cmd(post, cmd, binary=False, host='localhost'):
    co = http.client.HTTPConnection(host)    
    if post:
        co.request('POST', '/bank', urllib.parse.quote(cmd))
    else:
        co.request('GET', '/bank?' + urllib.parse.quote(cmd))
    if binary:
        return co.getresponse().read()    
    else:
        return co.getresponse().read().decode('utf8')    

def register(owner, iduser='anonymous', host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')    
    ki, kb = [b64toi(x) for x in ds[owner].split()], [x for x in ds[owner].split()]
    ds.close()
    s = sign(ki[1], ki[2], ' '.join((td[:10], owner, iduser)))
    assert (verify(RSA_E, ki[2], ' '.join((td[:10], owner, iduser)), s))
    cmd = '/'.join(('reg', owner, iduser, kb[2].decode('ascii'), s.decode('ascii')))
    return format_cmd(post, cmd)

def igreg(owner, idig, p1, pf, host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')
    ki = [b64toi(x) for x in ds[owner].split()]
    ds.close()
    s = sign(ki[1], ki[2], ' '.join((td[:10], owner, idig, '%s' % p1, '%s' % pf)))
    cmd = '/'.join(('ig', owner, idig, '%s' % p1, '%s' % pf, s.decode('ascii')))
    era = format_cmd(post, cmd, True)
    if era[:5] != b'Error':
        sk = decrypt(ki[1], ki[2], era)
        d = dbm.open('/cup/%s/keys' % __user__, 'c')
        d[sk] = idig
        d.close()
    return era

def buy(byr, ig, host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')
    ki = [b64toi(x) for x in ds[byr].split()]
    ds.close()
    s = sign(ki[1], ki[2], ' '.join((byr, ig, td)))
    cmd = '/'.join(('buy', byr, ig, td, s.decode('ascii')))
    era = format_cmd(post, cmd, True)
    if era[:5] != b'Error':
        sk = decrypt(ki[1], ki[2], era)
        print ('http://%s/%s?download/' % (host, __user__) + urllib.parse.quote(byr) + '/' + sk.decode('ascii'))
    else:
        print (era)

def statement(own, host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')
    ki = [b64toi(x) for x in ds[own].split()]
    ds.close()
    s = sign(ki[1], ki[2], ' '.join((own, td[:10])))
    cmd = '/'.join(('statement', own, s.decode('ascii')))
    return format_cmd(post, cmd, True)

if __name__ == '__main__':
    print (__user__)

    host = 'localhost'
    ig = 'économie'
    b1, b2 = 'Laurent Fournier', 'Valérie Fournier'
    slr = 'Carl⊔'
    ig1, ig2 = 'my_created_ig_1','my_created_ig_2'
    print(register(slr, 'anonymous', host))
    print(register(b1, 'fr167071927202809', host))
    print(register(b2, 'fr274044732307944', host))
    print(igreg(slr, ig1, 10, 100, host))
    print(igreg(b1,  ig2, 10, 100, host))    
    buy(b2, ig1, host)
    buy(b1, ig1, host)
    buy(b2, ig1, host)
    buy(b2, ig2, host)

    sys.exit()
# End ⊔net!
