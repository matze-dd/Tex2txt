
#   Bash:
#   example for tracking of line and column numbers
#

if [ $# -ne 1 ]
then
    echo "usage: bash $0 file_name" >&2
    exit 1
fi
file=$1

if [ ! -r "$file" ]
then
    echo "$0: cannot read file '$file'" >&2
    exit 1
fi

#
#   Python3:
#   replace line and column numbers
#   - argv[1]: original LaTeX file
#   - argv[2]: derived file with plain text
#   - argv[3]: file with character offset mapping
#   - expr: regular expression:
#     matching group 1 is line number, group 2 is column number
#
filter_numbers='

# LT produces: "1.) Line 25, column 13, Rule ID: ..."
expr = r"^\d+\.\) Line (\d+), column (\d+), Rule ID: "

import re, sys
tex = open(sys.argv[1]).read()
plain = open(sys.argv[2]).read()
def f(s):
    s = s.strip()
    if s[-1] == "+":
        return -int(s[:-1])
    return int(s)
map = tuple(f(s) for s in open(sys.argv[3]))

def f(m):
    def ret(s1, s2):
        s = m.group(0)
        return (s[:m.start(1)] + "[" + s1 + "]" + s[m.end(1):m.start(2)]
                    + "[" + s2 + "]" + s[m.end(2):])
    def unkn():
        return ret("?", "?")

    lin = int(m.group(1))
    col = int(m.group(2))
    if lin < 1 or col < 1:
        return unkn()

    # find start of line number lin in plain file
    i = 0
    n = -1
    while i < lin - 1:
        n += 1
        if n >= len(plain):
            break
        if plain[n] == "\n":
            i += 1
    if i < lin - 1:
        return unkn()
    n += 1

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

for s in sys.stdin:
    sys.stdout.write(re.sub(expr, f, s))
'

# extract raw text, write character offset information
#
python3 tex2txt.py --lang en --char --nums $file.num $file > $file.txt

# call language checker, filter line numbers in output;
#
java -jar ../LT/LanguageTool-4.4/languagetool-commandline.jar \
        --language en-GB --disable WHITESPACE_RULE $file.txt \
    | python3 -c "$filter_numbers" $file $file.txt $file.num

