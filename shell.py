#
#   Tex2txt, a flexible LaTeX filter
#   Copyright (C) 2018-2019 Matthias Baumann
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

# parse command line
#
parser = argparse.ArgumentParser()
parser.add_argument('file', nargs='+')
parser.add_argument('--replace')
parser.add_argument('--define')
parser.add_argument('--language')
parser.add_argument('--encoding')
parser.add_argument('--disable')
parser.add_argument('--extract')
parser.add_argument('--context', type=int)
parser.add_argument('--html', action='store_true')
parser.add_argument('--include', action='store_true')
cmdline = parser.parse_args()

if cmdline.language is None:
    cmdline.language = default_option_language
if cmdline.encoding is None:
    cmdline.encoding = default_option_encoding
if cmdline.disable is None:
    cmdline.disable = default_option_disable
if cmdline.context is None:
    cmdline.context = default_option_context
if cmdline.context < 0:
    # huge context: display whole text
    cmdline.context = int(1e8)
if cmdline.replace:
    cmdline.replace = tex2txt.read_replacements(cmdline.replace,
                                                encoding=cmdline.encoding)
if cmdline.define:
    cmdline.define = tex2txt.read_definitions(cmdline.define, encoding='utf-8')

# complement LT options
#
ltcmd = ltcmd.split() + ['--encoding', 'utf-8', '--language', cmdline.language]
if cmdline.html:
    ltcmd += ['--json']
if cmdline.disable:
    ltcmd += ['--disable', cmdline.disable]

# on option --include: add included files to work list
# otherwise: remove duplicates
#
if cmdline.include:
    sys.stderr.write('=== checking for file inclusions ... ')
    sys.stderr.flush()
    opts = tex2txt.Options(extr=inclusion_macros, repl=cmdline.replace,
                            defs=cmdline.define, lang=cmdline.language[:2])

todo = cmdline.file
done = []
while todo:
    f = todo.pop(0)
    if f in done:
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
        if f not in done + todo:
            todo.append(f)

cmdline.file = done
if cmdline.include:
    sys.stderr.write(', '.join(cmdline.file) + '\n')
    sys.stderr.flush()

# prepare options for tex2txt()
#
options = tex2txt.Options(char=True, repl=cmdline.replace,
                            defs=cmdline.define, lang=cmdline.language[:2],
                            extr=cmdline.extract)


#####################################################################
#
#   text report
#
#####################################################################

