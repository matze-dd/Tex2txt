#
#   Tex2txt, a flexible LaTeX filter
#   Copyright (C) 2018-2020 Matthias Baumann
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

#
#   Python3:
#   application of tex2txt as module,
#   use LanguageTool to create a proofreading report in text or HTML format
#
#   Usage: see README.md
#
#   CREDITS for mode of HTML report:
#   This idea goes back to Sylvain Hallé who developed TeXtidote.
#

# path of LT java archive
# - zip file can be obtained from from www.languagetool.org/download,
#   and be unzipped with 'unzip xxx.zip'
# - Java has to be installed,
#   under Cygwin the Windows version is used
#
ltjar = '../LT/LanguageTool-4.7/languagetool-commandline.jar'
ltcmd = 'java -jar ' +  ltjar

# on option --server: address of server hosted by LT
#
ltserver = 'https://languagetool.org/api/v2/check'

# default option values
#
default_option_language = 'en-GB'
default_option_encoding = 'utf-8'
default_option_disable = 'WHITESPACE_RULE'
default_option_context = 2

# option --include: inclusion macros
#
inclusion_macros = 'include,input'

# HTML: properties of <span> tag for highlighting
#
highlight_style = 'background: orange; border: solid thin black'
highlight_style_unsure = 'background: yellow; border: solid thin black'

# HTML: style for display of line numbers
#
number_style = 'color: grey'

# messages on usage of server hosted by LT
#
msg_LT_server_txt = '''===
=== Using LanguageTool server at https://languagetool.org/
=== For conditions and restrictions, refer to
===     http://wiki.languagetool.org/public-http-api
===
'''
msg_LT_server_html = '''
<H2>Using LanguageTool server at
<a href="https://languagetool.org/" target="_blank">
https://languagetool.org/</a></H2>
For conditions and restrictions, refer to
<a href="http://wiki.languagetool.org/public-http-api" target="_blank">
http://wiki.languagetool.org/public-http-api</a>
<hr><hr>
'''


#####################################################################
#
#   implementation
#
#####################################################################

import os
import re
import sys
import subprocess
import tex2txt
import argparse
import json
import urllib.parse
import urllib.request

# parse command line
#
parser = argparse.ArgumentParser()
parser.add_argument('file', nargs='+')
parser.add_argument('--replace')
parser.add_argument('--define')
parser.add_argument('--language')
parser.add_argument('--t2t-lang')
parser.add_argument('--encoding')
parser.add_argument('--disable')
parser.add_argument('--extract')
parser.add_argument('--context', type=int)
parser.add_argument('--html', action='store_true')
parser.add_argument('--include', action='store_true')
parser.add_argument('--skip')
parser.add_argument('--plain', action='store_true')
parser.add_argument('--link', action='store_true')
parser.add_argument('--server', action='store_true')
cmdline = parser.parse_args()

if cmdline.language is None:
    cmdline.language = default_option_language
if cmdline.t2t_lang is None:
    cmdline.t2t_lang = cmdline.language[:2]
if cmdline.encoding is None:
    cmdline.encoding = default_option_encoding
if cmdline.disable is None:
    cmdline.disable = default_option_disable
if cmdline.context is None:
    cmdline.context = default_option_context
if cmdline.context < 0:
    # huge context: display whole text
    cmdline.context = int(1e8)
if cmdline.plain and (cmdline.include or cmdline.replace):
    tex2txt.fatal('cannot handle --plain together with --include or --replace')
if cmdline.replace:
    cmdline.replace = tex2txt.read_replacements(cmdline.replace,
                                                encoding=cmdline.encoding)
if cmdline.define:
    cmdline.define = tex2txt.read_definitions(cmdline.define, encoding='utf-8')

# complement LT options
#
ltcmd = ltcmd.split() + ['--json', '--encoding', 'utf-8',
                            '--language', cmdline.language]
if cmdline.disable:
    ltcmd += ['--disable', cmdline.disable]

# on option --include: add included files to work list
# otherwise: remove duplicates
#
if cmdline.include:
    sys.stderr.write('=== checking for file inclusions ... ')
    sys.stderr.flush()
    opts = tex2txt.Options(extr=inclusion_macros, repl=cmdline.replace,
                            defs=cmdline.define, lang=cmdline.t2t_lang)

def skip_file(fn):
    # does file name match regex from option --skip?
    return cmdline.skip and re.search(r'\A' + cmdline.skip + r'\Z', fn)

