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

import re, os, sys, urllib.parse, hashlib, http.client, base64, dbm, binascii, datetime
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
__digest__ = base64.urlsafe_b64encode(hashlib.sha1(open(__file__, 'r', encoding='utf-8').read().encode('utf-8')).digest())[:5]

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
    mime, o, db, today = 'text/plain; charset=utf-8', 'Error:', '/u/bank.db', '%s' % datetime.datetime.now()
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
        elif reg(re.match(r'^\s*(reg|register)\s*(\(\s*"([^"]{3,})"\s*,\s*"([^"]{3,})"\s*,\s*"([^"]{3,})"\s*,\s*"([^"]{3,})"\s*\))\s*$', raw, re.U)):
            c, a = reg.v.group(1).lower(), eval(reg.v.group(2))
            assert (a[0] == reg.v.group(3) and a[1] == reg.v.group(4) and a[2] == reg.v.group(5) and a[3] == reg.v.group(6)) 
            #o = '4 ARGS %s %s %s' % (c, way, raw)
            pk, bal, ovr = b'PUB_' + bytes(a[0], 'utf8'), b'BAL_' + bytes(a[0], 'utf8'), b'OVR_' + bytes(a[0], 'utf8')
            if pk in d.keys():
                o += 'Public key already set!' 
            elif verify(RSA_E, b64toi(bytes(a[2], 'ascii')), ' '.join((today[:10], a[0], a[1])), bytes(a[3], 'ascii')):
                d[pk], d[bal], d[ovr], o = a[1], '0', '100', 'Public key id registration OK'
            else:
                o += 'Error in registration!'
        elif way == 'get':
            if raw.lower() in ('source', 'src', 'download'):
                o = open(__file__, 'r', encoding='utf-8').read()
            else:
                o, mime = frontpage(today), 'application/xhtml+xml; charset=utf-8'
    else:
        o += 'arg too long'
    d.close()
    start_response('200 OK', [('Content-type', mime)])
    return [o.encode('utf-8')] 

def frontpage(today):
    "_"
    o = '<?xml version="1.0" encoding="utf-8"?>\n' 
    o += '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink">\n'
    o += '<link rel="shortcut icon" type="image/png" href="favicon.png"/>\n'
    o += '<style>@import url(http://fonts.googleapis.com/css?family=Schoolbell);</style>\n'
    o += '<style type="text/css">svg{max-height:100;}text,path{stroke:none;fill:Dodgerblue;font-family:helvetica;}text.foot{font-size:14pt;fill:gray;text-anchor:middle;}text.alpha{font-family:Schoolbell;fill:#F87217;text-anchor:middle}text.note{fill:#CCC;font-size:9pt;text-anchor:end;}</style>\n'
    o += '<a xlink:href="http://cupfoundation.net"><path stroke-width="0" d="M10,10L10,10L10,70L70,70L70,10L60,10L60,60L20,60L20,10z"/></a>'
    d = dbm.open('/u/bank')
    nb, su, ck = 0, 0, 0
    for x in d.keys():
        if reg(re.match('BAL_(.*)$', x.decode('utf-8'))):
            nb += 1
            su += abs(float(d[x])/2)
            ck += float(d[x])
    o += '<text x="90" y="70" font-size="45" title="banking for intangible goods">Bank</text>\n'
    o += '<text class="alpha" font-size="16pt" x="92" y="25" title="still in security test!">Beta</text>\n'
    o += '<text class="alpha" font-size="64pt" text-anchor="middle" x="50%" y="40%"><tspan>No \"https\", no JavaScript,</tspan><tspan x="50%" dy="100">better security!</tspan></text>\n'
    o += '<text class="foot" x="100"  y="100" title="today">%s</text>\n' % today[:19]
    o += '<text class="foot" x="20%%" y="80%%" title="registered users">%04d users</text>\n' % nb
    o += '<text class="foot" x="40%%" y="80%%" title="">%06d transactions</text>\n' % int(d['NB_TR'])
    o += '<text class="foot" x="60%%" y="80%%" title="absolute value">Volume: %09.2f ⊔</text>\n' % su
    o += '<text class="foot" x="80%%" y="80%%" title="number of registered Intangible Goods">%04d IG</text>\n' % (0)
    o += '<a xlink:href="bank?source"><text class="note" text-anchor="start" x="160" y="98%" title="on GitHub (https://github.com/pelinquin/cup) hack it, share it!">Download the source code!</text></a>\n'
    o += '<a xlink:href="u?pi"><text class="note"      x="99%" y="40" title="at home!">Host</text></a>\n'            
    o += '<a xlink:href="bank?log"><text class="note"  x="99%" y="60" title="log file">Log</text></a>\n'
    o += '<a xlink:href="bank?help"><text class="note" x="99%" y="20" title="help">Help</text></a>\n'
    o += '<text class="note" x="50%%" y="98%%" title="you can use that server!">Status: <tspan fill="green">%s</tspan></text>\n' % ('OK' if (abs(ck) <= 0.00001) else 'error')
    o += '<text class="note" x="99%%" y="95%%">Digest: %s|%s</text>\n' % (d['__DIGEST__'].decode('utf-8'), __digest__.decode('utf-8'))
    o += '<text class="note" x="99%"  y="98%" title="or visit \'www.cupfoundation.net\'">Contact: laurent.fournier@cupfoundation.net</text>\n' 
    d.close()
    return o + '</svg>\n'

