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

import sys, re, os, math, random, urllib.parse, dbm, datetime, base64, hashlib, subprocess, shutil, smtplib, binascii, http.client
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES
__digest__ = base64.urlsafe_b64encode(hashlib.sha1(open(__file__, 'r', encoding='utf-8').read().encode('utf-8')).digest())[:5]

# constants defined by government banking authorities and should be as stable as possible while should pass the test bellow!
__cur_ratio__ = {
    'EUR':[' €',  0.781,  0.78996,   0.870, 'Euro'], 
    'USD':[' $',  0.998,  1.064,     1.107, 'United State Dollar'],
    'CAD':[' $',  0.990,  1.056495,  1.102, 'Canadian Dollar'], 
    'GBP':[' £',  0.651,  0.672573,  0.702, 'Great Britain'], 
    'JPY':[' ¥', 85.104, 93.4582,   96.832, 'Japan'], 
    'CNY':[' Ұ',  6.405,  6.63024,   6.703, 'China'],
    'BRL':['R$',  2.132,  2.158722,  2.275, 'Brasil'],
    }

def utility():
    "_"
    dtax = dbm.open('/u/tax')
    h = eval(dtax['HASH']) 
    dtax.close()
    h['USDUSD'] = 1
    base = __cur_ratio__['USD'][2]
    old_ratio = {x:__cur_ratio__[x][2] for x in __cur_ratio__}
    for c in __cur_ratio__:
        __cur_ratio__[c][2] = base*h['USD'+c]
    u = 0
    for c in __cur_ratio__:
        u += 100*abs(__cur_ratio__[c][2] - old_ratio[c])/__cur_ratio__[c][2]
    print (u)

def utility2():
    "_"
    dtax = dbm.open('/u/tax')
    nh = eval(dtax['HASH']) 
    oh = eval(dtax['OLD_HASH']) 
    rn = eval(dtax['RATE'])
    ro = eval(dtax['OLD_RATE'])
    dtax.close()
    u = 0
    for c in __cur_ratio__:
        u += 100*abs(rn[c] - ro[c])/ro[c]
    print (u)


def get_today_rates():
    "_"
    co, h = http.client.HTTPConnection('currencies.apps.grandtrunk.net'), {}
    log ('currencies.apps.grandtrunk.net')
    for c in __cur_ratio__:
        if c != 'USD':
            co.request('GET', '/getlatest/%s/USD' %c)
            h[c+'USD'] = float(co.getresponse().read())
    for c in __cur_ratio__:
        if c != 'USD':
            h['USD'+c] = 1/h[c+'USD']
    for c1 in __cur_ratio__:
         for c2 in __cur_ratio__:
             if c1 != c2 and (c1 != 'USD') and (c2 != 'USD'): 
                 h[c1+c2] = h[c1+'USD'] * h['USD'+c2]
    h['USDUSD'] = 1
    co.close()
    return h 

def test_cup_ratios():
    "_"
    #global __cur_ratio__
    now = '%s' % datetime.datetime.now()
    o, ko = '<p title="The test checks that first that taxes are positives and second it is never valuable to exchange from one local currency to another using ⊔ as intermediate.">%s: ⊔ currencies rates test: ' % now[:10], False 
    dtax = dbm.open('/u/tax', 'w')
    if dtax[b'TODAY'] == bytes(now[:10],'ascii'):
        h = eval(dtax[b'HASH'])
        #__cur_ratio__ = eval(dtax[b'RATE'])
    else:
        if b'HASH' in dtax.keys(): 
            dtax[b'OLD_HASH'], dtax[b'OLD_RATE'] = dtax[b'HASH'], dtax[b'RATE']    
        h = get_today_rates() # only once a day!
        if b'HASH' not in dtax.keys(): 
            dtax[b'OLD_HASH'] = '%s' % h    
            dtax[b'OLD_RATE'] = '%s' % {x:__cur_ratio__[x][2] for x in __cur_ratio__}
        dtax[b'HASH'] = '%s' % h
        dtax[b'RATE'] = '%s' % {x:__cur_ratio__[x][2] for x in __cur_ratio__}
        dtax[b'TODAY'] = '%s' % now[:10]
    dtax.close()
    for r in __cur_ratio__:
        if (__cur_ratio__[r][1] > __cur_ratio__[r][2]) or (__cur_ratio__[r][2] > __cur_ratio__[r][3]):
            ko = True
            o += '<br/><b class="red">ERROR: rates for %s</b>' % r
    for r in h:
        r1, r2 = r[:3], r[3:]
        t =  __cur_ratio__[r2][3]/__cur_ratio__[r1][1]
        if t < h[r] :
            ko = True
            o += '<br/><b class="red">ERROR: %s/%s: %5.2f</b>' % (r1, r2, 100*(t-h[r])/h[r])
    if not ko:
        o += '<b>pass</b>'
    return o + '</p>\n'

loc = {
    'bal': ['Balance',                  'Solde'],
    'new': ['New Good',                 'Nouveau bien'],
    'sha': ['Share',                    'Partager'],
    'buy': ['Buy',                      'Acheter'],
    'cIG': ['Created Intangible Goods', 'Biens immatériel créés'],
    'bIG': ['Bought Intangible Goods',  'Biens immatériel achetés'],
    'cur': ['Currency',                 'Monnaie'],
    'bra': ['Buy ⊔ Ratio',              'Taux d\'achat /⊔'],  	
    'nra': ['Nominal ⊔ Ratio',          'Taux nominal /⊔'],	
    'sra': ['Sale ⊔ Ratio',             'Taux de vente /⊔'],	
    'nbc': ['Nb of citizens',           'Nombre de citoyens'],	
    'tgt': ['Total Government Tax',     'Montant total des taxes'],
    }