todo = cmdline.file
done = []
while todo:
    f = todo.pop(0)
    if f in done or skip_file(f):
        continue
    done.append(f)
    if not cmdline.include:
        continue
    fp = tex2txt.myopen(f, encoding=cmdline.encoding)
    tex = fp.read()
    fp.close()
    (plain, _) = tex2txt.tex2txt(tex, opts)
    for f in plain.split():
        if not f.endswith('.tex'):
            f += '.tex'
        if f not in done + todo and not skip_file(f):
            todo.append(f)

cmdline.file = done
if cmdline.include:
    sys.stderr.write(', '.join(cmdline.file) + '\n')
    sys.stderr.flush()

# prepare options for tex2txt()
#
options = tex2txt.Options(char=True, repl=cmdline.replace,
                            defs=cmdline.define, lang=cmdline.t2t_lang,
                            extr=cmdline.extract)

# helpers for robust JSON evaluation
#
json_decoder = json.JSONDecoder()

def json_fatal(item):
    tex2txt.fatal('error reading JSON output from proofreader, (sub-)item "'
                    + item + '"')
def json_get(dic, item, typ):
    if not isinstance(dic, dict):
        json_fatal(item)
    ret = dic.get(item)
    if not isinstance(ret, typ):
        json_fatal(item)
    return ret

#   for given file:
#   - print progress message to stderr
#   - read file
#   - extract plain text
#   - call proofreading program
#
def run_proofreader(file):

    sys.stderr.write('=== ' + file + '\n')
    sys.stderr.flush()
    f = tex2txt.myopen(file, encoding=cmdline.encoding)
    tex = f.read()
    f.close()
    if not tex.endswith('\n'):
        tex += '\n'

    if cmdline.plain:
        (plain, charmap) = (tex, list(range(1, len(tex) + 1)))
    else:
        (plain, charmap) = tex2txt.tex2txt(tex, options)

    # here, we could dispatch to other tools,
    # see for instance Python package prowritingaid.python
    #
    matches = run_languagetool(plain)

    return (tex, plain, charmap, matches)

#   run LT and return element 'matches' from JSON output
#
def run_languagetool(plain):
    if cmdline.server:
        # use Web server hosted by LT
        data = {            # see package pyLanguagetool for field names
            'text': plain,
            'language': cmdline.language,
            'disabledRules': cmdline.disable,
        }
        data = urllib.parse.urlencode(data).encode(encoding='ascii')
        request = urllib.request.Request(ltserver, data=data)
        try:
            reply = urllib.request.urlopen(request)
            out = reply.read()
            reply.close()
        except:
            tex2txt.fatal('error connecting to "' + ltserver + '"')
    else:
        # use local installation
        try:
            out = subprocess.run(ltcmd, input=plain.encode(encoding='utf-8'),
                                        stdout=subprocess.PIPE).stdout
        except:
            tex2txt.fatal('error running "' + ltcmd[0] + '"')

    out = out.decode(encoding='utf-8')
    try:
        dic = json_decoder.decode(out)
    except:
        json_fatal('JSON root element')
    matches = json_get(dic, 'matches', list)
    return matches


#####################################################################
#
#   text report
#
#####################################################################

#   generate text report from element 'matches' of JSON output
#
#   - compare printMatches() in file CommandLineTools.java in directory
#     languagetool-commandline/src/main/java/org/languagetool/commandline/
#   - XXX: some code duplication with begin_match()
#
def output_text_report(tex, plain, charmap, matches, file):
    starts = tex2txt.get_line_starts(plain)

    for (nr, m) in enumerate(matches, 1):
        offset = json_get(m, 'offset', int)
        lin = plain.count('\n', 0, offset) + 1
        nl = plain.rfind('\n', 0, offset) + 1
        col = offset - nl + 1
        lc = tex2txt.translate_numbers(tex, plain, charmap, starts, lin, col)

        rule = json_get(m, 'rule', dict)
        print('=== ' + file + ' ===')

        s = (str(nr) + '.) Line ' + str(lc.lin) + ', column ' + str(lc.col)
                + ', Rule ID: ' + json_get(rule, 'id', str))
        if 'subId' in rule:
                s += '[' + json_get(rule, 'subId', str) + ']'
        print(s)
        print('Message: ' + json_get(m, 'message', str))

        repls = '; '.join(json_get(r, 'value', str)
                                for r in json_get(m, 'replacements', list))
        print('Suggestion: ' + repls)

        cont = json_get(m, 'context', dict)
        txt = json_get(cont, 'text', str)
        beg = json_get(cont, 'offset', int)
        length = json_get(cont, 'length', int)
        print(txt.replace('\t', ' '))
        print(' ' * beg + '^' * length)

        if 'urls' in rule:
            urls = json_get(rule, 'urls', list)
            if urls:
                print('More info: ' + json_get(urls[0], 'value', str))

        print('')

    sys.stdout.flush()  # in case redirected to file


