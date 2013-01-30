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
MAX_ARG_SIZE = 850

def reg(value):
    " function attribute is a way to access matching group in one line test "
    reg.v = value
    return value

def application(environ, start_response):
    "wsgi server app"
    if not os.path.isfile('/u/bank.db'):
        d = dbm.open('/u/bank', 'c')
        d['__DIGEST__'], d['NB_TR'] = __digest__, '0'
        d.close()
    if environ['REQUEST_METHOD'].lower() == 'post':
        raw, o = urllib.parse.unquote(environ['wsgi.input'].read().decode('utf-8')), 'error!'
        o = 'error! %s' % raw[:15]
        d = dbm.open('/u/bank', 'c')
        if reg(re.match(r'^TR(\(\s*"([^"]{3,30})"\s*,\s*"([^"]{3,30})".*)$', raw, re.U)): 
            t, byr, slr = eval(reg.v.group(1)), b'BAL_' + bytes(reg.v.group(2), 'utf-8') , b'BAL_' + bytes(reg.v.group(3), 'utf-8')
            if (len(t) == 5) and (type(t[2]).__name__ in  ('float', 'int')) and (type(t[0]).__name__ == 'str') and (type(t[1]).__name__ == 'str'):
                pk = bytes('PUB_%s' % t[0], 'utf-8')
                if pk in d.keys() and len(raw) < MAX_ARG_SIZE:
                    if t[3] not in d.keys():
                        if verify(RSA_E, b64toi(d[pk]), '%s|%s|%s|%s' % tuple(t[0:4]), t[4]):
                            d[byr] = '%f' % (float(d[byr]) - t[2] if byr in d.keys() else -t[2])
                            d[slr] = '%f' % (float(d[slr]) + t[2] if slr in d.keys() else  t[2])
                            d['NB_TR'], d[t[3]], o = '%d' % (int(d['NB_TR'])+1), '_', 'Transaction OK'
                        else:
                            o = 'Wrong buyer signature!'
                    else:
                        o = 'Duplicate transaction!'
                else:
                    o = 'Unknown public key!'
        elif reg(re.match(r'^PK(\(\s*"([^\"]{3,30})".*)$', raw, re.U)): 
            t, name = eval(reg.v.group(1)), b'PUB_' + bytes(reg.v.group(2), 'utf8')
            if name in d.keys():
                o = 'PUBLIC KEY ALREADY SET!' 
            elif (len(t) == 2) and (type(t[0]).__name__ == 'str') and (type(t[1]).__name__ == 'str') and len(raw) < MAX_ARG_SIZE:
                d[name], o = t[1], 'PUBKEY OK'
        elif reg(re.match(r'^BAL(\(\s*"([^\"]{3,30})".*)$', raw, re.U)): 
            t, name = eval(reg.v.group(1)), b'BAL_' + bytes(reg.v.group(2), 'utf8')
            if name in d.keys():
                today = '%s' % datetime.datetime.now()
                pk = bytes('PUB_%s' % t[0], 'utf-8')
                if verify(RSA_E, b64toi(d[pk]), today[:10], t[1]):
                    o = '%s: %s⊔' % (today, d[name].decode('utf-8'))
                else:
                    o = 'bad signature!'
        elif reg(re.match(r'^UPDATE$', raw)):
            o = 'provision update from Github'
        elif reg(re.match(r'^TEST', raw)): # unicode
            o = 'test! %s' % raw
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
                    su += abs(float(d[x]))
                    ck += float(d[x])
            o =  'Number of login: %d\n' % nb
            o += 'Total transactions: %f\n' % (su/2)
            o += 'Check integrity (should be zero): %f\n' % ck
            o += 'Number of transactions: %d\n' % int(d['NB_TR'])
            o += 'DIGESTS now, database creation :%s %s\n' % (d['__DIGEST__'], __digest__)
            d.close()
        elif arg.lower() in ('log', 'transaction'):
            d, o = dbm.open('/u/bank',), ''
            for x in d.keys():
                if reg(re.match('(\d{4}.*)$', x.decode('utf-8'))):
                    o += '%s\n' % reg.v.group(1)
            d.close()
        else:
            o = 'Welcome to ⊔net!\n\nHTTP POST request:\n'
            o += '\tPK(agent, public_key)\n'
            o += '\tTR(buyer, seller, price, current_date, buyer_signature) with signed message = \'seller|price|\' returns status (OK,KO)\n'
            o += '\tBAL(owner, owner_signature) with signed message = \'date_of_the_day\' returns ballance\n'
            o += 'HTTP GET request:\n\tstat\n\tsource\n\tlog\n'
    start_response('200 OK', [('Content-type', 'text/plain; charset=utf-8')])
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

