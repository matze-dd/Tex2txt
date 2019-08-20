
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

# properties of <span> tag for highlighting
#
highlight_style = 'background: orange; border: solid thin black'
highlight_style_unsure = 'background: yellow; border: solid thin black'

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
dec = json.JSONDecoder()

#   protect text between HTML tags from being seen as HTML code,
#   preserve text formatting
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

#   generate HTML output
#
def generate_html(tex, charmap, msg, file):

    prefix = '<html>\n<body>\n'
    postfix = '\n</body>\n</html>\n'

    js = dec.decode(msg)

    # sort matches according to offset in tex
    # - for footnotes etc.
    matches = list(m for m in js['matches'])
    def f(m):
        beg = m['offset']
        end = beg + max(1, m['length'])
        if beg < 0 or end < 0 or beg >= len(charmap) or end >= len(charmap):
            tex2txt.fatal('generate_html():'
                            + ' bad message read from LanguageTool')
        return abs(charmap[beg])
    matches.sort(key=f)

    h = 'File "' + file + '" with ' + str(len(matches)) + ' problem(s)'
    prefix += '<H3>' + protect_html(h) + '</H3>\n'

    res = ''
    last = 0
    overlaps = []

    for m in matches:

        beg = m['offset']
        end = beg + max(1, m['length'])
        unsure = (charmap[beg] < 0 or charmap[end] < 0)
        beg = abs(charmap[beg]) - 1
        end = abs(charmap[end]) - 1
        if unsure or end <= beg:
            end = beg + 1
        lin = tex.count('\n', 0, beg) + 1

        if (end == beg + 1 and tex[beg] == '\\'
                and re.search(r'(?<!\\)(\\\\)*\Z', tex[:beg])):
            # HACK:
            # if matched a single \ that is actually followed by macro name:
            # also highlight the macro name
            s = re.search(r'\A\\[a-zA-Z]+', tex[beg:])
            if s:
                end = beg + len(s.group(0))

        if beg < last:
            # overlapping with last message
            overlaps.append((m, tex[beg:end], lin, unsure))
            continue

        res += protect_html(tex[last:beg])
        res += begin_match(m, lin, unsure)
        res += protect_html(tex[beg:end])
        res += end_match()
        last = end

    res += protect_html(tex[last:])

    if overlaps:
        prefix += ('<H3>Overlapping message(s) found:'
                        + ' see end of page</H3>\n')
        post = '<H3>Overlapping message(s)</H3>\n'
        for (m, s, lin, unsure) in overlaps:
            post += begin_match(m ,lin, unsure)
            post += protect_html(s)
            post += end_match() + '<br>\n'
        postfix = post + postfix

    return prefix + res + postfix

for file in sys.argv[1:2]:

    # read file and call tex2txt()
    #
    f = tex2txt.myopen(file)
    tex = f.read()
    f.close()
    (plain, charmap) = tex2txt.tex2txt(tex, options)

    # call LanguageTool
    #
    proc = subprocess.Popen(ltcmd, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
    out = proc.communicate(input=plain.encode())[0]
    msg = out.decode()

    sys.stdout.write(generate_html(tex, charmap, msg, file))

