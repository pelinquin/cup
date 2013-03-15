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

import re, os, sys, urllib.parse, hashlib, http.client, base64, dbm, binascii, datetime, zlib, functools, subprocess, math, time
from Crypto.Cipher import AES

__digest__ = base64.urlsafe_b64encode(hashlib.sha1(open(__file__, 'r', encoding='utf8').read().encode('utf8')).digest())[:5]

__embedded_fonts__ = ('cmr10', 'cmr17')
__fonts__ = ('Helvetica', 'Times-Roman', 'Courier', 'Times-Bold', 'Helvetica-Bold', 'Courier-Bold', 'Times-Italic', 'Helvetica-Oblique', 
             'Courier-Oblique', 'Times-BoldItalic', 'Helvetica-BoldOblique', 'Courier-BoldOblique', 'Symbol') + __embedded_fonts__

__email__ = 'laurent.fournier@cupfoundation.net'
__url__   = 'http://cupfoundation.net'
_XHTMLNS  = 'xmlns="http://www.w3.org/1999/xhtml"'
_SVGNS    = 'xmlns="http://www.w3.org/2000/svg"'
_XLINKNS  = 'xmlns:xlink="http://www.w3.org/1999/xlink"'
RSA_E = 65537
MAX_ARG_SIZE = 2000
PRECISION = .0001

__currencies__ = {
    'USD': None, 'EUR': None, 'JPY': None, 'CAD': None, 'GBP': None,
    'CHF': None, 'RUB': None, 'AUD': None, 'SEK': None, 'DKK': None,
    'HKD': None, 'PLN': None, 'CNY': None, 'SGD': None, 'THB': None,
    'NZD': None, 'NOK': None,
}

def init_r(r1, u, a):
    "_"
    return { 'IGC'+x:a*r1[u+x] for x in __currencies__.keys()}

def expand_r (r):
    "_"
    u = 'USD'
    for c in __currencies__.keys():
        r[c+c] = 1
        if c != u:
            r[u+c] = 1/r[c+u]
    for c1 in __currencies__.keys():
         for c2 in __currencies__.keys():
             if c1 != c2 and (c1 != u) and (c2 != u): 
                 r[c1+c2] = r[c1+u] * r[u+c2]

def func_r(r, t, r2, i):
    "_"
    u = 'EUR' # works with any currency!
    for x in __currencies__.keys(): t['IGC'+x] = (r['IGC'+u]+i)*r2[u+x]
    return abs(sum(r['IGC'+w] - t['IGC'+w] for w in __currencies__.keys())) 

def compute_r(r2, r):
    "_"
    t, i, j = {}, -10.0, 10.0
    while i!=j:
        if func_r(r, t, r2, i) > func_r(r, t, r2, j): i = .5*(i+j) 
        else: j = .5*(i+j)
    return t 

def get_rates():
    "_"
    now, db, v0 = '%s' % datetime.datetime.now(), '/cup/rates', 2
    if not os.path.isfile(db + '.db'):
        dr = dbm.open(db, 'c')
        dr[now[:10]] = b'Init'
        dr.close()
    dr = dbm.open(db, 'w')
    if bytes(now[:10], 'ascii') not in dr.keys():
        co, h = http.client.HTTPConnection('currencies.apps.grandtrunk.net'), {}
        for c in __currencies__:
            if c != 'USD':
                co.request('GET', '/getlatest/%s/USD' %c)
                h[c+'USD'] = float(co.getresponse().read())
        tab = sorted(dr.keys())
        if len(tab)>1:
            r1, r2 = eval(dr[tab[-2]]), eval(dr[tab[-1]])
            expand_r(r1)
            expand_r(r2)
            r = init_r(r1, 'USD', r1['IGCUSD'] if 'IGCUSD' in r1 else v0)
            t = compute_r(r2, r)
            h['IGCUSD'] = t['IGCUSD']
        else:
            h['IGCUSD'] = v0
        dr[now[:10]] = '%s' % h
    r = eval(dr[bytes(now[:10],'ascii')]) # to optimize!
    expand_r(r)
    dr.close()
    return {x:r['IGCUSD']*r['USD'+x] for x in __currencies__}

def get_my_rate(r):
    "_"
    now, db, res = '%s' % datetime.datetime.now(), '/cup/rates', 0
    dr = dbm.open(db, 'w')
    if bytes(now[:10], 'ascii') in dr.keys():
        h = eval(dr[bytes(now[:10], 'ascii')])
        if 'IGCUSD' in h.keys(): res = h['IGCUSD']/h[r+'USD']
    dr.close()
    return res
    

def reg(value):
    " function attribute is a way to access matching group in one line test "
    reg.v = value
    return value

def init_db(db, db1):
    "_"
    if not os.path.isfile(db):
        d = dbm.open(db[:-3], 'c')
        d['__DIGEST__'] = __digest__
        d.close()
    if not os.path.isfile(db1):
        d = dbm.open(db1[:-3], 'c')
        d.close()