def style():
    "_"
    return """<style type="text/css"> 
h1,h2,h3,h4,h5,h6,input,a,p,td,th,fh6{font-family:helvetica neue,helvetica,arial,sans-serif;}
h1,h2 {background-color:#F4F4F4; font-size:64;}
n1{font-variant: small-caps;font-size:44; text-decoration:underline; vertical-align: baseline; top:-.2em;position:relative; }
mail{font-family:courier; color: #666;}
net1{font-variant: small-caps; font-size: x-small; text-decoration:underline; vertical-align: baseline; top:-.2em;position:relative;}
net{font-variant: small-caps; text-decoration:underline;}
it{text-decoration:underline;font-style: italic; font-family: times}
sc{font-variant: small-caps}
a{text-decoration:none;}
b.red{color:red;}
h1,a{color:Dodgerblue;}
h6 {text-align:right;color:#CCC;background-color:#F4F4F4;}
td.num {text-align:right;}
fh6 {display:block;font-size:10; text-align:right;color:#AAA;}
l {text-align:left;}
p{padding-left:30;}
div{position:absolute; top:10;right:20;}
div.lang{position:absolute; top:20;right:110;width:140;}
p1 { font-family: 'Schoolbell','Arizonia', Helvetica, sans-serif; color: #2b2b2b; font-size:32;}
img {vertical-align:top;}
table.main {border: 1px solid #666;width:100%;border-collapse:collapse;} 
td,th {border: 1px solid #666;padding:2pt;}
td.in:active {background-color:red;}
table.ig {margin:0px; color:white;background-color:Dodgerblue; display:inline-table;} 
td.small {font-size:7px;border:none;text-align:center; }
p2.small {font-size:7px; }
td.ig {font-family:monospace;font-size:16px;border:none;text-align:center; heigth:10px;}

.toggle p span { display: none;}
.toggle { position: relative; padding: 0;margin-left: 80px;}
.toggle label {position: relative;z-index: 3;display: block;width: 100%;}
.toggle input {position: absolute;opacity: 0;z-index: 5;}
.toggle p {position: absolute;left: -100px;width: 100%;margin: 0;padding-right: 10px;text-align: left;}
.toggle p span {position: absolute;top: 0;left: 0;z-index: 5;display: block;width: 50%;margin-left: 100px;text-align: center;}
.toggle p span:last-child { left: 50%; }
.toggle .slide-button {position: absolute;right: 0;top: 0;z-index: 4;display: block;width: 50%;height: 100%;padding: 0;}
.toggle{ display: block; height: 20px; }
.toggle * {-webkit-box-sizing: border-box;-moz-box-sizing: border-box;-ms-box-sizing: border-box;-o-box-sizing: border-box;box-sizing: border-box;}
.toggle .slide-button {display: block;-webkit-transition: all 0.3s ease-out;-moz-transition: all 0.3s ease-out;-ms-transition: all 0.3s ease-out;-o-transition: all 0.3s ease-out;transition: all 0.3s ease-out;}
.toggle input:checked ~ .slide-button { right: 50%; }
.toggle input:focus ~ .slide-button,
.toggle { -webkit-animation: bugfix infinite 1s;}
.candy {background-color: #2d3035;color: #fff;font-weight: bold;text-align: center;text-shadow: 1px 1px 1px #191b1e;border-radius: 3px;	box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.3), 0 1px 0px rgba(255, 255, 255, 0.2);}
.candy input:checked + label { color: #333; text-shadow: 0 1px 0 rgba(255,255,255,0.5);}
.candy .slide-button {border: 1px solid #333;background-color: #70c66b;background-image: -webkit-linear-gradient(top, rgba(255, 255, 255, 0.2), rgba(0, 0, 0, 0));background-image:-moz-linear-gradient(top, rgba(255, 255, 255, 0.2), rgba(0, 0, 0, 0));background-image:     -ms-linear-gradient(top, rgba(255, 255, 255, 0.2), rgba(0, 0, 0, 0));background-image:-o-linear-gradient(top, rgba(255, 255, 255, 0.2), rgba(0, 0, 0, 0));background-image:linear-gradient(top, rgba(255, 255, 255, 0.2), rgba(0, 0, 0, 0));box-shadow: 0 1px 1px rgba(0, 0, 0, 0.2), inset 0 1px 1px rgba(255, 255, 255, 0.45);border-radius: 3px;}
.candy p { color: #333; text-shadow: none; }
.candy span { color: #fff; }

</style>
"""