if __name__ == '__main__':
    popu = ('Alice', 'Valérie', 'Bob', 'Carl⊔', 'Daniel', 'Elise')
    co = http.client.HTTPConnection('localhost')
    ds = dbm.open('/u/sk', 'c')
    for a in popu:
        if bytes(a,'utf-8') not in ds.keys():
            print ('generate key for', a)
            k = RSA.generate(4096, os.urandom)
            ds[a] = bytes(' '.join([itob64(x).decode('ascii') for x in (k.e, k.d, k.n)]), 'ascii')
    ds.close()

    ds = dbm.open('/u/sk')
    for a in popu:
        k = [b64toi(x) for x in ds[a].split()]
        co.request('POST', '/bank', 'PK("%s", "%s")' % (urllib.parse.quote(a), itob64(k[2]).decode('ascii')))
        print(co.getresponse().read().decode('utf-8'))
    ds.close()

    ds = dbm.open('/u/sk')    

    byr, slr, prc, td = 'Alice', 'Bob', 1.65, bytes('%s' % datetime.datetime.now(), 'ascii')
    k = [b64toi(x) for x in ds[byr].split()]
    s = sign(k[1], k[2], '%s|%s|%s|%s' %(byr, slr, prc, td))
    co.request('POST', '/bank', 'TR("%s", "%s", %s, %s, %s)' % (urllib.parse.quote(byr), urllib.parse.quote(slr), prc, td, s))
    print(co.getresponse().read().decode('utf-8'))

    byr, slr, prc, td = 'Valérie', 'Carl⊔', 1.65, bytes('%s' % datetime.datetime.now(), 'ascii')
    k = [b64toi(x) for x in ds[byr].split()]
    s = sign(k[1], k[2], '%s|%s|%s|%s' %(byr, slr, prc, td))
    co.request('POST', '/bank', 'TR("%s", "%s", %s, %s, %s)' % (urllib.parse.quote(byr), urllib.parse.quote(slr), prc, td, s))
    print(co.getresponse().read().decode('utf-8'))

    byr, slr, prc, td = 'Bob', 'Daniel', 1.65, bytes('%s' % datetime.datetime.now(), 'ascii')
    k = [b64toi(x) for x in ds[byr].split()]
    s = sign(k[1], k[2], '%s|%s|%s|%s' %(byr, slr, prc, td))
    co.request('POST', '/bank', 'TR("%s", "%s", %s, %s, %s)' % (urllib.parse.quote(byr), urllib.parse.quote(slr), prc, td, s))
    print(co.getresponse().read().decode('utf-8'))
    s = sign(k[1], k[2], '%s|%s|%s|%s' %(byr, slr, prc, td))
    co.request('POST', '/bank', 'TR("%s", "%s", %s, %s, %s)' % (urllib.parse.quote(byr), urllib.parse.quote(slr), prc, td, s))
    print(co.getresponse().read().decode('utf-8'))

    owner, td = 'Valérie', '%s' % datetime.datetime.now()
    k = [b64toi(x) for x in ds[owner].split()]
    s = sign(k[1], k[2], td[:10])
    co.request('POST', '/bank', 'BAL("%s", %s)' % (urllib.parse.quote(owner), s))
    print(co.getresponse().read().decode('utf-8'))


    ds.close()

    #co.request('GET', '/bank?stat')
    #print(co.getresponse().read())
    
    sys.exit()

# End ⊔net!