def log(s, ip=''):
    "Append to head log file"
    logf, now = '/cup/log', '%s' % datetime.datetime.now()
    if not os.path.isfile(logf): open(logf, 'w', encoding='utf8').write('%s|%s Log file Creation\n' % (now[:-7], ip) )     
    cont = open(logf, 'r', encoding='utf8').read()
    open(logf, 'w', encoding='utf8').write('%s|%s|%s\n%s' % (now[:-7], ip, s, cont))

def pdf_receipt(td, ig, slr, byr, url, ncl, sig):
    "_"
    try: ig.encode('ascii')
    except: ig = '%s' % bytes(ig, 'utf8')
    try: byr.encode('ascii')
    except: byr = '%s' % bytes(byr, 'utf8')
    try: slr.encode('ascii')
    except: slr = '%s' % bytes(slr, 'utf8')
    content = [[(100, 300, '32F1', 'Invoice'),
                (420,  18, '12F1', td), 
                (20,  400, '14F1', 'Buyer: %s' % byr), 
                (20,  430, '14F1', 'Seller: %s' % slr), 
                (20,  460, '14F1', 'Intangible Good:'), 
                (300, 460, '18F1', ig), 
                (300, 500, '9F1',  '%d instances sold' % ncl), 
                (10,  630, '12F1', 'Digital Signature of dedicated IG \(RSA 4096\):'),
                (10,  650, '10F3', sig),
                (10,  782, '8F1',  url),
                ]]
    a = updf(595, 842)
    return a.gen(content)

def pdf_statement(own, bal, ovd, h):
    "_"
    url, size, c1, c2, content, tabb = 'http://cupfoundation.net', 54, 430, 480, [], sorted(h.keys(), reverse=True)
    tp = 1 + len(tabb)//size
    today = '%s' % datetime.datetime.now()
    for i in range(tp):
        tab = tabb[i*size:(i+1)*size]
        label = '\n'.join(['%02d/%d %s\n' % (k+1, i+1, x[:-15]) for k, x in enumerate(tab)])
        relat = '\n'.join(['%s\n' % h[x][2] for x in tab])
        ig    = '\n'.join(['%s\n' % h[x][1] for x in tab])        
        crdit = '\n'.join([('%09.2f' % h[x][3] if h[x][0] else ' ') for x in tab])
        debit = '\n'.join([(' ' if h[x][0] else '%09.2f' % h[x][3]) for x in tab])
        t1, t2 = sum([(0 if h[x][0] else h[x][3]) for x in tab]), sum([(h[x][3] if h[x][0] else 0) for x in tab])
        page = [(410,  18, '12F1', today[:19]), 
                (30,  20, '14F1', own), (20,  230, '10F1', 'Overdraft:'), (80,  230, '10F3', '%9.0f' % ovd), 
                (20,  250, '14F1', 'Balance:'), (80, 250, '10F6', '%9.2f' % bal), (c1 if bal>0 else c2, 250, '8F3', '%09.2f' % abs(bal)),
                (320, 240, '8F3', 'Volume'), (c1, 240, '8F6', '%09.2f' % t2), (c2, 240, '8F6', '%09.2f' % t1), 
                (12,  260, '8F3', label), (160, 260, '8F1', ig), (340, 260, '8F1', relat), (c1, 260, '8F3', crdit), (c2, 260, '8F3', debit), 
                (10,  782, '8F1', url), (500,  782, '8F1', 'page %d/%d' % (i+1, tp))]
        content.append(page)
    a = updf(595, 842)
    return a.gen(content)

def pdf_conversion(td, own, val):
    "_"
    r = get_my_rate('EUR')
    page = [(410,  18, '12F1', td), 
            (30,  20, '14F1', own), 
            (20,  250, '12F1', 'My Bank:'),                     (220,  250, '14F3', 'Banque Pop'),
            (20,  300, '12F1', 'Nominal rate:'),                (220,  300, '12F3', '%9.6f' % r),   (300,  300, '9F1', 'EUR/'), (324,  300, '6F1', '⊔'),
            (20,  320, '12F1', 'Amount for exchange:'),         (220,  320, '12F3', '%9.2f' % val),          (300,  320, '8F1', '⊔'),
            (20,  340, '12F1', 'Amount for exchange:'),         (220,  340, '12F3', '%9.2f' % (val*r)),      (300,  340, '9F1', 'EUR'),
            (20,  360, '12F1', 'Taxes \(2.0%\):'),              (220,  360, '12F3', '%9.2f' % (val*.02*r)),  (300,  360, '9F1', 'EUR'),
            (20,  380, '12F1', 'Total:'),                       (220,  380, '12F6', '%9.2f' % (val*1.02*r)), (300,  380, '9F1', 'EUR'),
            ] 
    a = updf(595, 842)
    return a.gen([page])