if not cmdline.html:
    if cmdline.server:
        sys.stderr.write(msg_LT_server_txt)
    for file in cmdline.file:
        (tex, plain, charmap, matches) = run_proofreader(file)
        output_text_report(tex, plain, charmap, matches, file)
    exit()


#####################################################################
#
#   HTML report
#
#####################################################################

#   protect text between HTML tags from being seen as HTML code,
#   preserve text formatting
#   - '<br>\n' is used by generate_highlight() and add_line_numbers()
#
def protect_html(s):
    s = re.sub(r'&', r'&amp;', s)
    s = re.sub(r'"', r'&quot;', s)
    s = re.sub(r'<', r'&lt;', s)
    s = re.sub(r'>', r'&gt;', s)
    s = re.sub(r'\t', ' ' * 8, s)
    s = re.sub(r' ', '&ensp;', s)
    s = re.sub(r'\n', r'<br>\n', s)
    return s

#   generate HTML tag from LT message
#
def begin_match(m, lin, unsure):
    cont = json_get(m, 'context', dict)
    txt = json_get(cont, 'text', str)
    beg = json_get(cont, 'offset', int)
    end = beg + json_get(cont, 'length', int)
    rule = json_get(m, 'rule', dict)

    msg = protect_html(json_get(m, 'message', str)) + '\n'

    msg += protect_html('Line ' + str(lin) + ('+' if unsure else '')
                        + ': >>>' + txt[beg:end] + '<<<')
    rule_id = json_get(rule, 'id', str)
    if 'subId' in rule:
            rule_id += '[' + json_get(rule, 'subId', str) + ']'
    msg += protect_html('    (Rule ID: ' + rule_id + ')') + '\n'

    repls = '; '.join(json_get(r, 'value', str)
                        for r in json_get(m, 'replacements', list))
    msg += 'Suggestion: ' + protect_html(repls) + '\n'

    txt = txt[:beg] + '>>>' + txt[beg:end] + '<<<' + txt[end:]
    msg += 'Context: ' + protect_html(txt)

    style = highlight_style_unsure if unsure else highlight_style
    beg_tag = '<span style="' + style + '" title="' + msg + '">'
    end_href = ''
    if cmdline.link and 'urls' in rule:
        urls = json_get(rule, 'urls', list)
        if urls:
            beg_tag += ('<a href="' + json_get(urls[0], 'value', str)
                        + '" target="_blank">')
            end_href = '</a>'
    return (beg_tag, end_href)

def end_match():
    return '</span>'

#   hightlight a text region
#   - avoid that span tags cross line breaks (otherwise problems in <table>)
#
def generate_highlight(m, s, lin, unsure):
    (pre, end_href) = begin_match(m, lin, unsure)
    s = protect_html(s)
    post = end_href + end_match()
    def f(m):
        return pre + m.group(1) + post + m.group(2)
    return re.sub(r'((?:.|\n)*?(?!\Z)|(?:.|\n)+?)(<br>\n|\Z)', f, s)