def register(owner, iduser='anonymous', post=False, host='localhost'):
    co, td = http.client.HTTPConnection(host), '%s' % datetime.datetime.now()
    ds = dbm.open('/u/sk')    
    ki, kb = [b64toi(x) for x in ds[owner].split()], [x for x in ds[owner].split()]
    ds.close()
    s = sign(ki[1], ki[2], ' '.join((td[:10], owner, iduser)))
    cmd = 'reg("%s","%s","%s","%s")' % (owner, iduser, kb[1].decode('ascii'), s.decode('ascii'))
    if post:
        co.request('POST', '/bank', urllib.parse.quote(cmd))
    else:
        co.request('GET', '/bank?' + urllib.parse.quote(cmd))
    #print('http://%s/bank?' % host + urllib.parse.quote(cmd))
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
        else:
            o = '<?xml version="1.0" encoding="utf-8"?>\n' 
            o += '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" xmlns:xlink="http://www.w3.org/1999/xlink">\n'
            o += '<link rel="shortcut icon" type="image/png" href="favicon.png"/>\n'
            #o += '<link xlink:href="http://fonts.googleapis.com/css?family=Schoolbell" rel="stylesheet" type="text/css"/>\n' 
            o += '<style>@import url(http://fonts.googleapis.com/css?family=Schoolbell);</style>\n'
            o += '<style type="text/css">text,path{stroke:none;fill:Dodgerblue;font-family:helvetica;}text.foot{fill:gray;}text.alpha{font-family:Schoolbell;fill:#F87217;}text.note{fill:#CCC;font-size:8pt;text-anchor:end;}text.w{fill:white;}rect{fill:#CCC;}</style>\n'
            o += '<a xlink:href="http://cupfoundation.net"><path stroke-width="0" d="M10,10L10,10L10,70L70,70L70,10L60,10L60,60L20,60L20,10z"/></a>'
            d = dbm.open('/u/bank',)
            nb, su, ck = 0, 0, 0
            for x in d.keys():
                if reg(re.match('BAL_(.*)$', x.decode('utf-8'))):
                    nb += 1
                    su += abs(float(d[x])/2)
                    ck += float(d[x])
            today = '%s' % datetime.datetime.now()
            o += '<text x="90" y="70" font-size="48" title="banking for intangible goods">Bank</text>\n'
            o += '<text class="alpha" font-size="14pt" x="72"  y="25" title="still in security test!">Beta</text>\n'
            o += '<text class="alpha" font-size="64pt" text-anchor="middle" x="50%" y="50%"><span>No \"https\", no JavaScript,</span><span>better security!</span></text>\n'

            o += '<text class="foot" x="20"  y="100">%s</text>\n' % today[:19]
            o += '<text class="foot" x="20"  y="360">%04d users</text>\n' % nb
            o += '<text class="foot" x="240" y="360">%05d transactions</text>\n' % int(d['NB_TR'])
            o += '<text class="foot" x="460" y="360">volume: %09.2f ⊔</text>\n' % su
            o += '<text class="foot" x="680" y="360" title="number of registered Intangible Goods">%04d IG</text>\n' % (0)
            o += '<a xlink:href="bank?source"><text class="note" text-anchor="start" x="220" y="98%" title="on Github (https://github.com/pelinquin/cup), hack it, share it!">Download the source code!</text></a>\n'
            o += '<a xlink:href="u?pi"><text class="note" x="99%" y="20" title="at home!">Host</text></a>\n'            
            o += '<a xlink:href="bank?log"><text class="note" x="99%" y="40">Log</text></a>\n'
            o += '<a xlink:href="bank?help"><text class="note" x="99%" y="60">Help</text></a>\n'

            o += '<text class="note" x="99%%" y="90%%">Status: %s</text>\n' % ('ok' if (abs(ck) <= 0.00001) else 'error')
            o += '<text class="note" x="99%%" y="94%%">Digest: %s|%s</text>\n' % (d['__DIGEST__'].decode('utf-8'), __digest__.decode('utf-8'))
            o += '<text class="note" x="99%" y="98%" title="or visit \'www.cupfoundation.net\'">Contact: laurent.fournier@cupfoundation.net</text>\n' 
            d.close()
            o += '</svg>\n'
            mime = 'application/xhtml+xml; charset=utf-8'
    start_response('200 OK', [('Content-type', mime)])
    return [o.encode('utf-8')] 