def pdf_test(own, ig, attr, li):
    "_"
    today = '%s' % datetime.datetime.now()
    page = [
        (410,  18, '12F1', today[:19]), 
        (30, 20, '14F1', own), 
        (20, 260, '14F1', 'Intangible Good:'), 
        (50, 330, '24F1', ig), 
        (20, 430, '12F3', attr), 
        (40, 460, '12F3', li[0]), (40, 480, '12F3', li[1]), (40, 500, '12F3', li[2]), (40, 520, '12F3', li[3]), 
        ] 
    a = updf(595, 842)
    return a.gen([page])

def api():
    """All requests can be send in GET or in POST
In Python, but one can use any other server side languages, for 
\tco = http.client.HTTPConnection(host)    
one can call:
\tco.request('POST', '/bank', urllib.parse.quote(cmd))\nor
\tco.request('GET', '/bank?' + urllib.parse.quote(cmd))
to get the response, use: 
\tco.getresponse().read()
for binary (encrypted string or PDF), or
\tco.getresponse().read().decode('utf8') 
for utf-8 or ascii string 
All requests include a signature of the sender for authentication\n 
\n1/Register a user
\treg/user/iduser/public_key/signature
where:
'user' is a name in any Unicode length<80 ('/' is the only not allowed character). 
'iduser' is a valid personnal identifier. For French users, it 'fr' with the social security number
'public_key' is the RSA 4096bits length public key in base64 encoding (url safe)....Never send your Private key!
'signature' is the RSA signature from the user of the string: "date/user/userid", date should be at day precision, like ""
\n\n2/Register an Intangible good
\tig/user/ig_id/first_unitary_price/maximum_income/signature
where:
'signature' of the string: "date/user/ip_id/price_first/max_income"
\n\n2/Buy an Intangible good
\tig/user/ig_id/first_unitary_price/maximum_income/signature
where:
blabla
\t
...
"""
    return api.__doc__

