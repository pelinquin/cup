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

# SHORT TODO LIST (just for me!)
# - Unicode inside PDF
# - Fix SVG position relative to right side
# - Add session key
# - Add wait alert when registering
# - Use/test several nodes
# - SRP authentication
# - Implement the 'share' request for co-authors
# - Add thunbnail covers in jpeg
# - Replace RSA with eliptic curves

__owner__ = 'Laurent Fournier'

import re, os, sys, math, urllib.parse, hashlib, http.client, base64, dbm, binascii, datetime, zlib, functools, subprocess
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES

__digest__ = base64.urlsafe_b64encode(hashlib.sha1(open(__file__, 'r', encoding='utf8').read().encode('utf8')).digest())[:5]
__user__ = os.path.basename(__file__)[:-3]
__email__ = 'laurent.fournier@cupfoundation.net'
__url__   = 'http://cupfoundation.net'
_XHTMLNS  = 'xmlns="http://www.w3.org/1999/xhtml"'
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
    ncok = []
    init_db(db)
    if environ['REQUEST_METHOD'].lower() == 'post':
        raw, way = environ['wsgi.input'].read(), 'post'        
    else:
        raw, way = urllib.parse.unquote(environ['QUERY_STRING']), 'get'
    fr = 'on' if 'HTTP_COOKIE' in environ and re.search(r'fr=on', environ['HTTP_COOKIE']) else None
    login = reg.v.group(1) if 'HTTP_COOKIE' in environ and reg(re.search(r'user=([^;]+)$', environ['HTTP_COOKIE'])) else ''
    d = dbm.open(db[:-3], 'c')
    if way == 'post':
        if environ['CONTENT_TYPE'] == 'application/x-www-form-urlencoded':
            if reg(re.match('lgn=([^&]{3,})&pw1=([^&]{4,})&pw2=([^&]+)&sid=(.+)$', urllib.parse.unquote(raw.decode('utf8')))):
                login, pw1, pw2, sid = reg.v.group(1), reg.v.group(2), reg.v.group(3), reg.v.group(4)
                if pw1==pw2 and pw1!=login and not login.encode('utf8') in d.keys():
                    ncok = [('set-cookie', 'user=%s' % login)]
                    #d['PW_'+login] = hashlib.sha1('%s/%s' % (login.encode('utf8'),pw1.encode('utf8'))).hexdigest()
                    d['PW_'+login] = hashlib.sha1(pw1.encode('utf8')).hexdigest()
                    k = RSA.generate(4096, os.urandom)
                    d['PK_' + login] = bytes(' '.join([itob64(x).decode('ascii') for x in (k.e, k.d, k.n)]), 'ascii')
                    ki, kb = [b64toi(x) for x in d['PK_' + login].split()], [x for x in d['PK_' + login].split()]
                    register(login, ki, kb, sid) 
                    o, mime = frontpage(today, environ['REMOTE_ADDR'], d, fr, login), 'application/xhtml+xml; charset=utf8'
                else:
                    o += 'login may already used or password too short or difference in the two passwords!'
            elif reg(re.match('lgn=([^&]{3,})&pw1=(.{4,})$', urllib.parse.unquote(raw.decode('utf8')))):
                login, pw = reg.v.group(1), reg.v.group(2)
                if b'PW_'+login.encode('utf8') in d.keys() and d['PW_'+login] == hashlib.sha1(pw.encode('utf8')).hexdigest().encode('utf8'):
                    ncok = [('set-cookie', 'user=%s' % login)]
                    o, mime = frontpage(today, environ['REMOTE_ADDR'], d, fr, login), 'application/xhtml+xml; charset=utf8'  
                else:
                    o += 'bad login or bad password!'                    
            elif re.match('act=logout$', urllib.parse.unquote(raw.decode('utf8'))):
                login = ''
                ncok = [('set-cookie', 'user=')]
                o, mime = frontpage(today, environ['REMOTE_ADDR'], d, fr, login), 'application/xhtml+xml; charset=utf8'
            elif reg(re.match('ig=([^&]+)', urllib.parse.unquote(raw.decode('utf8')))):
                ki = [b64toi(x) for x in d['PK_' + login].split()]
                buy(login, reg.v.group(1), ki) 
                o, mime = frontpage(today, environ['REMOTE_ADDR'], d, fr, login), 'application/xhtml+xml; charset=utf8'
            elif reg(re.match('get=([^&]+)', urllib.parse.unquote(raw.decode('utf8')))):
                ki = [b64toi(x) for x in d['PK_' + login].split()]
                ig = reg.v.group(1)
                #ncl = isclient(__owner__, login, ig)
                #if ncl[:5] != b'Error':
                fpdf = '/cup/%s/%s.pdf' % (__user__, ig)
                content = open(fpdf.encode('utf8'), 'rb').read()
                o, mime, fname = content, 'application/pdf', ig + '.pdf'                 
            elif reg(re.match('val=([^&]+)&act=invoice$', urllib.parse.unquote(raw.decode('utf8')))):
                ki = [b64toi(x) for x in d['PK_' + login].split()]
                o, mime, fname = conversion(login, float(reg.v.group(1)), ki), 'application/pdf', 'invoice.pdf'                 
            elif re.match('act=statement$', urllib.parse.unquote(raw.decode('utf8'))):
                ki = [b64toi(x) for x in d['PK_' + login].split()]
                o, mime, fname = statement(login, ki), 'application/pdf', 'statement.pdf'
            else:
                o += 'something wrong in the input text! %s' % raw
        else:
            l, le = raw[:300].split(b'\r\n'), raw[-550:].split(b'\r\n')
            f, fn = len(l[0]) + 6, reg.v.group(1) if reg(re.search('filename="([^"]+)"', l[1].decode('utf8'), re.U)) else 'error'
            t = f + len(l[1]) + len(l[2]) + 2
            tail = 2+len(b'\r\n'.join(le[-14:]))
            open(bytes ('/cup/%s/' % __user__, 'utf8') + fn.encode('utf8'), 'wb').write(raw[t:-tail])
            xi, pi, p1 = int(le[-3]), float(le[-7]), float(le[-11])
            ki = [b64toi(x) for x in d['PK_'+login].split()]
            igreg(login, fn, p1, pi, ki)
            o, mime = frontpage(today, environ['REMOTE_ADDR'], d, fr, login), 'application/xhtml+xml; charset=utf8'
    else:
        log(raw, environ['REMOTE_ADDR'])
        values = [d[k].decode('utf8') for k in d.keys()]
        if raw[:9].lower() == 'statement':
            ncl = statement(__owner__)
            o, mime, fname = ncl, 'application/pdf', 'statement' 
        else:
            o, mime = frontpage(today, environ['REMOTE_ADDR'], d, fr, login), 'application/xhtml+xml; charset=utf8'
            #o = '%s' % environ['HTTP_COOKIE']
    d.close()
    start_response('200 OK', [('Content-type', mime), ('Content-Disposition', 'filename={}'.format(fname))] + ncok)
    return [o if mime == 'application/pdf' else o.encode('utf8')] 

