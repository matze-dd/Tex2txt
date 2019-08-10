
#
#   Python3:
#   - application of tex2txt as module
#   - generation of html output with problems highlighted,
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
    s = re.sub(' ', '&nbsp;', s)
    s = re.sub(r'\n', r'<br>\n', s)
    return s

#   generate HTML tag from LT message
#
def begin_match(m):
    cont = m['context']
    txt = cont['text']
    beg = cont['offset']
    end = beg + cont['length']

    msg = protect_html(m['message']) + '\n'

    msg += protect_html('>>>' + txt[beg:end] + '<<<') + '\n'

    repls = ' '.join("'" + r['value'] + "'" for r in m['replacements'])
    msg += 'Suggestions: ' + protect_html(repls) + '\n'

    txt = txt[:beg] + '>>>' + txt[beg:end] + '<<<' + txt[end:]
    msg += 'Context: ' + protect_html(txt)

    return '<span style="background: orange" title="' + msg + '">'

def end_match(m):
    return '</span>'

#   generate HTML output
#
def generate_html(tex, charmap, msg, file):

    prefix = '<html>\n<body>\n'
    postfix = '\n</body>\n</html>'

    js = dec.decode(msg)

    # sort matches according to offset in tex
    # - for footnotes etc.
    matches = list(m for m in js['matches'])
    matches.sort(key=lambda m: abs(charmap[m['offset']]))

    h = 'File ' + file + ': ' + str(len(matches)) + ' problem(s)'
    prefix += '<H3>' + protect_html(h) + '</H3>\n'

    res = ''
    last = 0
    skipped = 0

    for m in matches:

        offs = m['offset']
        length = max(1, m['length'])
        beg = abs(charmap[offs]) - 1
        end = abs(charmap[offs + length]) - 1
        if end <= beg:
            end = beg + 1

        if beg < last:
            # overlapping with last message
            if end <= last:
                # cannot shift beginning: skip
                skipped += 1
                continue
            beg = last

        res += protect_html(tex[last:beg])
        res += begin_match(m)
        res += protect_html(tex[beg:end])
        res += end_match(m)
        last = end

    warn = ''
    if skipped:
        warn = ('<H3>[[skipped display of problem(s)'
                                + ' due to overlap' + ']]</H3>')
    return prefix + warn + res + protect_html(tex[last:]) + postfix

for file in sys.argv[1:2]:

    # read file and call tex2txt()
    #
    tex = tex2txt.myopen(file).read()
    (plain, charmap) = tex2txt.tex2txt(tex, options)
    starts = tex2txt.get_line_starts(plain)

    # call LanguageTool
    #
    proc = subprocess.Popen(ltcmd, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
    out = proc.communicate(input=plain.encode())[0]
    msg = out.decode()

    sys.stdout.write(generate_html(tex, charmap, msg, file))