def application(environ, start_response):
    "wsgi server app"
    mime, o, db, db1, today = 'text/plain; charset=utf8', 'Error:', '/cup/bank.db', '/cup/rates.db', '%s' % datetime.datetime.now()
    init_db(db, db1)
    if environ['REQUEST_METHOD'].lower() == 'post':
        raw, way = urllib.parse.unquote(environ['wsgi.input'].read().decode('utf8')), 'post'
    else:
        raw, way = urllib.parse.unquote(environ['QUERY_STRING']), 'get'
    log(raw[:10] + '...', environ['REMOTE_ADDR'])
    d = dbm.open(db[:-3], 'c')
    if len(raw) < MAX_ARG_SIZE:
        # register()
        if reg(re.match(r'^(user|reg|register)/([^/]{3,50})/([^/]{3,17})/([^/]{680,685})/([^/]{680,685})$', raw, re.U)):
            # checks both id and public key not already used and local id is valid
            own, uid, pbk, sig = reg.v.group(2), reg.v.group(3), reg.v.group(4), reg.v.group(5)
            Por, Bor, Oor, Tor, Uid = b'P_' + bytes(own, 'utf8'), b'B_' + bytes(own, 'utf8'), b'O_' + bytes(own, 'utf8'), b'T_' + bytes(own, 'utf8'), b'U_' + bytes(uid, 'utf8')
            if Por in d.keys():
                o += 'public key already exists for %s !' % own 
            elif (uid != 'anonymous') and (Uid in d.keys()):
                o += 'user id already registered for %s !' % own 
            elif verify(RSA_E, b64toi(bytes(pbk, 'ascii')), '/'.join((today[:10], own, uid)), bytes(sig, 'ascii')):
                d[Oor] = '100' if reg(re.match('^fr\d{15}$', uid)) and int(uid[-2:]) == (97 - int(uid[2:-2])%97) else '0' # french id!                    
                d[Por], d[Bor], d[Uid], o = pbk, '0', own, 'Public key id registration OK for \'%s\'' % own 
            else:
                o += ' something wrong in user registration!'
        # igreg()
        elif reg(re.match(r'^(ig|igreg|immaterial|good)/([^/]{3,50})/([^/]{3,80})/([^/]{1,12})/([^/]{1,12})/(\d{1,3})/([^/]{680,685})$', raw, re.U)): 
            # checks
            own, iid, p1, pf, xi, sig = reg.v.group(2), reg.v.group(3), reg.v.group(4), reg.v.group(5), reg.v.group(6), reg.v.group(7)
            Iig, Cig, Ppk = b'I_' + bytes(iid, 'utf8'), b'C_' + bytes(iid, 'utf8'), bytes('P_%s' % own, 'utf8')
            if Iig in d.keys():
                o += 'IG id already set!'
            elif float(p1)<0 or float(pf)<float(1):
                o += 'bad prices!'
            elif verify(RSA_E, b64toi(d[Ppk]), '/'.join((today[:10], own, iid, p1, pf, xi)), bytes(sig, 'ascii')):
                ra = os.urandom(16)
                akey = itob64(int(binascii.hexlify(os.urandom(16)), 16))
                era = encrypt(RSA_E, b64toi(d[Ppk]), akey)
                d[Iig], d[Cig] = '/'.join((today[:10], p1, pf, xi, own, akey.decode('ascii'))), b' '
                #o = 'IG id registration OK from \'%s\'' % own
                o, mime = era, 'application/pdf'
            else:
                o += 'ig registration fail!'
        # buy()
        elif reg(re.match(r'^(buy)/([^/]{3,50})/([^/]{3,80})/([^/]{26})/([^/]{680,685})$', raw, re.U)):
            # checks 
            byr, ig, td, sig = reg.v.group(2), reg.v.group(3), reg.v.group(4), reg.v.group(5)
            Bby, Pby, Oby, Ttr = b'B_'+bytes(byr, 'utf8'), b'P_' + bytes(byr, 'utf8'), b'O_' + bytes(byr, 'utf8'), b'T_' + bytes(sig[:20], 'ascii'), 
            Iig, Cig = b'I_' + bytes(ig, 'utf8'), b'C_' + bytes(ig, 'utf8')
            if verify(RSA_E, b64toi(d[Pby]), '/'.join((byr, ig, td)), bytes(sig, 'ascii')) and Iig in d.keys() and not (Ttr in d.keys()):
                tab, tac = d[Iig].decode('utf8').split('/'), d[Cig].decode('utf8').split('/')
                prc, slr = float(tab[1]), tab[4]
                Bsr = b'B_'+bytes(slr, 'utf8')
                i = len(tac)-1
                if i == 0:
                    p = prc
                else:
                    p1, pf, xi = float(tab[1]), float(tab[2]), float(tab[3])/100 # 6/ get nb, p1, pf, xi
                    k = math.log(pf-p1) - math.log(pf-2*p1)          
                    p = (pf - (pf-p1)*math.exp(-xi*i*k))/(i+1)               # new price
                    dt = (pf-p1)*(math.exp(-xi*(i-1)*k) - math.exp(-xi*i*k)) # new delta
                    rfd = (p-dt)/i                                           # 7/ update prices
                if float(d[Bby]) - p > - float(d[Oby]):
                    d[Bby] = '%f' % (float(d[Bby]) - p)
                    d[Bsr] = '%f' % (float(d[Bsr]) + (p if i==0 else dt))
                    if i != 0:
                        for j, cst in enumerate(tac[1:]):
                            Bcs = b'B_'+bytes(cst, 'utf8')
                            d[Bcs] = '%f' % (float(d[Bcs]) + rfd)
                            d[bytes('T_%s_%04d' %(sig[:15], j), 'ascii')] = '/'.join((td, ig, 'refund', cst, '0', '%s' % rfd))
                    d[Cig] += b'/' + bytes(byr, 'utf8')
                    d[Ttr] = '/'.join((td, ig, byr, slr, '%s' % p, '%s' % (p if i== 0 else dt))) 
                    era = encrypt(RSA_E, b64toi(d[Pby]), bytes(tab[5], 'ascii'))
                    o, mime = era, 'application/pdf'
                else:
                    o += 'account not funded!'
            else:
                o += 'ig buy!'
        # download()
        elif reg(re.match(r'^(download)/([^/]{3,50})/([^/]+)/([^/]{680,685})$', raw, re.U)):
            # checks 
            byr, era, sig = reg.v.group(2), reg.v.group(3), reg.v.group(4)
            o += 'download!'
        # isclient()
        elif reg(re.match(r'^(isclient)/([^/]{3,50})/([^/]{3,50})/([^/]{3,80})/([^/]{680,685})$', raw, re.U)):
            # checks 
            slr, byr, ig, sig = reg.v.group(2), reg.v.group(3), reg.v.group(4), reg.v.group(5)
            Psl, Cig = b'P_' + bytes(slr, 'utf8'), b'C_' + bytes(ig, 'utf8') 
            if verify(RSA_E, b64toi(d[Psl]), '/'.join((slr, byr, ig, today[:10])), bytes(sig, 'ascii')):
                tac = d[Cig].decode('utf8').split('/')
                if len(tac)>1 and byr in tac:
                    o = '%d' % len(tac)-1 # send number of customers
                    o, mime = pdf_receipt('td', 'ig', 'owner', 'byr', 'url', 1, 'sig'), 'application/pdf'
                else:
                    o += 'not client!'
            else:
                o += 'bad signature!'
        # playlist()
        elif reg(re.match(r'^(playlist)/([^/]{3,50})/([^/]{680,685})$', raw, re.U)):
            owr, sig, res = reg.v.group(2), reg.v.group(3), ''
            Por = b'P_' + bytes(owr, 'utf8') 
            if verify(RSA_E, b64toi(d[Por]), '/'.join((owr, today[:10])), bytes(sig, 'ascii')):
                for x in d.keys():
                    if reg(re.match('C_(.*)$', x.decode('utf8'))):
                        if owr in d[x].decode('utf8').split('/'):
                            res += '/' + reg.v.group(1)
                    if reg(re.match('I_(.*)$', x.decode('utf8'))):
                        if owr == d[x].decode('utf8').split('/')[4]:
                            res += '/' + reg.v.group(1)
                o = res
            else:
                o += 'playlist empty!'
        # receipt()
        elif reg(re.match(r'^(receipt)/([^/]{3,50})/([^/]{3,80})/([^/]{680,685})$', raw, re.U)):
            own, ig, sig = reg.v.group(2), reg.v.group(3), reg.v.group(4)
            Bow, Oow, Pow = b'B_'+bytes(own, 'utf8'), b'O_'+bytes(own, 'utf8'), b'P_' + bytes(own, 'utf8') 
            if verify(RSA_E, b64toi(d[Pow]), '/'.join(('rp', own, ig, today[:10])), bytes(sig, 'ascii')):
                #for x in d.keys():
                #    if reg(re.match('T_(.*)$', x.decode('utf8'))):
                Iig, Cig = b'I_' + bytes(ig, 'utf8'), b'C_' + bytes(ig, 'utf8')
                tab = d[Iig].decode('utf8').split('/')
                author = tab[4]
                #nb = len(d[Cig].split('/'))-1
                try: author.encode('ascii')
                except: author = ('%s' % bytes(author, 'utf8'))[2:-1]
                try: own.encode('ascii')
                except: own = ('%s' % bytes(own, 'utf8'))[2:-1]
                try: ig.encode('ascii')
                except: ig = ('%s' % bytes(ig, 'utf8'))[2:-1]
                o, mime = pdf_test(own, ig[:-4], author, tab[0:4]), 'application/pdf'
            else:
                o += 'pdf receipt reading!'            
        # statement()
        elif reg(re.match(r'^(state|statement)/([^/]{3,50})/([^/]{680,685})$', raw, re.U)):
            own, sig = reg.v.group(2), reg.v.group(3)
            Bow, Oow, Pow = b'B_'+bytes(own, 'utf8'), b'O_'+bytes(own, 'utf8'), b'P_' + bytes(own, 'utf8') 
            if verify(RSA_E, b64toi(d[Pow]), '/'.join(('st', own, today[:10])), bytes(sig, 'ascii')):
                o, a, h = 'balance: \t%9.2f⊔\n' % (float(d[Bow].decode('ascii'))), [], {}
                for x in d.keys():
                    if reg(re.match('T_(.*)$', x.decode('utf8'))):
                        tab = d[x].decode('utf8').split('/')
                        if own in (tab[2], tab[3]):
                            tg = tab[3] if own == tab[2] else tab[2]
                            try: tg.encode('ascii')
                            except: tg = ('%s' % bytes(tg, 'utf8'))[2:-1]
                            ig = tab[1][:-4]
                            try: ig.encode('ascii')
                            except: ig = ('%s' % bytes(ig, 'utf8'))[2:-1]
                            k = ' '.join((tab[0][:19], x[2:].decode('ascii')))
                            if tab[2] == tab[3]:
                                h[k] = (True, ig, tg, float(tab[4]) - float(tab[5]))
                            else:
                                h[k] = (True, ig, tg, float(tab[4])) if own == tab[2] else (False, ig, tg, float(tab[5]))
                own1 = own
                try: own1.encode('ascii')
                except: own1 = ('%s' % bytes(own1, 'utf8'))[2:-1]
                o, mime = pdf_statement(own1, float(d[Bow].decode('ascii')), float(d[Oow].decode('ascii')), h), 'application/pdf'
            else:
                o += 'statement reading!'            
        # balance()
        elif reg(re.match(r'^(balance)/([^/]{3,50})/([^/]{680,685})$', raw, re.U)):
            own, sig = reg.v.group(2), reg.v.group(3)
            Bow, Oow, Pow = b'B_'+bytes(own, 'utf8'), b'O_'+bytes(own, 'utf8'), b'P_' + bytes(own, 'utf8') 
            if verify(RSA_E, b64toi(d[Pow]), '/'.join((own, today[:10])), bytes(sig, 'ascii')):
                o = '%9.2f %9.2f' % (float(d[Bow].decode('ascii')), float(d[Oow].decode('ascii')))
            else:
                o += 'balance reading!'            
        # conversion()
        elif reg(re.match(r'^(conversion)/([^/]{3,50})/([\d\.]{1,20})/([^/]{680,685})$', raw, re.U)):
            own, val, sig = reg.v.group(2), reg.v.group(3), reg.v.group(4)
            Bow, Oow, Pow = b'B_'+bytes(own, 'utf8'), b'O_'+bytes(own, 'utf8'), b'P_' + bytes(own, 'utf8') 
            if verify(RSA_E, b64toi(d[Pow]), '/'.join(('ex', own, val, today[:10])), bytes(sig, 'ascii')):
                try: own.encode('ascii')
                except: own = ('%s' % bytes(own, 'utf8'))[2:-1]
                o, mime = pdf_conversion(today[:19], own, float(val)), 'application/pdf'
            else:
                o += 'conversion!'            
        elif way == 'get':
            if raw.lower() in ('source', 'src'):
                o = open(__file__, 'r', encoding='utf8').read()
            elif raw.lower() in ('help', 'about'):
                o = 'Welcome to ⊔net!\n\nHere is the Help in PDF format soon!'
            elif raw.lower() in ('api',):
                o = api()
            elif raw.lower() == 'reset':
                subprocess.call(('rm', '-f', db, '/cup/nodes/keys.db')) # Of course this is only temporary available for testing!!!
                o = 'RESET DATABASE OK!'
            elif raw.lower() in ('host',):
                o, mime = open('/cup/host.jpg', 'rb').read(), 'image/jpeg'
            elif raw.lower() in ('log',):
                o = open('/cup/log', 'r', encoding='utf8').read()                
            elif raw.lower() in ('list', 'raw'):
                o = ''
                for x in d.keys():
                    if reg(re.match('I_(.*)$', x.decode('utf8'))):
                        tab = d[x].decode('utf8').split('/')
                        cu = 'C_' + reg.v.group(1)
                        if bytes(cu, 'utf8') in d.keys():
                            o += '%s/%s/%s\n' % (x[2:].decode('utf8'), '/'.join(tab[:-1]), len(d[cu].split(b'/'))-1)
            else:
                o, mime = frontpage(today, environ['REMOTE_ADDR']), 'application/xhtml+xml; charset=utf8'
    else:
        o += 'arg too long'
    d.close()
    start_response('200 OK', [('Content-type', mime)])
    return [o if mime == 'application/pdf' or mime == 'image/jpeg' else o.encode('utf8')] 

