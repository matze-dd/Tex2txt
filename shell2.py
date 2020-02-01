
#
#   Python3:
#   simple application of tex2txt.py as module
#
#   - extract plain text from LaTeX file(s)
#     (phrase replacements and macro definitions: see variable 'options')
#   - run LanguageTool (LT), see variables 'ltjar' and 'ltcmd'
#   - filter stdout of LT: correct line and column numbers in messages
#     (displayed in [] brackets to indicate filter operation)
#
#   Usage:
#   python3 this_script latex_file [latex_file ...]
#

import os
import re
import sys
import subprocess
import tex2txt

# encoding of input file(s), values as for standard function open()
#
input_encoding = 'utf-8'
# input_encoding = 'latin-1'

# path of LT java archive and used options
#
ltjar = '../LT/LanguageTool-4.7/languagetool-commandline.jar'
ltcmd = ('java -jar ' +  ltjar
            + ' --language en-GB --encoding utf-8'
            + ' --disable WHITESPACE_RULE'
).split()

# prepare options for tex2txt()
#
options = tex2txt.Options(
            char=True,
#           repl=tex2txt.read_replacements('Tools/LT/repls.txt',
#                                           encoding=input_encoding),
#           defs=tex2txt.read_definitions('Tools/LT/defs.py',
#                                           encoding='utf-8'),
            lang='en'
)

for file in sys.argv[1:]:

    sys.stderr.write('=== ' + file + '\n')
    sys.stderr.flush()

    # read file and call tex2txt()
    #
    f = tex2txt.myopen(file, encoding=input_encoding)
    tex = f.read()
    f.close()
    (plain, charmap) = tex2txt.tex2txt(tex, options)
    starts = tex2txt.get_line_starts(plain)

    # call LanguageTool
    #
    out = subprocess.run(ltcmd, input=plain.encode(encoding='utf-8'),
                                stdout=subprocess.PIPE)
    if 'Windows' in os.getenv('OS', default=''):
        # under Windows, LanguageTool produces Latin-1 output
        msg = out.stdout.decode(encoding='latin-1')
    else:
        msg = out.stdout.decode(encoding='utf-8')

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
            return (file + '\n' + '=' * len(file) + '\n'
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

