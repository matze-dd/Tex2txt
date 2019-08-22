
#
#   Python3:
#   - application of tex2txt as module
#   - generation of HTML output with problems highlighted,
#     LT messages displayed on mouse hover
#
#   CREDITS:
#   This idea goes back to Sylvain Hallé who developed TeXtidote.
#
#   Usage:
#   python3 this_script a_LaTeX_file > out.html
#

import re
import sys
import subprocess
import tex2txt
import json

# number of context lines (before and after a highlighted place)
#
context_lines = 2

# properties of <span> tag for highlighting
#
highlight_style = 'background: orange; border: solid thin black'
highlight_style_unsure = 'background: yellow; border: solid thin black'

# style for display of line numbers
#
number_style = 'color: grey'

# path of LT java archive and used options
# - we need JSON output
#
ltjar = '../LT/LanguageTool-4.4/languagetool-commandline.jar'
ltcmd = ('java -jar ' +  ltjar
            + ' --json'
            + ' --language en-GB --encoding utf-8'
            + ' --disable WHITESPACE_RULE'
).split()

# prepare options for tex2txt()
#
options = tex2txt.Options(
            char=True,
#           repl=tex2txt.read_replacements('Tools/LT/repls.txt'),
#           defs=tex2txt.read_definitions('Tools/LT/defs.py'),
            lang='en'
)

#   the JSON decoder
#
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
    s = re.sub(' ', '&ensp;', s)
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

    prefix = '<html>\n<head>\n<meta charset="UTF-8">\n</head>\n<body>\n'
    postfix = '\n</body>\n</html>\n'

    matches = decoder.decode(msg)['matches']
    s = 'File "' + file + '" with ' + str(len(matches)) + ' problem(s)'
    prefix += '<H3>' + protect_html(s) + '</H3>\n'

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
        h.beglin = max(h.beglin - context_lines, 0)
        h.endlin = min(h.endlin + context_lines, len(starts) - 1)
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
        # no problems found: just display first context_lines lines
        endlin = min(context_lines, len(starts) - 1)
        res_tot = protect_html(tex[:starts[endlin]])
        line_numbers = list(range(endlin))
    if line_numbers:
        res_tot = add_line_numbers(res_tot, line_numbers)

    if overlaps:
        prefix += ('<H3>Overlapping message(s) found:'
                        + ' see end of page</H3>\n')
        post = '<H3>Overlapping message(s)</H3>\n'
        for h in overlaps:
            post += h + '<br>\n'
        postfix = post + postfix

    return prefix + res_tot + postfix

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
            '<tr>\n<td style="' + number_style + '" valign="top">'
            + s + '&nbsp;&nbsp;</td>\n<td>'
            + m.group(1) + '</td>\n</tr>\n'
        )
    s = re.sub(r'((?:.|\n)*?(?!\Z)|(?:.|\n)+?)(<br>\n|\Z)', f, s)
    return '<table cellspacing="0">\n' + s + '</table>\n'

#   ensure UTF-8 encoding for stdout
#   (not standard with Windows Python)
#
sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8')

for file in sys.argv[1:2]:

    # read file and call tex2txt()
    #
    f = tex2txt.myopen(file)
    tex = f.read()
    f.close()
    if not tex.endswith('\n'):
        tex += '\n'
    (plain, charmap) = tex2txt.tex2txt(tex, options)

    # call LanguageTool
    #
    proc = subprocess.Popen(ltcmd, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
    out = proc.communicate(input=plain.encode())[0]
    msg = out.decode()

    sys.stdout.write(generate_html(tex, charmap, msg, file))