def favicon():
    "_"
    code = '<svg %s n="%s"><path stroke-width="4" fill="none" stroke="Dodgerblue" d="M3,1L3,14L13,14L13,1"/></svg>' % (_SVGNS, datetime.datetime.now())
    tmp = base64.b64encode(code.encode('utf8'))
    return '<link xmlns="http://www.w3.org/1999/xhtml" rel="shortcut icon" type="image/svg+xml" href="data:image/svg+xml;base64,%s"/>\n' % tmp.decode('utf8')

def frontpage(today, ip, d, fr, login=''):
    "not in html!"
    o = '<?xml version="1.0" encoding="utf8"?>\n' 
    o += '<svg %s %s>\n' % (_SVGNS, _XLINKNS) + favicon()
    o += '<style type="text/css">@import url(http://fonts.googleapis.com/css?family=Schoolbell);svg{max-height:100;}text,path{stroke:none;fill:Dodgerblue;font-family:helvetica;}a,text.a{fill:Dodgerblue;}text.foot{font-size:14pt;fill:gray;text-anchor:start;}text.foot1{font-size:12pt;fill:gray;}text.alpha{font-family:Schoolbell;fill:#F87217;text-anchor:start;}text.note{fill:#CCC;font-size:9pt;text-anchor:end;}input,button{padding:2px;margin:1px;border:1px solid #D1D1D2;border-radius:3px;font-size:12px;}input[type="text"],input[type="password"]{color:#999;width:66px;}input[type="submit"],button{color:#fff}input[type="file"]{color:#999;}input[type="submit"].blue{background-color:Dodgerblue;font-size:14pt;border-radius:8px}</style>\n'
    o += '<a xlink:href="%s"><path stroke-width="0" d="M10,10L10,10L10,70L70,70L70,10L60,10L60,60L20,60L20,10z"/></a>\n' % __url__
    o += '<text x="80" y="70" font-size="45">%s</text>\n' % __user__
    if login:
        o += '<text class="alpha" font-size="50pt" x="510" y="70">%s</text>\n' % login
        o += '<a xlink:href="/bank"><text class="a" x="120" y="30">Bank</text></a>\n'

        o += '<foreignObject x="92%%" y="10" width="100" height="30"><div %s><form method="post">\n' % _XHTMLNS
        o += '<input class="right" type="submit" name="act" value="logout"/>\n'        
        o += '</form></div></foreignObject>\n'
        
        ki = [b64toi(x) for x in d['PK_' + login].split()]
        [bal, ovd] = balance(login, ki).split() 
        o += '<text class="note" x="240" y="98%%">Balance: %s ⊔ Overdraft: %s ⊔</text>\n' % (bal, ovd)

        o += '<foreignObject x="92%%" y="40" width="100" height="30"><div %s><form method="post">\n' % _XHTMLNS
        o += '<input type="submit" name="act" value="statement"/>\n'        
        o += '</form></div></foreignObject>\n'

        o += '<foreignObject x="92%%" y="90" width="100" height="70"><div %s><form method="post">\n' % _XHTMLNS
        o += '<input type="text" name="val" placeholder="amount" required="yes" title="in your overdraft limit!"/>⊔ <br/>'
        o += '<input type="submit" name="act" value="invoice"/>\n'        
        o += '</form></div></foreignObject>\n'

        o += '<foreignObject x="200" y="10" width="300" height="80"><div %s><form enctype="multipart/form-data" method="post">\n' % _XHTMLNS
        o += '<input type="file" name="upfile" accept="pdf/*"/><br/>'
        o += '<input type="text" name="p1" placeholder="p1" required="yes" title=">0"/>⊔ '
        o += '<input type="text" name="ic" placeholder="income" required="yes" title=">0 and >price"/>⊔ '
        o += '<input type="text" name="xi" placeholder="xi" required="yes" title="[0-100]"/>%<br/>'
        o += '<input type="submit" value="create IG"/>\n'
        o += '</form></div></foreignObject>\n'
    else:
        o += '<foreignObject x="200" y="10" width="400" height="30"><div %s><form method="post">\n' % _XHTMLNS
        o += '<input type="text"     name="lgn" placeholder="name" required="yes"/>'
        o += '<input type="password" name="pw1" placeholder="password"  required="yes"/>'
        o += '<input type="password" name="pw2" placeholder="pw again!" required="yes"/>'
        o += '<input type="text"     name="sid" placeholder="social id" required="yes" title="Your Social Security Number to get 100⊔ overdraft"/>'
        o += '<input type="submit"   value="register"/>\n'
        o += '</form></div></foreignObject>\n'
        o += '<foreignObject x="200" y="36" width="400" height="30"><div %s><form method="post">\n' % _XHTMLNS
        o += '<input type="text"     name="lgn" placeholder="name" required="yes"/>'
        o += '<input type="password" name="pw1" placeholder="password" required="yes"/>'
        o += '<input type="submit"   value="login"/>\n'
        o += '</form></div></foreignObject>\n'

    if ip == '127.0.0.1': 
        o += '<text class="note" x="160" y="90"  title="my ip adress">local server</text>\n'
    i, dte, pl = 0, 32 ,[]
    if login:
        ki = [b64toi(x) for x in d['PK_'+login].split()]
        pl = playlist(login, ki).split('/')
    for x in format_cmd(False, 'list', False).split('\n'):
        tab = x.split('/')
        if os.path.isfile (bytes('/cup/%s/%s' % (__user__, tab[0]), 'utf8')):
            i +=1
            p1, pf, n = float(tab[2]), float(tab[3]), int(tab[5])
            k, xi = math.log(pf-p1) - math.log(pf-2*p1), .25          
            price = (pf - (pf-p1)*math.exp(-xi*n*k))/(n+1)               
            o += '<text class="note" x="480" y="%s">%s</text>\n' % (110+dte*i, tab[1])
            o += '<text class="note" x="540" y="%s" title="author">%s</text>\n' % (110+dte*i, tab[4])
            o += '<text class="note" x="102" y="%s" title="number of buyers">%04d</text>\n' % (110+dte*i, int(tab[5]))
            o += '<foreignObject x="10" y="%s" width="80" height="35"><div %s><form method="post">\n' % (90+dte*i, _XHTMLNS)
            o += '<input type="hidden" name="ig" value="%s"/>\n' % tab[0]        
            o += '<input type="submit" name="buy" value="%7.2f⊔" title="max income: %s⊔"/>\n' % (price, tab[3])        
            o += '</form></div></foreignObject>\n'
            if tab[0] in pl:
                o += '<foreignObject x="120" y="%s" width="200" height="35"><div %s><form method="post">\n' % (90+dte*i, _XHTMLNS)
                o += '<input class="blue" type="submit" name="get" value="%s"/>\n' % (tab[0][:-4])        
                o += '</form></div></foreignObject>\n'
                o += '<foreignObject x="560" y="%s" width="60" height="35"><div %s><form method="post">\n' % (90+dte*i, _XHTMLNS)
                o += '<input type="submit" name="rcp" value="receipt"/>\n'         
                o += '</form></div></foreignObject>\n'
            else:
                o += '<text class="foot" x="120" y="%s">%s</text>\n' % (110+dte*i, tab[0][:-4])                
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

