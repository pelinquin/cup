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

import re, os, sys, math, urllib.parse, hashlib, http.client, base64, dbm, binascii, datetime, zlib, functools, subprocess, time

__digest__ = base64.urlsafe_b64encode(hashlib.sha1(open(__file__, 'r', encoding='utf8').read().encode('utf8')).digest())[:5]
__app__    = os.path.basename(__file__)[:-3]
__email__  = 'laurent.fournier@cupfoundation.net'
__url__    = 'http://cupfoundation.net'
_XHTMLNS   = 'xmlns="http://www.w3.org/1999/xhtml"'
_SVGNS     = 'xmlns="http://www.w3.org/2000/svg"'
_XLINKNS   = 'xmlns:xlink="http://www.w3.org/1999/xlink"'

def reg(value):
    " function attribute is a way to access matching group in one line test "
    reg.v = value
    return value

def init_db(db):
    "_"
    di = '/cup/%s' % __app__
    if not os.path.exists(di):
        os.makedirs(di)
    if not os.path.isfile(db):
        d = dbm.open(db[:-3], 'c')
        d.close()
        os.chmod(db, 511)

def log(s, ip=''):
    "Append to head log file"
    logf, now = '/cup/%s/log' % __app__, '%s' % datetime.datetime.now()
    if not os.path.isfile(logf): open(logf, 'w', encoding='utf8').write('%s|%s Log file Creation\n' % (now[:-7], ip) )     
    cont = open(logf, 'r', encoding='utf8').read()
    open(logf, 'w', encoding='utf8').write('%s|%s|%s\n%s' % (now[:-7], ip, s, cont))

def application(environ, start_response):
    "wsgi server app"
    mime, o, db, today, fname = 'text/plain; charset=utf8', 'Error:', '/cup/%s/keys.db' % __app__, '%s' % datetime.datetime.now(), 'default.txt'
    init_db(db)
    if environ['REQUEST_METHOD'].lower() == 'post':
        raw, way = environ['wsgi.input'].read(), 'post'        
    else:
        raw, way = urllib.parse.unquote(environ['QUERY_STRING']), 'get'
    d = dbm.open(db[:-3], 'c')
    if way == 'post':
        o += 'something wrong in the input text! %s' % urllib.parse.unquote_plus(raw.decode('utf8'))
    else:
        log(raw, environ['REMOTE_ADDR'])
        if raw.lower() in ('log',):
            o = open('/cup/%s/log' % __app__, 'r', encoding='utf8').read()                
        else:
            o, mime = frontpage(), 'application/xhtml+xml; charset=utf8'
    d.close()
    start_response('200 OK', [('Content-type', mime), ('Content-Disposition', 'filename={}'.format(fname))])
    return [o if mime == 'application/pdf' else o.encode('utf8')] 

def favicon():
    "_"
    code = '<svg %s n="%s"><path stroke-width="4" fill="none" stroke="Dodgerblue" d="M3,1L3,14L13,14L13,1"/></svg>' % (_SVGNS, datetime.datetime.now())
    tmp = base64.b64encode(code.encode('utf8'))
    return '<link xmlns="http://www.w3.org/1999/xhtml" rel="shortcut icon" type="image/svg+xml" href="data:image/svg+xml;base64,%s"/>\n' % tmp.decode('utf8')

def frontpage():
    "svg"
    o = '<?xml version="1.0" encoding="utf8"?>\n' 
    o += '<svg %s %s>\n' % (_SVGNS, _XLINKNS) + favicon()
    o += '<style type="text/css"></style>\n'
    o += '<text x="80" y="70" font-size="45">%s</text>\n' % __app__
    return o + '</svg>'

if __name__ == '__main__':
    print (__app__)
    
    sys.exit()

# End ⊔net!
