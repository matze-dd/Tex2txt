
#
#   Python3:
#   application of tex2txt as module
#
#   python3 this_script file1 file2 ...
#

import re
import sys
import subprocess
import tex2txt

# path of LT java archive and used options
#
ltjar = '../LT/LanguageTool-4.4/languagetool-commandline.jar'
ltcmd = ('java -jar ' +  ltjar
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

for file in sys.argv[1:]:

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
    # msg = out.decode(encoding='latin-1')    # for Cygwin

    lines = msg.splitlines(keepends=True)
    if len(lines) > 0:
        # write final diagnostic line to stderr
        sys.stderr.write(lines.pop())

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