def register(owner, ki, kb, iduser='anonymous', host='localhost', post=False):
    "_"
    td = '%s' % datetime.datetime.now()
    s = sign(ki[1], ki[2], '/'.join((td[:10], owner, iduser)))
    assert (verify(RSA_E, ki[2], '/'.join((td[:10], owner, iduser)), s))
    cmd = '/'.join(('reg', owner, iduser, kb[2].decode('ascii'), s.decode('ascii')))
    return format_cmd(post, cmd)

def igreg(owner, idig, p1, pf, ki, host='localhost', post=False):
    "_"
    td = '%s' % datetime.datetime.now()
    s = sign(ki[1], ki[2], '/'.join((td[:10], owner, idig, '%s' % p1, '%s' % pf)))
    cmd = '/'.join(('ig', owner, idig, '%s' % p1, '%s' % pf, s.decode('ascii')))
    era = format_cmd(post, cmd, True)
    if era[:5] != b'Error':
        sk = decrypt(ki[1], ki[2], era)
        d = dbm.open('/cup/%s/keys' % __user__, 'c')
        d[sk] = idig
        d.close()
    return era

def buy(byr, ig, ki, host='localhost', post=False):
    "_"
    td = '%s' % datetime.datetime.now()
    s = sign(ki[1], ki[2], '/'.join((byr, ig, td)))
    cmd = '/'.join(('buy', byr, ig, td, s.decode('ascii')))
    era = format_cmd(post, cmd, True)
    if era[:5] != b'Error':
        sk = decrypt(ki[1], ki[2], era)
        return 'http://%s/%s?download/' % (host, __user__) + urllib.parse.quote(byr) + '/' + sk.decode('ascii')
    else:
        return era