def output_text_report(file):
    sys.stderr.write('=== ' + file + '\n')
    sys.stderr.flush()

    # read file and call tex2txt()
    #
    f = tex2txt.myopen(file, encoding=cmdline.encoding)
    tex = f.read()
    f.close()
    if not tex.endswith('\n'):
        tex += '\n'
    (plain, charmap) = tex2txt.tex2txt(tex, options)
    starts = tex2txt.get_line_starts(plain)

    # call LanguageTool
    #
    proc = subprocess.Popen(ltcmd, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
    out = proc.communicate(input=plain.encode(encoding='utf-8'))[0]
    s = os.getenv('OS')
    if s and s.count('Windows'):
        # under Windows, LanguageTool produces Latin-1 output
        msg = out.decode(encoding='latin-1')
    else:
        msg = out.decode(encoding='utf-8')

    lines = msg.splitlines(keepends=True)
    if lines:
        # write final diagnostic line to stderr
        sys.stderr.write(lines.pop())
        sys.stderr.flush()

    # correct line and column numbers in messages, prepend file name
    #
    expr=r'^\d+\.\) Line (\d+), column (\d+), Rule ID: '
    def f(m):
        def ret(s1, s2):
            s = m.group(0)
            return ('=== ' + file + ' ===\n'
                    + s[:m.start(1)] + '[' + s1 + ']' + s[m.end(1):m.start(2)]
                    + '[' + s2 + ']' + s[m.end(2):])

        lin = int(m.group(1))
        col = int(m.group(2))
        r = tex2txt.translate_numbers(tex, plain, charmap, starts, lin, col)
        if not r:
            return ret('?', '?')
        mark = '+' if r.flag else ''
        return ret(str(r.lin) + mark, str(r.col) + mark)

    for s in lines:
        sys.stdout.write(re.sub(expr, f, s))
    sys.stdout.flush()

if not cmdline.html:
    for file in cmdline.file:
        output_text_report(file)
    exit()


#####################################################################
#
#   HTML report
#
#####################################################################

import json
decoder = json.JSONDecoder()

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
    cont = m['context']
    txt = cont['text']
    beg = cont['offset']
    end = beg + cont['length']

    msg = protect_html(m['message'] + '; ' + m['rule']['id']) + '\n'

    msg += protect_html('Line ' + str(lin) + ('+' if unsure else '')
                        + ': >>>' + txt[beg:end] + '<<<') + '\n'

    repls = ' '.join("'" + r['value'] + "'" for r in m['replacements'])
    msg += 'Suggestions: ' + protect_html(repls) + '\n'

    txt = txt[:beg] + '>>>' + txt[beg:end] + '<<<' + txt[end:]
    msg += 'Context: ' + protect_html(txt)

    style = highlight_style_unsure if unsure else highlight_style
    return '<span style="' + style + '" title="' + msg + '">'

def end_match():
    return '</span>'

#   hightlight a text region
#   - avoid that span tags cross line breaks (otherwise problems in <table>)
#
def generate_highlight(m, s, lin, unsure):
    pre = begin_match(m, lin, unsure)
    s = protect_html(s)
    post = end_match()
    def f(m):
        return pre + m.group(1) + post + m.group(2)
    return re.sub(r'((?:.|\n)*?(?!\Z)|(?:.|\n)+?)(<br>\n|\Z)', f, s)

#   generate HTML output
#
def generate_html(tex, charmap, msg, file):

    matches = decoder.decode(msg)['matches']
    s = 'File "' + file + '" with ' + str(len(matches)) + ' problem(s)'
    title = protect_html(s)
    anchor = file
    anchor_overlap = file + '-@@@'
    prefix = '<a id="' + anchor + '"></a><H3>' + title + '</H3>\n'

    # collect data for highlighted places
    #
    hdata = []
    for m in matches:
        beg = m['offset']
        end = beg + max(1, m['length'])
        if beg < 0 or end < 0 or beg >= len(charmap) or end >= len(charmap):
            tex2txt.fatal('generate_html():'
                            + ' bad message read from LanguageTool')
        h = tex2txt.Aux()
        h.unsure = (charmap[beg] < 0 or charmap[end] < 0)
        h.beg = abs(charmap[beg]) - 1
        h.end = abs(charmap[end]) - 1
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
                overlaps.append(s)
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
        for h in overlaps:
            postfix += h + '<br>\n'

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

#   ensure UTF-8 encoding for stdout
#   (not standard with Windows Python)
#
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8')

html_report_parts = []
for file in cmdline.file:

    sys.stderr.write('=== ' + file + '\n')
    sys.stderr.flush()

    # read file and call tex2txt()
    #
    f = tex2txt.myopen(file, encoding=cmdline.encoding)
    tex = f.read()
    f.close()
    if not tex.endswith('\n'):
        tex += '\n'
    (plain, charmap) = tex2txt.tex2txt(tex, options)

    # call LanguageTool
    #
    proc = subprocess.Popen(ltcmd, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
    out = proc.communicate(input=plain.encode(encoding='utf-8'))[0]
    msg = out.decode(encoding='utf-8')

    html_report_parts.append(generate_html(tex, charmap, msg, file))


page_prefix = '<html>\n<head>\n<meta charset="UTF-8">\n</head>\n<body>\n'
page_postfix = '\n</body>\n</html>\n'

sys.stdout.write(page_prefix)
if len(html_report_parts) > 1:
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

