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

import sys, re, os, math, random, urllib.parse, dbm, datetime, base64, hashlib, subprocess, shutil
__digest__ = base64.urlsafe_b64encode(hashlib.sha1(open(__file__, 'r', encoding='utf-8').read().encode('utf-8')).digest())[:5]

# constants defined by government banking authorities and should be very stable
__cur_ratio__ = {'EUR':['€',0.731,0.820,0.923], 
                 'USD':['$',0.998,1.064,1.107], 
                 'GBP':['£',0.651,0.664,0.702], 
                 'JPY':['¥',85.204,87.740,88.632], 
                 'CNY':['Ұ',6.405,6.634,6.703],
                 }

def style():
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
table {border: 1px solid #666;width:100%;border-collapse:collapse;} 
td,th {border: 1px solid #666;padding:2pt;}
td.in:active {background-color:red;}

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
    return """<script type="text/ecmascript">\n/*<![CDATA[*//*---->*/\n
var sel;


function submited() {
  var hid = document.documentElement.scrollTop;
  //alert (hid);
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
    t1[i].firstChild.nodeValue='\\'' + v + '\\' buy\\n(' + sel + ')'; t1[i].setAttribute('value', v + ' ' + sel);
  }
  for (var i=0; i<t2.length; i++) { 
    t2[i].removeAttribute('disabled'); 
    var v=t2[i].getAttribute('value').replace(/ \S*$/,'');
    t2[i].firstChild.nodeValue='\\'' + v + '\\' shares\\n(' + sel + ')'; t2[i].setAttribute('value', v + ' ' + sel);
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
    here = os.path.dirname(os.path.abspath(__file__))
    # add security
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
    if query == 'benhamou':
        start_response('200 OK', [('Content-type', 'application/pdf'), ('Content-Disposition', 'filename={}'.format('EDLC.pdf'))])
        return [open('/home/pi/Economie_de_la_culture.pdf', 'rb').read()] 
    if query == 'reset':
        subprocess.Popen(('rm', '/u/net.db', '/u/ig.db', '/u/tax.db'),).communicate()
        start_response('200 OK', [('Content-type', 'text/plain; charset=utf-8')])
        return ['RESET DATABASE OK!'.encode('utf-8')]
    o = '<?xml version="1.0" encoding="utf-8"?>\n<html>\n' 
    o += '<link rel="shortcut icon" type="image/png" href="favicon.png"/>\n'
    o += '<link href="http://fonts.googleapis.com/css?family=Schoolbell" rel="stylesheet" type="text/css">\n' 
    o += style() + script() + head()
    hg, agents = {}, {}
    if os.path.isfile('/u/net.db'):
        d = dbm.open('/u/net')
        for x in d.keys():
            agents[x] = True;
            v = eval(d[x])
            for g in v[1]:
                hg[g] = x
        d.close()
    if not os.path.isfile('/u/tax.db'):
        dtax = dbm.open('/u/tax', 'c')
        for x in __cur_ratio__: dtax[x] = '%s' % [0, 0.00]
        dtax.close()
    d, dig, dtax = dbm.open('/u/net', 'c'), dbm.open('/u/ig', 'c'), dbm.open('/u/tax', 'c')
    raw, cb, fr = None, None, None
    if environ['REQUEST_METHOD'].lower() == 'post':
        raw = environ['wsgi.input'].read().decode('utf-8')
        m = re.match(r'(fr=on&|)adda=([^&]{2,16})&cur=(\w{3})(&cb=on|)', raw) # Name
        if m:
            fr, a, cur, cb = m.group(1), m.group(2), m.group(3), m.group(4)
            if bytes(a, 'utf-8') not in agents:
                now = '%s' % datetime.datetime.now()
                d[a] = '%s' % [0, {}, {}, now[:-7], cur, 0]
                vtax = eval (dtax[cur])
                vtax[0] += 1
                dtax[cur] = '%s' % vtax
        m = re.match(r'(fr=on&|)adda=&cur=\w{3}&(cb=on&|)([^&]{2,16})=(10{0,2})$',raw) # +/-1,10,100
        if m:
            fr, cb, name, montant = m.group(1), m.group(2), m.group(3), m.group(4)
            v = eval(d[name])
            mont = - int (montant) if cb else int(montant)
            if v[0] + mont >= 0:
                c = v[4]
                v[0] += mont
                ra = __cur_ratio__[c][1] if cb else __cur_ratio__[c][3]
                v[5] -= mont * ra
                vtax = eval (dtax[c])
                delta = __cur_ratio__[c][1] - __cur_ratio__[c][2] if cb else __cur_ratio__[c][3] - __cur_ratio__[c][2]
                vtax[1] += mont * delta
                dtax[c] = '%s' % vtax
            d[name] = '%s' % v
        m = re.match(r'(fr=on&|)adda=&cur=\w{3}&(cb=on&|)%40([^&]{2,16})=New$',raw) # New IG (sell)
        if m:
            fr, cb, s = m.group(1), m.group(2), m.group(3)
            now = '%s' % datetime.datetime.now()
            g = hashf(now.encode('utf-8'))
            p, f, c = random.randint(1,1000)/100, random.randint(1,500)*100, 'content'
            v = eval(d[s])
            v[1][g] = 100
            d[s] = '%s' % v 
            dig[g] = '%s' % [(p,p,0), [], {s:10}, (p, f, 'signature1', 'the date1', c)] # 10 parts for initial author
        m = re.match(r'(fr=on&|)adda=&cur=\w{3}&(cb=on&|)share=([^\+]+)\+([\w\-]{4})$',raw) # share
        if m:
            fr, cb, s, g = m.group(1), m.group(2), m.group(3), m.group(4)  
            v = eval(dig[g])
            v[2][s] = v[2].get(s,0) + 1
            sumi = sum(v[2][x] for x in v[2])
            for x in v[2]:
                vnet = eval(d[x])
                vnet[1][g] = v[2][x]*100/sumi
                d[x] = '%s' % vnet
            dig[g] = '%s' % v 
        #'Agent1' [23.43, {'ig1': 0.01},      {'ig2': 2},            '2013-01-11 16:21:19', 'JPY',   -2658.96]
        # Name    Ballance  {author hash: %}, {custom hash: nb},     date,                 currency, local balance] 
        #'ig1'    [(6.57, 6.57, 0),        ['agent2',],   {'Agent1': 10, 'Agent2': 1}, (6.57, 11700, 'signature1', 'the date1', 'content')]
        # IG id   [(price, delta, refund), [custom list], {co-author parts},             (p1,   pf,     signature,    date,       content
        m = re.match(r'(fr=on&|)adda=&cur=\w{3}&(cb=on&|)buy=([^\+]+)\+([\w\-]{4})$',raw) # buy
        if m: 
            fr, cb, b, g = m.group(1), m.group(2), m.group(3), m.group(4)  
            s = hg[g]
            vb, vs, vig = eval(d[b]), eval(d[s]), eval(dig[g])
            if vb[0] >= vig[0][0]:
                #for a in self.ig[g][1]: self.net[a][0] += self.ig[g][0][2]                       # 1/ refund all other buyers
                #self.net[b][2][g] = self.net[b][2].get(g,0) + 1                                  # 2/ add nb of bought to buyer
                #self.net[b][0] -= self.ig[g][0][0]                                               # 3/ buyer pay the price
                #for s in self.ig[g][2]: self.net[s][0] += self.ig[g][0][1]*self.net[s][1][g]/100 # 4/ income for all authors 
                #self.ig[g][1].append(b)                                                          # 5/ add buyer to ig hash
                #i, p1, pf = len(self.ig[g][1]) + 1, self.ig[g][3][0], self.ig[g][3][1]           # 6/ get nb, p1, pf
                #k = math.log(pf-p1) - math.log(pf-2*p1)
                #p = (pf - (pf-p1)*math.exp(-self.xi*(i-1)*k))/i                                  # new price 
                #d = (pf-p1)*(math.exp(-self.xi*(i-2)*k) - math.exp(-self.xi*(i-1)*k))            # new delta
                #self.ig[g][0] = (p, d, (p-d)/(i-1))                                              # 7/ updates prices
                for a in vig[1]: 
                    va = eval(d[a])
                    va[0] += vig[0][2]                                              # 1/ refund the other buyers
                    d[a] = '%s' % va
                vb[2][g] = vb[2].get(g,0) + 1                                       # 2/ add nb of bought ig to buyer 
                vb = eval(d[b])
                vb[2][g] = s
                vb[0] -= vig[0][0]                                                  # 3/ buyer pay the price
                d[b] = '%s' % vb
                for s in vig[2]: 
                    vs = eval(d[s])
                    vs[0] += vig[0][1]*vs[1][g]/100                                 # 4/ all sellers receive payement (income)
                    d[s] = '%s' % vs
                vig[1].append(b)                                                    # 5/ add buyer to ig hash
                i, p1, pf = len(vig[1]) + 1, vig[3][0], vig[3][1]                   # 6/ get nb, p1, pf
                k, xi = math.log(pf-p1) - math.log(pf-2*p1), .25          
                p = (pf - (pf-p1)*math.exp(-xi*(i-1)*k))/i                          # new price
                dt = (pf-p1)*(math.exp(-xi*(i-2)*k) - math.exp(-xi*(i-1)*k))        # new delta
                vig[0] = (p, dt, (p-dt)/(i-1))                                      # 7/ update prices            
                d[s], dig[g] = '%s' % vs, '%s' % vig
        if False:
            s = hg[g]
            vb, vs = eval(d[b]), eval(d[s])
            if vb[0] >= vs[1][g][0][0]:
                for a in vs[1][g][1]:
                    va = eval(d[a])
                    va[0] += vs[1][g][0][2] # refund
                    d[a] = '%s' % va
                vb = eval(d[b])
                vb[2][g] = s
                vb[0] -= vs[1][g][0][0] # buyer price
                d[b] = '%s' % vb
                vs = eval(d[s])
                vs[0] += vs[1][g][0][1] # seller income
                vs[1][g][1].append(b) # add buyer
                i = len(vs[1][g][1]) + 1
                p1 = vs[1][g][2][0]
                pf = vs[1][g][2][1]
                k, xi = math.log(pf-p1) - math.log(pf-2*p1), .25
                p = (pf - (pf-p1)*math.exp(-xi*(i-1)*k))/i
                dt = (pf-p1)*(math.exp(-xi*(i-2)*k) - math.exp(-xi*(i-1)*k))
                vs[1][g][0] = (p, dt, (p-dt)/(i-1))
    o += '<form method="post" onsubmit="submited();"><table>\n'
    disp = ' checked' if fr else ''
    #o += '<div class="lang"><label class="toggle candy" lenght="20"><input name="fr" id="fr" type="checkbox"%s/><p><span>en</span><span>fr</span></p><a class="slide-button"></a></label></div>' % disp
    o += '<tr><th width="100"><input name="adda" placeholder="Name" title="add new authors\'s name" size="10"/></th>'
    o += '<th width="50"><select name="cur" title="select the official money before creating an agent">'
    for m in __cur_ratio__:
        o += '<option title="ratio %s/⊔:%s/%s/%s">%s</option>' % (__cur_ratio__[m][0], __cur_ratio__[m][1], __cur_ratio__[m][2], __cur_ratio__[m][3], m)
    o += '</select></th>'
    o += '<th width="120">'
    disp = ' checked' if cb else ''
    o += '<label title="\'+\': convert money to ⊔ ... \'-\': convert ⊔ to money" style="width: 40px;" class="toggle candy"><input name="cb" id="cb" type="checkbox"%s/><p>Balance<span>-</span><span>+</span></p><a class="slide-button"></a></label>' % disp
    o += '</th><th>Created IGs</th><th>Bought IGs</th></tr>\n'
    i, s, n1, n2 = 0, 0, 0, 0
    for x in d.keys():
        i += 1
        v = eval(d[x])
        s += v[0]
        name = x.decode('utf-8')
        o += '<tr><td title="created %s">%s</td>' % (v[3], name)
        o += '<td class="num" title="%s is registered with %s currency">%5.2f%s<br/>%s</td>' % (name, v[4], v[5], __cur_ratio__[v[4]][0], v[4])
        o += '<td class="num">%5.2f ⊔<br/><input name="%s" type="submit" title="provision 1⊔ to/from the account" value="1"/><input name="%s" type="submit" title="provision 10⊔ to/from the account" value="10"/><input name="%s" type="submit" title="provision 100⊔ to/from the account" value="100"/></td><td onclick="f(event);"><input name="@%s" type="submit" value="New"/><button name="share" type="submit" value="%s" disabled="yes">Share</button><br/>' % (v[0], name, name, name,  name, name)  
        sv = sorted(v[1].keys())
        for g in sv:
            n1 += 1
            vig = eval(dig[g])
            per, pc, pf = v[1][g], vig[0][0], vig[3][1]
            o += ' <a id="%s" title="%5.2f⊔%2.0f (%5.2f %%)">(%s)</a>' % (g, pc, pf, per, g)
        o += '<fh6>%d</fh6></td>' % len(sv)
        o += '<td><button name="buy" type="submit" value="%s" disabled="yes"/>Buy</button><br/>' % name
        sv = sorted(v[2].keys())
        for g in sv:
            n2 += 1
            se = hg[g].decode('utf-8')
            o += ' <a title="Author:%s">(%s)</a>' % (se, g)
        o += '<fh6>%d</fh6></td></tr>\n' % len(sv)
    o += '<tr><td><i>Total (%d)<i></td><td> </td><td class="num">%5.2f ⊔</td><td>%d IGs</td><td>%d IGs</td></tr>' %(i, s, n1, n2)
    o += '</table><form>'
    o += '<table width="50%"><tr><th width="50">Currency</th><th width="10"> </th><th>Buy Ratio</th><th>Nominal Ratio</th><th>Sale Ratio</th><th>Nb of citizens</th><th>Total Government Tax</th></tr>'
    for c in __cur_ratio__:
        vtax = eval (dtax[c])
        o += '<tr><td>%s</td><td>%s</td><td class="num">%5.3f</td><td class="num">%5.3f</td><td class="num">%5.3f</td><td class="num">%05d</td><td class="num"><b>%7.2f %s</b></td><tr>' % (c, __cur_ratio__[c][0], __cur_ratio__[c][1], __cur_ratio__[c][2], __cur_ratio__[c][3], vtax[0], vtax[1], __cur_ratio__[c][0]) 
    o += '</table>'
    d.close()
    dig.close()
    dtax.close()
    #if raw: o += "<pre>%s</pre>" % raw
    #o += "<pre>%s</pre>" % query
    o += foot() + '</html>'
    start_response('200 OK', [('Content-type', mime), ('Content-Disposition', 'filename={}'.format(fname))])
    return [o.encode('utf-8')] 

def head():
    return """\n<title>The ⊔Foundation</title>
<h1 title="the 'cup' Foundation"><a href="http://www.cupfoundation.net/">⊔<n1>Simulation</n1></a></h1>
<div class="logo"><svg xmlns="http://www.w3.org/2000/svg" width="70"><path stroke-width="0" fill="Dodgerblue" stroke="none" d="M10,10L10,10L10,70L70,70L70,10L60,10L60,60L20,60L20,10z"/></svg></div>\n"""

def foot():
    return """\n<br/><table><tr><td><p1>Help</p1></td><td><p1>Aide</p1></td></td>
<tr><td><p>To add an agent, type a name not already choosen, create two or three agents at least<br/>
Set switch to '+', then then provision some ⊔ using the '1','10' or '100' buttons so the current agent can buy some IGs (Intangible Good)<br/>
Create for an agent (artist) several IGs using the 'New' button,<br/> 
prices are randomly setted and visible as tooltip.<br/>
Select one created IG, then push one button of a selected buyer for that IG<br/>
To simulate sponsorship, make the same agent buy several times the same good<br/>
Any artist can convert its ⊔ to local money by switching to '-' position.<br/>
Check that the total ⊔ sum does not change when buying an IG<br/>
You can check both the increasing author's income and the refunding of previous buyers<br/>
Note that for an artist buying its own IGs does not change her balance, but only decrease the current price.</p></td>
<td><p>Pour ajouter un agent, tapez un nom qui n'est pas déjà été choisi, créer deux ou trois agents au moins<br/>
Positionnez l'interrupteur sur '+', puis provisionner alors des ⊔ en utilisant les boutons '1', '10' ou '100' afin que l'agent courant puisse acheter des IGs (Bien Immatériel)<br/>
Créer pour un agent (artiste) plusieurs IGs en utilisant le bouton 'New',<br/> 
Les prix sont fixés aléatoirement et visible dans les bulles.<br/>
Sélectionnez un IG créé et pressez alors un bouton d'un acheteur potentiel de cet IG<br/>
Pour simuler un mécénat, faites acheter par le même agent plusieurs fois le même bien<br/>
Tout artiste peut convertir ses ⊔ en argent local en positionnant l'interrupteur sur '-'.<br/>
Vérifier que la somme totale en ⊔ n'a pas changé lors de l'achat d'un IG<br/>
Vous pouvez vérifier que le revenu de l'auteur est croissant et aussi le remboursement des précédents acheteurs<br/>
Remarquez que pour un artiste achetant ses propres créations, son solde ne change pas, seulement le prix courant décroit.</p></td>
</tr></table>
<p>! This simulation is hosted on a tiny <a href="http://pi.pelinquin.fr/u?pi">RaspberryPi</a> with a low bandwidth personnal box. see <a href="cup?source">Source code</a>.
<h6>Digest: %s<br/>
Contact: <mail>laurent.fournier@cupfoundation.net</mail><br/>
⊔FOUNDATION is currently registered in Toulouse/France  SIREN: 399 661 602 00025<br/></h6>\n""" % __digest__.decode('utf-8')

class cup_old:
    xi = .25
    def __init__(self, pop):
        self.net = {a:[pop[a],{},{}] for a in pop}

    def update(self, s, g):
        i = len(self.net[s][1][g][1]) + 1
        p1 = self.net[s][1][g][2][0]
        pf = self.net[s][1][g][2][1]
        k = math.log(pf-p1) - math.log(pf-2*p1)
        p = (pf - (pf-p1)*math.exp(-self.xi*(i-1)*k))/i 
        d = (pf-p1)*(math.exp(-self.xi*(i-2)*k) - math.exp(-self.xi*(i-1)*k))
        self.net[s][1][g][0] = (p, d, (p-d)/(i-1))

    def buy(self, b, s, g):
        assert b in self.net and s in self.net and g in self.net[s][1]
        if self.net[b][0] > self.net[s][1][g][0][0]:
            for a in self.net[s][1][g][1]: self.net[a][0] += self.net[s][1][g][0][2] # refund
            self.net[b][2][g] = s
            self.net[b][0] -= self.net[s][1][g][0][0] # buyer price
            self.net[s][0] += self.net[s][1][g][0][1] # seller income 
            self.net[s][1][g][1].append(b) # add buyer
            self.update(s, g)
        else:
            print ('Transaction refused! (negative balance)')

    def sell(self, s, g, p, f, c):
        assert s in self.net and p < f and p >= 0
        self.net[s][1][g] = [(p,p,0), [], (p, f, 'signature1', 'the date1', c)]

    def display(self):
        print (self.net, '\nTotal ammount:', sum(self.net[a][0] for a in self.net))

class cup:
    xi = .25
    def __init__(self, pop):
        self.net = {a:[pop[a],{},{}] for a in pop}
        self.ig = {}

    #'Agent1' [23.43, {'ig1': 0.0999}, {'ig2': 2}, '2013-01-11 16:21:19', 'JPY',   -2658.96]
    # Name    Ballance  {author hash}, {custom hash},     date,                 currency, local balance 
    #'ig1'    [(6.57, 6.57, 0),        ['ig2','ig3'], {'Agent1': 10, 'Agent2': 1}, (6.57, 11700, 'signature1', 'the date1', 'content')]
    # Id      [(price, delta, refund), [ig list    ], {co-author parts},             (p1,   pf,     signature,    date,        content) ]
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
    u.display1() 
    
    d = dbm.open('/u/net')
    for x in d.keys():
        print (x, d[x])
    d.close()
    print ('IG')
    d = dbm.open('/u/ig')
    for x in d.keys():
        print (x, d[x])
    d.close()
    
    #d = dbm.open('/u/tax')
    #for x in d.keys():
    #    print (x, d[x])
    #d.close()
    

# End ⊔net!