def favicon():
    "_"
    code = '<svg %s n="%s"><path stroke-width="4" fill="none" stroke="Dodgerblue" d="M3,1L3,14L13,14L13,1"/></svg>' % (_SVGNS, datetime.datetime.now())
    tmp = base64.b64encode(code.encode('utf8'))
    return '<link xmlns="http://www.w3.org/1999/xhtml" rel="shortcut icon" type="image/svg+xml" href="data:image/svg+xml;base64,%s"/>\n' % tmp.decode('utf8')

def frontpage(today, ip):
    "not in html!"
    rates = get_rates() 
    d = dbm.open('/cup/bank')
    nb, ck, tr, di, ni, v1, v2 = 0, 0, 0, d['__DIGEST__'], 0, 0 ,0
    for x in d.keys():
        if re.match('B_', x.decode('utf8')):
            nb += 1
            ck += float(d[x])
        elif re.match('I_', x.decode('utf8')):
            ni += 1
        elif re.match('T_', x.decode('utf8')):
            tab = d[x].split(b'/')
            v1 += float(tab[4])
            v2 += float(tab[5])
            tr += 1
    d.close()
    #assert(abs(v1-v2) < PRECISION and abs(ck) < PRECISION)
    o = '<?xml version="1.0" encoding="utf8"?>\n' 
    o += '<svg %s %s>\n' % (_SVGNS, _XLINKNS) + favicon()
    o += '<style type="text/css">@import url(http://fonts.googleapis.com/css?family=Schoolbell);svg{max-height:100;}text,path{stroke:none;fill:Dodgerblue;font-family:helvetica;}text.foot{font-size:18pt;fill:gray;text-anchor:middle;}text.rate{font-family:courier; font-size:9pt; fill:#333;}text.alpha{font-family:Schoolbell;fill:#F87217;text-anchor:middle}text.note{fill:#CCC;font-size:9pt;text-anchor:end;}input{padding:5px;border:1px solid #D1D1D2;border-radius:10px;font-size:24px;}input[type="text"]{color:#999;}input[type="submit"]{color:#FFF;}</style>\n'
    o += '<a xlink:href="%s"><path stroke-width="0" d="M10,10L10,10L10,70L70,70L70,10L60,10L60,60L20,60L20,10z"/></a>\n' % __url__
    o += '<text x="80" y="70" font-size="45" title="banking for intangible goods">Bank</text>\n'

    if rates:
        o += '<text x="15" y="88" font-size="10">%s</text>\n' % today[:10] 
        o += '<text class="rate" x="15" y="102" font-size="10">1⊔ =</text>\n' 
        for i, x in enumerate(rates.keys()): o += '<text class="rate" x="110" y="%d" text-anchor="end">%9.6f %s</text>\n' % (116+15*i, rates[x], x)
        for i, x in enumerate(rates.keys()): o += '<text class="rate" x="150" y="%d" text-anchor="start">%s = %9.8f⊔</text>\n' % (116+15*i, x, 1/rates[x])

    o += '<text class="alpha" font-size="16pt" x="92"  y="25" title="still in security test phase!" transform="rotate(-30 92,25)">Beta</text>\n'
    #o += '<text class="alpha" font-size="50pt" x="50%" y="40%"><tspan title="only HTTP (GET or POST), SVG and CSS!">No https, no html, no JavaScript,</tspan><tspan x="50%" dy="100" title="better privacy also!">better security!</tspan></text>\n'
    o += '<text class="alpha" font-size="50pt" x="50%" y="25%"><tspan title="only HTTP (GET or POST), SVG and CSS!">No https, no html, </tspan><tspan x="50%" dy="85" title="no JavaScript!">no JavaScript,</tspan><tspan x="50%" dy="85" title="better privacy also!">better security!</tspan></text>\n'

    o += '<text class="foot" x="50%%" y="50" title="today">%s</text>\n' % today[:19]
    o += '<text class="foot" x="16%%" y="88%%" title="registered users">%04d users</text>\n' % nb
    o += '<text class="foot" x="38%%" y="88%%" title="">%06d transactions</text>\n' % tr
    o += '<text class="foot" x="62%%" y="88%%" title="number of registered Intangible Goods">%04d IGs</text>\n' % ni
    o += '<text class="foot" x="84%%" y="88%%" title="absolute value">Volume: %09.2f ⊔</text>\n' % v1
    o += '<a xlink:href="bank?src" ><text class="note" x="160" y="98%" title="on GitHub (https://github.com/pelinquin/cup) hack it, share it!">Download the source code!</text></a>\n'
    #o += '<foreignObject x="40%%" y="100" width="600" height="100"><div %s><form method="post">\n' % _XHTMLNS
    #o += '<input type="text" name="q"/><input type="submit" value="IG Search" title="Intangible Goods Search Request"/>\n'
    #o += '</form></div></foreignObject>\n'
    if ip == '127.0.0.1': 
        o += '<text class="note" x="160" y="90"  title="my ip adress">local server</text>\n'
    o += '<a xlink:href="bank?help"><text class="note" x="99%" y="20" title="help">Help</text></a>\n'
    o += '<a xlink:href="bank?host"><text class="note" x="99%" y="40" title="at home!">Host</text></a>\n'            
    o += '<a xlink:href="bank?log" ><text class="note" x="99%" y="60" title="log file">Log</text></a>\n'
    o += '<a xlink:href="bank?list"><text class="note" x="99%" y="80" title="ig list">List</text></a>\n'
    o += '<a xlink:href="bank?api"><text class="note" x="99%" y="100" title="for developpers">API</text></a>\n'
    o += '<text class="note" x="50%%" y="98%%" title="you can use that server!">Status: <tspan fill="%s</tspan></text>\n' % ('green">OK' if (abs(ck) < PRECISION) else 'red">Error!')
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

