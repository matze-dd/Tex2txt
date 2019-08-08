
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
ltcmd = [
    'java', '-jar', ltjar,
    '--language', 'en-GB',
    '--encoding', 'utf-8',
    '--disable', 'WHITESPACE_RULE'
]

# prepare options for tex2txt()
#
options = tex2txt.Options(
                char=True,
                lang='en'
)

for file in sys.argv[1:]:

    # read file and call tex2txt()
    #
    tex = tex2txt.myopen(file).read()
    (plain, map) = tex2txt.tex2txt(tex, options)
    starts = list(m.start(0) for m in re.finditer(r"\n", "\n" + plain))

    # call LanguageTool
    #
    proc = subprocess.Popen(ltcmd, stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE)
    proc.stdin.write(plain.encode())
    s_out = proc.communicate()[0]
    proc.stdin.close()

    msg = s_out.decode()
    # msg = s_out.decode(encoding='latin-1')    # for Cygwin

    lines = msg.splitlines(keepends=True)
    if len(lines) > 0:
        # write final diagnostic line to stderr
        sys.stderr.write(lines.pop())

    # correct line and column numbers in messages
    #
    expr=r'^\d+\.\) Line (\d+), column (\d+), Rule ID: '
    def f(m):
        def ret(s1, s2):
            s = m.group(0)
            return (file + "\n" + "=" * len(file) + "\n"
                    + s[:m.start(1)] + "[" + s1 + "]" + s[m.end(1):m.start(2)]
                    + "[" + s2 + "]" + s[m.end(2):])
        def unkn():
            return ret("?", "?")

        lin = int(m.group(1))
        col = int(m.group(2))
        if lin < 1 or col < 1:
            return unkn()

        # find start of line number lin in plain file
        if lin > len(starts):
            return unkn()
        n = starts[lin - 1]

        # add column number col
        s = plain[n:]
        i = s.find("\n")
        if i >= 0 and col > i or i < 0 and col > len(s):
            return unkn()
        n += col - 1

        # map to character position in tex file
        if n >= len(map):
            return unkn()
        n = map[n]
        mark = ""
        if n < 0:
            mark = "+"
            n = -n

        # get line and column in tex file
        if n > len(tex):
            return unkn()
        s = tex[:n]
        lin = s.count("\n") + 1
        col = len(s) - (s.rfind("\n") + 1)
        return ret(str(lin) + mark, str(col) + mark)

    for s in lines:
        sys.stdout.write(re.sub(expr, f, s))