def script():
    "_"
    return """<script type="text/ecmascript">\n/*<![CDATA[*//*---->*/\n
var sel;

function ajax_get(txt,url, cb) {
  var req = new XMLHttpRequest();
  req.onreadystatechange = processRequest;
  function processRequest () {
    if (req.readyState == 4) {
      if (req.status == 200 || req.status == 0) {
if (cb) {
if (txt) {
cb(req.responseText);
} else {
cb(req.responseXML);
}
}
      } else {
alert('Error Get status:'+ req.status);
      }
    }
  }
  this.doGet = function() {
    req.open('GET', url);
    req.send(null);
  }
};

function submited() {
  var hid = document.documentElement.scrollTop;
  //alert (hid);
}

function charge(evt) {
  var aj = new ajax_get(true, 'cup?log', function(res){
     var ig = evt.target.parentNode.parentNode.parentNode.id.substring(1);   
     //document.location.replace('cup?ig='+ig);
     window.open('cup?ig='+ig);
     //document.location.replace(content.document.location);
  });
  aj.doGet(); 
}

function f(evt) {
if (evt.target.id) {
if (sel) {
  document.getElementById(sel).setAttribute('style','font-weight:normal');
}
var t1 = document.getElementsByName('buy');
var t2 = document.getElementsByName('share');
if (sel == undefined) {
  sel = evt.target.id;
  document.getElementById(sel).setAttribute('style','font-weight:bold');
  for (var i=0; i<t1.length; i++) { 
    t1[i].removeAttribute('disabled'); 
    var v=t1[i].getAttribute('value').replace(/ \S*$/,'');
    t1[i].firstChild.nodeValue='\\'' + v + '\\' buy\\n[' + sel + ']'; t1[i].setAttribute('value', v + ' ' + sel);
  }
  for (var i=0; i<t2.length; i++) { 
    t2[i].removeAttribute('disabled'); 
    var v=t2[i].getAttribute('value').replace(/ \S*$/,'');
    t2[i].firstChild.nodeValue='\\'' + v + '\\' shares\\n[' + sel + ']'; t2[i].setAttribute('value', v + ' ' + sel);
  }
} else {
  for (var i=0;i<t1.length; i++) {t1[i].firstChild.nodeValue='Buy';t1[i].setAttribute('disabled','yes');}
  for (var i=0;i<t2.length; i++) {t2[i].firstChild.nodeValue='Share';t2[i].setAttribute('disabled','yes');}
  sel = undefined;
}
}
}
\n/*--*//*]]>*/</script>
"""

def hashf(s):
    "_"
    return base64.urlsafe_b64encode(hashlib.sha1(s).digest())[:-24].decode('utf-8')