#   generate HTML output
#
def generate_html(tex, charmap, matches, file):

    s = 'File "' + file + '" with ' + str(len(matches)) + ' problem(s)'
    title = protect_html(s)
    anchor = file
    anchor_overlap = file + '-@@@'
    prefix = '<a id="' + anchor + '"></a><H3>' + title + '</H3>\n'

    # collect data for highlighted places
    #
    hdata = []
    for m in matches:
        beg = json_get(m, 'offset', int)
        end = beg + max(1, json_get(m, 'length', int))
        if beg < 0 or end < 0 or beg >= len(charmap) or end >= len(charmap):
            tex2txt.fatal('generate_html():'
                            + ' bad message read from proofreader')
        h = tex2txt.Aux()
        h.unsure = (charmap[beg] < 0 or charmap[max(beg, end - 1)] < 0)
        h.beg = abs(charmap[beg]) - 1
        h.end = abs(charmap[max(beg, end - 1)])         # see issue #21
        if h.unsure or h.end <= h.beg:
            h.end = h.beg + 1

        if (h.end == h.beg + 1 and tex[h.beg] == '\\'
                and re.search(r'(?<!\\)(\\\\)*\Z', tex[:h.beg])):
            # HACK:
            # if matched a single \ that is actually followed by macro name:
            # also highlight the macro name
            s = re.search(r'\A\\[a-zA-Z]+', tex[h.beg:])
            if s:
                h.end = h.beg + len(s.group(0))
        elif h.unsure and tex[h.beg].isalpha():
            # HACK:
            # if unsure: mark till end of word (only letters)
            s = re.search(r'\A.[^\W0-9_]+', tex[h.beg:])
            if s:
                h.end = h.beg + len(s.group(0))

        h.beglin = tex.count('\n', 0, h.beg)
        h.endlin = tex.count('\n', 0, h.end) + 1
        h.lin = h.beglin
        h.m = m
        hdata.append(h)

    # sort matches according to offset in tex
    # - necessary for separated footnotes etc.
    #
    hdata.sort(key=lambda h: h.beg)

    # group adjacent matches into regions
    #
    regions = []
    starts = tex2txt.get_line_starts(tex)
    for h in hdata:
        h.beglin = max(h.beglin - cmdline.context, 0)
        h.endlin = min(h.endlin + cmdline.context, len(starts) - 1)
        if not regions or h.beglin >= max(h.endlin for h in regions[-1]):
            # start a new region
            regions.append([h])
        else:
            # match is part of last region
            regions[-1].append(h)

    # produce output
    #
    res_tot = ''
    overlaps = []
    line_numbers = []
    for reg in regions:
        #
        # generate output for one region:
        # collect all matches in that region
        #
        beglin = reg[0].beglin
        endlin = max(h.endlin for h in reg)
        res = ''
        last = starts[beglin]
        for h in reg:
            s = generate_highlight(h.m, tex[h.beg:h.end], h.lin + 1, h.unsure)
            if h.beg < last:
                # overlapping with last message
                overlaps.append((s, h.lin + 1))
                continue
            res += protect_html(tex[last:h.beg])
            res += s
            last = h.end

        res += protect_html(tex[last:starts[endlin]])
        res_tot += res + '<br>\n'
        line_numbers += list(range(beglin, endlin)) + [-1]

    if not line_numbers:
        # no problems found: just display first cmdline.context lines
        endlin = min(cmdline.context, len(starts) - 1)
        res_tot = protect_html(tex[:starts[endlin]])
        line_numbers = list(range(endlin))
    if line_numbers:
        res_tot = add_line_numbers(res_tot, line_numbers)

    postfix = ''
    if overlaps:
        prefix += ('<a href="#' + anchor_overlap + '">'
                        + '<H3>Overlapping message(s) found:'
                        + ' see here</H3></a>\n')
        postfix = ('<a id="' + anchor_overlap + '"></a><H3>'
                    + protect_html('File "' + file + '":')
                    + ' overlapping message(s)</H3>\n')
        postfix += '<table cellspacing="0">\n'
        for (s, lin) in overlaps:
            postfix += ('<tr><td style="' + number_style
                            + '" align="right" valign="top">' + str(lin)
                            + '&nbsp;&nbsp;</td><td>' + s + '</td></tr>\n')
        postfix += '</table>\n'

    return (title, anchor, prefix + res_tot + postfix)

#   add line numbers using a large <table>
#
def add_line_numbers(s, line_numbers):
    aux = tex2txt.Aux()
    aux.lineno = 0
    def f(m):
        lin = line_numbers[aux.lineno]
        s = str(lin + 1) if lin >= 0 else ''
        aux.lineno += 1
        return (
            '<tr>\n<td style="' + number_style
            + '" align="right" valign="top">' + s + '&nbsp;&nbsp;</td>\n<td>'
            + m.group(1) + '</td>\n</tr>\n'
        )
    s = re.sub(r'((?:.|\n)*?(?!\Z)|(?:.|\n)+?)(<br>\n|\Z)', f, s)
    return '<table cellspacing="0">\n' + s + '</table>\n'


#   generate HTML report: a part for each file
#
html_report_parts = []
for file in cmdline.file:
    (tex, plain, charmap, matches) = run_proofreader(file)
    html_report_parts.append(generate_html(tex, charmap, matches, file))

#   ensure UTF-8 encoding for stdout
#   (not standard with Windows Python)
#
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8')

page_prefix = '<html>\n<head>\n<meta charset="UTF-8">\n</head>\n<body>\n'
page_postfix = '\n</body>\n</html>\n'

sys.stdout.write(page_prefix)
if cmdline.server:
    sys.stdout.write(msg_LT_server_html)
if len(html_report_parts) > 1:
    # start page with file index
    sys.stdout.write('<H3>Index</H3>\n<ul>\n')
    for r in html_report_parts:
        s = '<li><a href="#' + r[1] + '">' + r[0] + '</a></li>\n'
        sys.stdout.write(s)
    sys.stdout.write('</ul>\n<hr><hr>\n')
for (i, r) in enumerate(html_report_parts):
    if i:
        sys.stdout.write('<hr><hr>\n')
    sys.stdout.write(r[2])
sys.stdout.write(page_postfix)