def itob64(n):
    "utility to transform int to base64"
    c = hex(n)[2:]
    if len(c)%2: c = '0'+c
    return re.sub(b'=*$', b'', base64.b64encode(bytes.fromhex(c)))

def b64toi(c):
    "transform base64 to int"
    if c == '': return 0
    return int.from_bytes(base64.b64decode(c + b'='*((4-(len(c)%4))%4)), 'big')

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

def register_old(owner, iduser=None, host='localhost'):
    "_"
    co = http.client.HTTPConnection(host)
    td = '%s' % datetime.datetime.now()
    ds = dbm.open('/u/sk')
    k = [b64toi(x) for x in ds[owner].split()]
    if iduser: 
        s = sign(k[1], k[2], '%s %s %s' % (td[:10], owner, iduser))
        co.request('POST', '/bank', 'PK("%s", "%s", "%s", %s)' % (urllib.parse.quote(owner), itob64(k[2]).decode('ascii'), iduser, s))
    else:
        s = sign(k[1], k[2], '%s %s' % (td[:10], owner))
        co.request('POST', '/bank', 'PK("%s", "%s", %s)' % (urllib.parse.quote(owner), itob64(k[2]).decode('ascii'), s))
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
    

if __name__ == '__main__':
    popu = {
        'Pelinquin': 'FR167071927202809', 
        'Alice':     'FR167070280099999', 
        'Valérie':   'FR164070287098888', 
        'Bob':       'FR261070280095555', 
        'Carl⊔':     'FR177070284098888', 
        'Daniel':    'FR287070280123333',
        }
    
    ds = dbm.open('/u/sk', 'c')
    for a in popu:
        if bytes(a,'utf-8') not in ds.keys():
            print ('generate key for', a)
            k = RSA.generate(4096, os.urandom)
            ds[a] = bytes(' '.join([itob64(x).decode('ascii') for x in (k.e, k.d, k.n)]), 'ascii')
    ds.close()

    host = 'localhost'
    #host = 'pi.pelinquin.fr'
    #for a in popu: print (register(a, popu[a], host))
    #print (register_ig('Alice', 'toto您tata', 0.56, 100000, host))
    #print (transaction('Alice',   'Bob', 1.65, host))
    #print (transaction('Valérie', 'Carl⊔', 4.65, host))
    #print (transaction('Bob',     'Valérie', 2.15, host))
    #print (transaction('Bob',     'Daniel', 4.65, host))
    #print (buy('Bob', 'toto您tata', host))
    #print (read_balance('Daniel', False, host))
    #print (transaction('Daniel', 'Valérie', 44.65, host))
    #print (read_balance('Valérie', False, host))

    co = http.client.HTTPConnection(host)
    ds = dbm.open('/u/sk')    
    ki = [b64toi(x) for x in ds['Alice'].split()]
    kb = [x for x in ds['Alice'].split()]
    ds.close()
    s = sign(ki[1], ki[2], 'blabla')

    cmd = 'TEST ( "hello Valérie", "%s")' % s.decode('ascii')
    co.request('POST', '/bank', urllib.parse.quote(cmd))
    print (co.getresponse().read().decode('utf-8'))
    co.request('GET', '/bank?' + urllib.parse.quote(cmd))
    print (co.getresponse().read().decode('utf-8'))


    print (register('Valérie', 'anonymous', False, 'localhost'))


    
    sys.exit()

# End ⊔net!