def app_update(host):
    "_"
    here = os.path.dirname(os.path.abspath(__file__))
    # add security here !
    cmd = 'cd %s; ls' % here  if host == 'cup' else 'cd %s/..; rm -rf cup; git clone https://github.com/pelinquin/cup.git' % here 
    out, err = subprocess.Popen((cmd), shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    o = '<html><pre>Application Update...\n'
    o += 'Error:%s\n' % err if err else 'Message:%s\nUpdate OK\n' % out.decode('utf-8')
    o += '</pre><br/><a href="cup">Reload the new version</a></html>'
    return o.encode('utf-8')

def log(s, ip=''):
    "Append log"
    now = '%s' % datetime.datetime.now()
    open('/u/log', 'a', encoding='utf-8').write('%s|%s|%s\n' % (now[:-7], ip, s))

def app_verify(environ, start_response):
    "_"
    A_UBAL, A_AUTH, A_CUST, A_DATE, A_CURR, A_LBAL, A_AAGE, A_CKEY = 0, 1, 2, 3, 4, 5, 6, 7
    IG_PRC, IG_CUST, IG_AUTH, IG_COAU, IG_FILE = 0, 1, 2, 3, 4        
    o, net, dig, tax = '', dbm.open('/u/net'), dbm.open('/u/ig'), dbm.open('/u/tax')
    for ig in dig.keys():
        h = eval(dig[ig])
        #o += 'IG %s\n' % ig
        #o += 'Prices %s %s %s \n' % h[0]
        #o += 'Customers %s \n' % h[1]
        #o += 'Main Author %s \n' % h[2]
        author = h[2]
        #o += 'CoAuthors %s \n' % h[3]
        #o += 'P1:%s inf:%s \n' % (h[4][0], h[4][1])
        #o += 'signature %s \n' % h[4][2]
        signature = h[IG_FILE][2]
        #o += 'date %s \n' % h[4][3]
        #o += 'encrypted content %s \n' % h[IG_FILE][4]
        content = h[IG_FILE][4]
        ag = eval(net[author])
        #o += 'pub key %s\n' % ag[A_CKEY]
        k = [b64toi(x) for x in ag[A_CKEY].split()]
        assert (verify(k[0], k[2], content, signature))  # verif
        cc = decrypt(k[1], k[2], content)  # decrypt
        o += 'Content of %s: %s  \n' % (ig, cc)
    net.close()
    dig.close()
    tax.close()
    start_response('200 OK', [('Content-type', 'text/plain; charset=utf-8')])
    return [o.encode('utf-8')]

def app_read(ig, environ, start_response):
    "_"
    A_UBAL, A_AUTH, A_CUST, A_DATE, A_CURR, A_LBAL, A_AAGE, A_CKEY = 0, 1, 2, 3, 4, 5, 6, 7
    IG_PRC, IG_CUST, IG_AUTH, IG_COAU, IG_FILE = 0, 1, 2, 3, 4        
    net, dig = dbm.open('/u/net'), dbm.open('/u/ig')
    if ig in dig.keys():
        h = eval(dig[ig])
        author = h[2]
        signature = h[IG_FILE][2]
        content = h[IG_FILE][4]
        ag = eval(net[author])
        k = [b64toi(x) for x in ag[A_CKEY].split()]
        assert (verify(k[0], k[2], content, signature))  # verif
        cc = decrypt(k[1], k[2], content)  # decrypt
    net.close()
    dig.close()
    start_response('200 OK', [('Content-type', 'application/pdf')])
    return [cc] 

def application(environ, start_response):
    """ WSGI Web application """
    query, mime, o, fname = urllib.parse.unquote(environ['QUERY_STRING']), 'text/html; charset=utf-8', 'Error!', 'toto'
    log(query, environ['REMOTE_ADDR'])
    if query == 'update':
        start_response('200 OK', [('Content-type', mime), ('Content-Disposition', 'filename={}'.format(fname))])
        return [app_update(environ['SERVER_NAME']) ]
    if query == 'source':
        start_response('200 OK', [('Content-type', 'text/plain; charset=utf-8')])
        return [open(__file__, 'r', encoding='utf-8').read().encode('utf-8')] 
    if query == 'log':
        start_response('200 OK', [('Content-type', 'text/plain; charset=utf-8')])
        return [open('/u/log', 'r', encoding='utf-8').read().encode('utf-8')] 
    if query == 'fben':
        start_response('200 OK', [('Content-type', 'application/pdf'), ('Content-Disposition', 'filename={}'.format('EDLC.pdf'))])
        return [open('/home/pi/Economie_de_la_culture.pdf', 'rb').read()] 
    if query == 'reset':
        subprocess.Popen(('rm', '/u/net.db', '/u/ig.db', '/u/tax.db'),).communicate()
        start_response('200 OK', [('Content-type', 'text/plain; charset=utf-8')])
        return ['RESET DATABASE OK!'.encode('utf-8')]
    if query == 'verify': return app_verify(environ, start_response)
    m = re.match(r'ig=(\w+)', query)
    if m: return app_read(bytes(m.group(1), 'ascii'), environ, start_response)
    o = '<?xml version="1.0" encoding="utf-8"?>\n<html>\n' 
    o += '<link rel="shortcut icon" type="image/png" href="favicon.png"/>\n'
    o += '<link href="http://fonts.googleapis.com/css?family=Schoolbell" rel="stylesheet" type="text/css">\n' 
    o += style() + script() + head()
    agents = {}
    if os.path.isfile('/u/net.db'):
        d = dbm.open('/u/net')
        for x in d.keys(): agents[x] = True;
        d.close()
    if not os.path.isfile('/u/tax.db'):
        dtax = dbm.open('/u/tax', 'c')
        dtax[b'TODAY'] = b'hello'
        for x in __cur_ratio__: dtax[x] = '%s' % [0, 0.00]
        dtax.close()
    d, dig, dtax = dbm.open('/u/net', 'c'), dbm.open('/u/ig', 'c'), dbm.open('/u/tax', 'c')
    raw, cb, fr, newcook = None, None, None, []
    A_UBAL, A_AUTH, A_CUST, A_DATE, A_CURR, A_LBAL, A_AAGE, A_CKEY = 0, 1, 2, 3, 4, 5, 6, 7
    IG_PRC, IG_CUST, IG_AUTH, IG_COAU, IG_FILE = 0, 1, 2, 3, 4        
    #'Agent1' [23.43, {'ig1': 0.01},      {'ig2': 2},            '2013-01-11 16:21:19', 'JPY',   -2658.96,      14, KEY]
    # Name    Ballance  {author hash: %}, {custom hash: nb},     date,                 currency, local balance, Age RSA key] 
    #'ig1'    [(6.57, 6.57, 0),        ['agent2',],  'Agent1',    {'Agent1':10, 'Agent2':1}, (6.57, 11700, 'signature1', 'the date1', 'encrypted content')]
    # IG id   [(price, delta, refund), [custom list], MainAuthor, {co-author: parts},        (p1,   pf,     signature,    date,       encrypt_content
    if environ['REQUEST_METHOD'].lower() == 'post':
        raw = environ['wsgi.input'].read().decode('utf-8')
        fr1 = None 
        m = re.match(r'(fr=on&|)', raw) # fr
        if m:
            fr1 = m.group(1)
        m = re.match(r'(fr=on&|)adda=([^&]{2,16})&age=(\d\d)&cur=(\w{3})(&cb=on|)', raw) # Name + Currency + Ballance + Age + key
        if m:
            fr1, a, age, cur, cb = m.group(1), m.group(2), int(m.group(3)), m.group(4), m.group(4)
            if bytes(a, 'utf-8') not in agents:
                now = '%s' % datetime.datetime.now()
                k = RSA.generate(1024, os.urandom) 
                ckey = bytes(' '.join([itob64(x).decode('ascii') for x in (k.e, k.d, k.n)]), 'ascii')
                d[a] = '%s' % [0, {}, {}, now[:-7], cur, 0, age, ckey]
                vtax = eval (dtax[cur])
                vtax[0] += 1
                dtax[cur] = '%s' % vtax
        m = re.match(r'(fr=on&|)adda=&age=&cur=&(cb=on&|)([^&]{2,16})=(10{0,2})$',raw) # +/-1,10,100
        if m:
            fr1, cb, name, montant = m.group(1), m.group(2), m.group(3), m.group(4)
            v = eval(d[name])
            mont = - int (montant) if cb else int(montant)
            if v[A_UBAL] + mont >= 0:
                c = v[A_CURR]
                v[A_UBAL] += mont
                ra = __cur_ratio__[c][1] if cb else __cur_ratio__[c][3]
                v[A_LBAL] -= mont * ra
                vtax = eval (dtax[c])
                delta = __cur_ratio__[c][1] - __cur_ratio__[c][2] if cb else __cur_ratio__[c][3] - __cur_ratio__[c][2]
                vtax[1] += mont * delta
                dtax[c] = '%s' % vtax
            d[name] = '%s' % v
        m = re.match(r'(fr=on&|)adda=&age=&cur=&(cb=on&|)%40([^&]{2,16})=(New|Nouveau)',raw) # New IG (sell)
        if m:
            fr1, cb, s = m.group(1), m.group(2), m.group(3)
            now = '%s' % datetime.datetime.now()
            g = hashf(now.encode('utf-8'))
            p, f = random.randint(1,1000)/100, random.randint(1,500)*100
            c = gen_pdf_doc(g)
            v = eval(d[s])
            v[A_AUTH][g] = 100
            d[s] = '%s' % v 
            k = [b64toi(x) for x in v[A_CKEY].split()]
            content = encrypt(k[0], k[2], c)
            signature = sign(k[1], k[2], content)
            assert(verify(k[0], k[2], content, signature))
            cc2 = decrypt(k[1], k[2], content)        # check decrypt
            dig[g] = '%s' % [(p,p,0), [], s, {s:10}, (p, f, signature, 'the date1', content)] # 10 parts for initial author
        m = re.match(r'(fr=on&|)adda=&age=&cur=&(cb=on&|)share=([^\+]+)\+([\w\-]{4})$',raw) # share
        if m:
            fr1, cb, s, g = m.group(1), m.group(2), m.group(3), m.group(4)  
            v = eval(dig[g])
            v[IG_COAU][s] = v[IG_COAU].get(s,0) + 1
            sumi = sum(v[IG_COAU][x] for x in v[IG_COAU])
            for x in v[IG_COAU]:
                vnet = eval(d[x])
                vnet[A_AUTH][g] = v[IG_COAU][x]*100/sumi
                d[x] = '%s' % vnet
            dig[g] = '%s' % v 
        m = re.match(r'(fr=on&|)adda=&age=&cur=&(cb=on&|)buy=([^\+]+)\+([\w\-]{4})$',raw) # buy
        if m: 
            fr1, cb, b, g = m.group(1), m.group(2), m.group(3), m.group(4)  
            vb, vig = eval(d[b]), eval(dig[g])
            if vb[A_UBAL] >= vig[IG_PRC][0]:
                for a in vig[IG_CUST]: 
                    va = eval(d[a])
                    va[A_UBAL] += vig[IG_PRC][2]                                         # 1/ refund the other buyers
                    d[a] = '%s' % va
                vb = eval(d[b])
                vb[A_CUST][g] = vb[A_CUST].get(g,0) + 1                                  # 2/ add nb of bought ig to buyer 
                vb[A_UBAL] -= vig[IG_PRC][0]                                             # 3/ buyer pay the price
                d[b] = '%s' % vb
                for s in vig[IG_COAU]: 
                    vs = eval(d[s])
                    vs[A_UBAL] += vig[IG_PRC][1]*vs[A_AUTH][g]/100                       # 4/ all sellers receive payement (income)
                    d[s] = '%s' % vs
                vig[IG_CUST].append(b)                                                   # 5/ add buyer to ig hash
                i, p1, pf = len(vig[IG_CUST]) + 1, vig[IG_FILE][0], vig[IG_FILE][1]      # 6/ get nb, p1, pf
                k, xi = math.log(pf-p1) - math.log(pf-2*p1), .25          
                p = (pf - (pf-p1)*math.exp(-xi*(i-1)*k))/i                   # new price
                dt = (pf-p1)*(math.exp(-xi*(i-2)*k) - math.exp(-xi*(i-1)*k)) # new delta
                vig[IG_PRC] = (p, dt, (p-dt)/(i-1))                                      # 7/ update prices            
                dig[g] = '%s' % vig
        fr = 'on' if fr1 else None
        newcook = [('set-cookie', 'fr=%s' % fr)]
    else:
        fr = 'on' if 'HTTP_COOKIE' in environ and re.search(r'fr=on', environ['HTTP_COOKIE']) else None
    l = 1 if fr else 0
    o += '<form method="post">\n'
    o += '<div class="lang"><label class="toggle candy" lenght="20"><input name="fr" id="fr" type="checkbox"%s/><p><span>fr</span><span>en</span></p><a class="slide-button"></a></label></div>' % (' checked' if fr else '')
    o += '<table class="main">\n'
    o += '<tr><th width="100"><input name="adda" placeholder="Name" title="add new authors\'s name" size="10"/></th>'
    o += '<th width="20"><input name="age" placeholder="Age" title="Age" size="2"/></th>'
    o += '<th width="50"><select name="cur" title="select the official money before creating an agent">'
    o += '<option value="">Cur.</option>' 
    for m in __cur_ratio__:
        o += '<option title="ratio %s/⊔:%s/%s/%s" value="%s">%s %s</option>' % (__cur_ratio__[m][0], __cur_ratio__[m][1], __cur_ratio__[m][2], __cur_ratio__[m][3], m, m, __cur_ratio__[m][0])
    o += '</select></th>'
    o += '<th width="120">'
    disp = ' checked' if cb else ''
    o += '<label title="\'+\': convert money to ⊔ ... \'-\': convert ⊔ to money" style="width: 40px;" class="toggle candy"><input name="cb" id="cb" type="checkbox"%s/><p>%s<span>-</span><span>+</span></p><a class="slide-button"></a></label>' % (disp, loc['bal'][l])
    o += '</th><th rowspan="2">%s</th><th rowspan="2">%s</th></tr>\n' % (loc['cIG'][l], loc['bIG'][l])
    o += '<tr><td colspan="4" class="num"><input type="submit"/></td></tr>\n'
    ia, su, n1, n2 = 0, 0, 0, 0
    for x in d.keys():
        ia += 1
        v = eval(d[x])
        su += v[A_UBAL]
        name = x.decode('utf-8')
        o += '<tr><td title="created %s">%s</td>' % (v[A_DATE], name)
        o += '<td title="years old">%d</td>' % v[A_AAGE]
        o += '<td class="num" title="%s is registered with %s currency">%5.2f%s<br/>%s</td>' % (name, v[A_CURR], v[A_LBAL], __cur_ratio__[v[A_CURR]][0], v[A_CURR])
        o += '<td class="num">%5.2f ⊔<br/><input name="%s" type="submit" title="provision 1⊔ to/from the account" value="1"/><input name="%s" type="submit" title="provision 10⊔ to/from the account" value="10"/><input name="%s" type="submit" title="provision 100⊔ to/from the account" value="100"/></td><td onclick="f(event);"><input name="@%s" type="submit" value="%s"/><button name="share" type="submit" value="%s" disabled="yes">%s</button><br/>' % (v[A_UBAL], name, name, name,  name, loc['new'][l], name, loc['sha'][l])  
        sv = sorted(v[A_AUTH].keys())
        for g in sv:
            n1 += 1
            vig = eval(dig[g])
            per, pc, pf, np = v[A_AUTH][g], vig[IG_PRC][0], vig[IG_FILE][1], vig[IG_COAU][name]
            o += ' <a><table class="ig" title="%5.2f %% (%s parts)"><tr><td id="%s" class="ig">%s</td></tr><tr><td class="small">%5.2f⊔%2.0f</td></tr></table></a>' % (per, np, g, g, pc, pf) 
        o += '<fh6>%d</fh6></td>' % len(sv)
        o += '<td><button name="buy" type="submit" value="%s" disabled="yes"/>%s</button><br/>' % (name, loc['buy'][l])
        sv = sorted(v[A_CUST].keys())
        for g in sv:
            n2 += 1
            vig = eval(dig[g])
            lis = ''
            for a in vig[IG_COAU]:
                lis += '%s:%s ' % (a, vig[IG_COAU][a])
            o += ' <a><table id="+%s" onclick="charge(event);" class="ig" title=""><tr><td class="ig">%s<p2 class="small">(%d)</p2></td></tr><tr><td class="small">%s</td></tr></table></a>' % (g, g, v[A_CUST][g], lis) 
        o += '<fh6>%d</fh6></td></tr>\n' % len(sv)
    o += '<tr><td colspan="3"><i>Total (%d)<i></td><td class="num">%5.2f ⊔</td><td>%d IGs</td><td>%d IGs</td></tr>' %(ia, su, n1, n2)
    o += '</table></form>'
    o += '<table class="main" width="50%%"><tr><th width="50" colspan="2">%s</th><th>%s</th><th width="30">&lt;-%%-&gt;</th><th>%s</th><th width="30">&lt;-%%-&gt;</th><th>%s</th><th>%s</th><th>%s</th></tr>' % (loc['cur'][l], loc['bra'][l], loc['nra'][l], loc['sra'][l], loc['nbc'][l], loc['tgt'][l])
    for c in __cur_ratio__:
        vtax = eval (dtax[c])
        deltab = 100*(__cur_ratio__[c][2] - __cur_ratio__[c][1])/__cur_ratio__[c][2]
        deltas = 100*(__cur_ratio__[c][3] - __cur_ratio__[c][2])/__cur_ratio__[c][2]
        o += '<tr><td width="30">%s</td><td width="10" class="num">%s</td><td class="num">%5.3f</td><td class="num">%5.2f%%</td><td class="num">%5.3f</td><td class="num">%5.2f%%</td><td class="num">%5.3f</td><td class="num">%05d</td><td class="num"><b>%7.2f %s</b></td><tr>' % (c, __cur_ratio__[c][0], __cur_ratio__[c][1], deltab, __cur_ratio__[c][2], deltas, __cur_ratio__[c][3], vtax[0], vtax[1], __cur_ratio__[c][0]) 
    o += '</table>'
    d.close()
    dig.close()
    dtax.close()
    #if raw: o += "<pre>%s</pre>" % raw
    #o += "<pre>%s</pre>" % query
    o += test_cup_ratios() 
    o += foot(fr) + '</html>'
    start_response('200 OK', [('Content-type', mime), ('Content-Disposition', 'filename={}'.format(fname))] + newcook)
    return [o.encode('utf-8')] 

def head():
    "_"
    return """\n<title>The ⊔Foundation</title>
<h1 title="the 'cup' Foundation"><a href="http://www.cupfoundation.net/">⊔<n1>Simulation</n1></a></h1>
<div class="logo"><svg xmlns="http://www.w3.org/2000/svg" width="70"><path stroke-width="0" fill="Dodgerblue" stroke="none" d="M10,10L10,10L10,70L70,70L70,10L60,10L60,60L20,60L20,10z"/></svg></div>\n"""

def foot(fr):
    "_"
    if fr:
        o = """\n<p><p1>Aide :</p1> Pour ajouter un agent, choisir un nom inconnu, donnez un age et une monnaie courante. Créer au moins deux ou trois<br/>
Positionnez l'interrupteur sur '+', puis provisionner alors des ⊔ en utilisant les boutons '1', '10' ou '100' afin que l'agent courant puisse acheter des IGs (Bien Immatériel). Créer pour un agent (artiste) plusieurs IGs en utilisant le bouton 'New'. Les prix sont fixés aléatoirement. Pour simuler le partage de la création d'un IG, sélectionner un IG et choisir un bouton "share" d'un agent pour lui ajouter une part (l'auteur initial a 10 parts). Pour simuler une vente, sélectionner un IG créé et pressez alors un bouton d'un acheteur potentiel de cet IG. Pour simuler un mécénat, acheter par le même agent plusieurs fois le même bien. Tout artiste peut convertir ses ⊔ en argent local en positionnant l'interrupteur sur '-'. Vérifier que la somme totale en ⊔ n'a pas changé lors de l'achat d'un IG. Vérifier aussi que le revenu de l'auteur est croissant et qu'il y a remboursement des précédents acheteurs. Remarquer que pour un artiste achetant ses propres créations, son solde ne change pas, seulement le prix courant décroit.</p>"""
    else:
        o = """\n<p><p1>Help:</p1> To add an agent, type a name not already choosen, create two or three agents at least. Set switch to '+', then then provision some ⊔ using the '1','10' or '100' buttons so the current agent can buy some IGs (Intangible Good). Create for an agent (artist) several IGs using the 'New' button, prices are randomly setted and visible as tooltip. Select one created IG, then push one button of a selected buyer for that IG. To simulate sponsorship, make the same agent buy several times the same good. Any artist can convert its ⊔ to local money by switching to '-' position. Check that the total ⊔ sum does not change when buying an IG. You can check both the increasing author's income and the refunding of previous buyers. Note that for an artist buying its own IGs does not change her balance, but only decrease the current price.</p>"""
    o += """\n<p>! This simulation is hosted on a tiny <a href="http://pi.pelinquin.fr/u?pi">RaspberryPi</a> with a low bandwidth personnal box, see <a href="cup?source">Source code</a> and <a href="cup?log">Log file</a>.
<h6>Digest: %s<br/>
Contact: <mail>laurent.fournier@cupfoundation.net</mail><br/>
⊔FOUNDATION is currently registered in Toulouse/France  SIREN: 399 661 602 00025<br/></h6>\n""" % __digest__.decode('utf-8')
    return o

def gen_pdf_doc(ig='sample'):
    r"""\documentclass{beamer}
\usepackage{tikz}
\usepackage{wasysym}
\usepackage[utf8]{inputenc}
\usepackage{marvosym}
\usepackage{beamerthemeshadow}
\usepackage{graphicx}
\title[\texttt{WLgLr}]{This is the title for %s}
\subtitle{$\sqcup \underline{net}$ }
\author{Laurent Fournier\inst{*}}\institute{*laurent.fournier@cupfoundation.net}
\begin{document}
\usetikzlibrary{shapes,fit,arrows,shadows,backgrounds,svg.path}
\begin{frame}[fragile]
\titlepage
\begin{tikzpicture}[remember picture,overlay,shift={(current page.north west)}] 
\draw[draw=none,fill=blue,scale=1,shift={(.6,-1)}] svg "M0,0L0,18L4,18L4,4L14,4L14,18L18,18L18,0Z";
\end{tikzpicture}
\end{frame}
\end{document}"""
    o = gen_pdf_doc.__doc__ % ig
    open('/tmp/%s.tex' % ig, 'w').write(o)
    subprocess.call(('pdflatex','-interaction=batchmode', '-output-directory', '/tmp', '%s.tex' % ig, '1>/dev/null'))
    return open('/tmp/%s.pdf' % ig, 'rb').read()

class cup:
    xi = .25
    def __init__(self, pop):
        self.net = {a:[pop[a],{},{}] for a in pop}
        self.ig = {}

    def buy(self, b, g):
        assert b in self.net
        if self.net[b][0] > self.ig[g][0][0]:                                                # 0/ if balance buyer > ig price 
            for a in self.ig[g][1]: self.net[a][0] += self.ig[g][0][2]                       # 1/ refund all other buyers
            self.net[b][2][g] = self.net[b][2].get(g,0) + 1                                  # 2/ add nb of bought to buyer
            self.net[b][0] -= self.ig[g][0][0]                                               # 3/ buyer pay the price
            for s in self.ig[g][2]: self.net[s][0] += self.ig[g][0][1]*self.net[s][1][g]/100 # 4/ income for all authors 
            self.ig[g][1].append(b)                                                          # 5/ add buyer to ig hash
            i, p1, pf = len(self.ig[g][1]) + 1, self.ig[g][3][0], self.ig[g][3][1]           # 6/ get nb, p1, pf
            k = math.log(pf-p1) - math.log(pf-2*p1)
            p = (pf - (pf-p1)*math.exp(-self.xi*(i-1)*k))/i                                  # new price 
            d = (pf-p1)*(math.exp(-self.xi*(i-2)*k) - math.exp(-self.xi*(i-1)*k))            # new delta
            self.ig[g][0] = (p, d, (p-d)/(i-1))                                              # 7/ updates prices
        else:
            print ('Transaction refused! (negative balance)')

    def sell(self, s, g, p, f, c):
        assert s in self.net and p < f and p >= 0
        self.net[s][1][g] = 100
        self.ig[g] = [(p,p,0), [], {s:10}, (p, f, 'signature1', 'the date1', c)] # 10 parts for initial author

    def share(self, s, g, n=1):
        assert s in self.net
        self.ig[g][2][s] = self.ig[g][2].get(s,0) + n
        sumi = sum(self.ig[g][2][x] for x in self.ig[g][2])
        for x in self.ig[g][2]: self.net[x][1][g] = self.ig[g][2][x]*100/sumi

    def display(self):
        print ('AGENTS:', self.net, '\nIG:', self.ig, '\nTotal ammount:', sum(self.net[a][0] for a in self.net))

    def display1(self):
        print ('BALLANCE:', sum(self.net[a][0] for a in self.net))
        for a in self.net:
            print ('AGENT:', a, self.net[a])
        for g in self.ig:
            print ('IG:', g, self.ig[g])

def itob64(n):
    " utility to transform int to base64"
    c = hex(n)[2:]
    if len(c)%2: c = '0'+c
    return re.sub(b'=*$', b'', base64.b64encode(bytes.fromhex(c)))

def b64toi(c):
    "transform base64 to int"
    if c == '': return 0
    return int.from_bytes(base64.b64decode(c + b'='*((4-(len(c)%4))%4)), 'big')

def num(c):
    return (4-(len(c)%4)%4)

def H(*tab):
    return int(hashlib.sha1(b''.join(bytes('%s' % i, 'ascii') for i in tab)).hexdigest(), 16)
 
def crand(n=1024):  
    return random.SystemRandom().getrandbits(n)

def encrypt(e, n, msg):
    skey = os.urandom(16)
    iskey = int(binascii.hexlify(skey),16)
    aes = AES.new(skey, AES.MODE_ECB)
    c, r = itob64(pow(iskey, e, n)), len(msg)
    raw = bytes(((r)&0xff, (r>>8)&0xff, (r>>16)&0xff, (r>>24)&0xff, (len(c))&0xff))
    return raw + c + aes.encrypt(msg+b'\0'*(16-len(msg)%16))

def decrypt(d, n, raw):
    lmsg, l2 = raw[0]+(raw[1]<<8)+(raw[2]<<16)+(raw[3]<<24), raw[4]
    print (lmsg,l2)
    ckey, cmsg = raw[5:l2+5], raw[l2+5:]
    c = hex(pow(b64toi(ckey), d, n))[2:]
    if len(c)%2: c = '0'+c
    #open('/u/zorro', 'a', encoding='utf-8').write('%s %d\n' % (c,len(c)))
    #print('%s %d\n' % (c,len(c)))
    aes2 = AES.new(bytes.fromhex(c), AES.MODE_ECB)
    return aes2.decrypt(cmsg)[:lmsg]

def sign(d, n, msg):
    return itob64(pow(H(msg), d, n))

def verify(e, n, msg, s):
    return (pow(b64toi(s), e, n) == H(msg)) 

if __name__ == '__main__':
    u = cup({'agent1':90, 'agent2':200, 'agent3':300, 'agent4':10})
    for a in ('agent1', 'agent2'):
        for g in ('g1', 'g2', 'g3'): u.sell (a, '%s_%s' % (g,a), 1, 1000, 'content %s %s' % (g, a))
    u.share('agent2', 'g1_agent1')
    u.share('agent1', 'g1_agent1')
    for b in ('agent2', 'agent3', 'agent1', 'agent2', 'agent4'): u.buy(b, 'g1_agent1')
    u.share('agent1', 'g1_agent1', 10)
    #u.display1()

    u = cup({'agent1':90, 'agent2':120, 'agent3':100})
    u.sell ('agent1', 'ig1', 1, 1000, 'content_ig1')
    u.share('agent2', 'ig1', 10)
    u.buy('agent3', 'ig1')
    u.buy('agent3', 'ig1')
    #u.display1()
 
    if True:
        for b in ('/u/net', '/u/ig', '/u/tax'):
            print (b)
            d = dbm.open(b)
            for x in d.keys():
                print (x, '->', d[x])
            d.close()

    # TEST SIMPLE CRYPTO
    for x in range(100):
        k = RSA.generate(1024, os.urandom)
        msg = b"""this is a long message kdhsdkhjksdhkdshdGJGHGJHGJGJHGJGJhksdjksdhdsfdffddfdfdf COUCOU dssdsdlkjdskljsdsds"""
        msg = b'This is a long content!'
        s = sign(k.d, k.n, msg)           # sign
        assert (verify(k.e, k.n, msg, s)) # verif
        aa = encrypt(k.e, k.n, msg)       # encrypt
        cc = decrypt(k.d, k.n, aa)        # decrypt
        print (cc)

    #utility()

# End ⊔net!