def playlist(own, ki, host='localhost', post=False):
    "_"
    td = '%s' % datetime.datetime.now()
    s = sign(ki[1], ki[2], '/'.join((own, td[:10])))
    cmd = '/'.join(('playlist', own, s.decode('ascii')))
    return format_cmd(post, cmd, False, host)

def statement(own, ki, host='localhost', post=False):
    "_"
    td = '%s' % datetime.datetime.now()
    s = sign(ki[1], ki[2], '/'.join(('st', own, td[:10])))
    cmd = '/'.join(('statement', own, s.decode('ascii')))
    return format_cmd(post, cmd, True)

def conversion(own, val, ki, host='localhost', post=False):
    "_"
    td = '%s' % datetime.datetime.now()
    s = sign(ki[1], ki[2], '/'.join(('ex', own, '%f' % val, td[:10])))
    cmd = '/'.join(('conversion', own, '%f' % val, s.decode('ascii')))
    return format_cmd(post, cmd, True)

def balance(own, ki, host='localhost', post=False):
    "_"
    td = '%s' % datetime.datetime.now()
    s = sign(ki[1], ki[2], '/'.join((own, td[:10])))
    cmd = '/'.join(('balance', own, s.decode('ascii')))
    return format_cmd(post, cmd, False)

if __name__ == '__main__':
    print (__user__)

    d = dbm.open('/cup/node/keys')
    login = 'laurent'
    ki = [b64toi(x) for x in d['PK_' + login].split()]
    d.close()
    #content = statement(login, ki)
    content = conversion(login, 2.5, ki)
    open(bytes ('toto.pdf', 'utf8'), 'wb').write(content)
    
    sys.exit()
# End ⊔net!