def format_cmd1(post, cmd):
    co = http.client.HTTPConnection(host)    
    if post:
        co.request('POST', '/bank', urllib.parse.quote(cmd))
    else:
        co.request('GET', '/bank?' + urllib.parse.quote(cmd))
    res = co.getresponse().read()
    if res[:5] == b'Error':
        return res.decode('utf8')    
    else:
        return res
    
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
    s = sign(ki[1], ki[2], '/'.join((td[:10], owner, iduser)))
    assert (verify(RSA_E, ki[2], '/'.join((td[:10], owner, iduser)), s))
    cmd = '/'.join(('reg', owner, iduser, kb[2].decode('ascii'), s.decode('ascii')))
    return format_cmd(post, cmd)

def igreg(owner, idig, p1, pf, host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')
    ki = [b64toi(x) for x in ds[owner].split()]
    ds.close()
    s = sign(ki[1], ki[2], '/'.join((td[:10], owner, idig, '%s' % p1, '%s' % pf)))
    cmd = '/'.join(('ig', owner, idig, '%s' % p1, '%s' % pf, s.decode('ascii')))
    era = format_cmd1(post, cmd)
    if era[:5] != 'Error':
        sk = decrypt(ki[1], ki[2], era)
        d = dbm.open('/cup/mysite', 'c')
        d[sk] = ig
        d.close()
    return era

def transaction(byr, slr, prc, host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')
    ki = [b64toi(x) for x in ds[byr].split()]
    ds.close()
    s = sign(ki[1], ki[2], '/'.join((byr, slr, '%s' % prc, td)))
    cmd = '/'.join(('transaction', byr, slr, '%s' % prc, td, s.decode('ascii')))
    return format_pdf(post, cmd, 'tata')


def isclient(slr, byr, ig, host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')
    ki = [b64toi(x) for x in ds[slr].split()]
    ds.close()
    s = sign(ki[1], ki[2], '/'.join((slr, byr, ig, td[:10])))
    cmd = '/'.join(('isclient', slr, byr, ig, s.decode('ascii')))
    return format_cmd(post, cmd)

def download(byr, url, host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')
    ki = [b64toi(x) for x in ds[byr].split()]
    ds.close()
    era = encrypt(RSA_E, ki[2], url)
    s = sign(ki[1], ki[2], '/'.join((byr, td[:10], '%s' % era[:20])))
    cmd = '/'.join(('download', byr, '%s' % era, s.decode('ascii')))
    return format_pdf(post, cmd, 'tata')

def prep_transaction(byr, slr, prc, host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')
    ki = [b64toi(x) for x in ds[byr].split()]
    ds.close()
    s = sign(ki[1], ki[2], '/'.join((byr, slr, '%s' % prc, td)))
    cmd = '/'.join(('transaction', byr, slr, '%s' % prc, td, s.decode('ascii')))
    return 'http://%s/bank?%s' % (host, urllib.parse.quote(cmd))

def statement(own, host='localhost', post=False):
    "_"
    td, ds = '%s' % datetime.datetime.now(), dbm.open('/u/sk')
    ki = [b64toi(x) for x in ds[own].split()]
    ds.close()
    s = sign(ki[1], ki[2], '/'.join((own, td[:10])))
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
        if par[3] == '⊔':
            w, x, y = int(par[2].split('F')[0]), par[0]+self.mx, self.ph-par[1]-self.my
            o = '.11 .35 1.0 rg %s %s %s %s re %s %s %s %s re %s %s %s %s re f 0 0 0 rg ' % (x, y, w, w/4, x, y, w/4, 1.5*w, x+w, y, w/4, 1.5*w)
        else:
            ff, other = par[2].split('F'), False
            o = '1 0 0 1 %s %s Tm /F%s %s Tf %s TL ' % (par[0]+self.mx, self.ph-par[1]-self.my, ff[1], ff[0], 1.2*int(ff[0]))
            for m in re.compile(r'([^\n]+)').finditer(par[3]):
                o += '%s[(%s)]TJ ' % ('T* ' if other else '', self.kern(m.group(1), self.afm[int(ff[1])-1])) 
                other = True
        return o

    def gen(self, document):
        "generate a valid binary PDF file, ready for printing!"
        np = len(document)
        self.o += b'\xBF\xF7\xA2\xFE\n' if self.binary else b'ASCII!\n'
        self.add('/Linearized 1.0/L 1565/H [570 128]/O 11/E 947/N 111/T 1367')
        ref, kids, seenall, fref, h, firstp = [], '', {}, [], {}, 0
        for p, page in enumerate(document):
            w, x, y = 12, 26, 798
            t = bytes('.11 .35 1 rg %s %s %s %s re %s %s %s %s re %s %s %s %s re f ' % (x, y, w, w/4, x, y, w/4, 1.5*w, x+w, y, w/4, 1.5*w),'ascii')
            t += bytes('BT 1 w 0.9 0.9 0.9 RG %s %s %s %s re S 0 0 0 RG 0 Tc ' % (self.mx, self.my, self.pw-2*self.mx, self.ph-2*self.my), 'ascii')
            t += b'0.99 0.99 0.99 rg 137 150 50 400 re f 137 100 321 50 re f 408 150 50 400 re f '
            t += b'0.88 0.95 1.0 rg 44 600 505 190 re f '
            t += b'1.0 1.0 1.0 rg 1 0 0 1 60 680 Tm /F1 60 Tf (Put your Ads here)Tj 0.0 0.0 0.0 rg '
            t += b'0.9 0.9 0.9 rg 499 740 50 50 re f '
            t += b'1.0 1.0 1.0 rg 1 0 0 1 512 776 Tm 14 TL /F1 12 Tf (Ads)Tj T* (QR)Tj T* (Code)Tj 0.0 0 0 rg '
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
    # debug zone!
    popu = {
        'Pelinquin':        'anonymous', 
        'Carl⊔':            'anonymous', 
        }    
    man, woman, ig, host = 'Laurent Fournier', 'Valérie Fournier', 'myig_您1', 'localhost'
    host = 'pi.pelinquin.fr'


    url = 'www.creditmutuel.fr/groupe/fr/index.html'.split('/')
    co = http.client.HTTPSConnection(url[0])
    co.request('GET', '/' + '/'.join(url[1:]))
    res = co.getresponse()
    if res.reason == 'OK':
        print ('OK')
    else:
        print (res.status, res.msg['location'])

    sys.exit()

# End ⊔net!
