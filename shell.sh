
#   bash
#   Example for filtering line numbers
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

#   Python3:
#   add original line numbers to messages
#   - argv[1]:  RE search pattern;
#               first () group must contain the number;
#               text till second () group is removed
#   - argv[2]: file with original line numbers
#
repl_lines='
import re, sys
expr = sys.argv[1]
numbers = open(sys.argv[2]).readlines()
def repl(m):
    lin = int(m.group(1)) - 1
    if lin >= 0 and lin < len(numbers):
        n = numbers[lin].strip()
        return (m.string[m.start(0):m.end(1)] + " [" + n + "]"
                    + m.string[m.end(2):m.end(0)])
    return m.group(0)
for lin in sys.stdin:
    sys.stdout.write(re.sub(expr, repl, lin))
'

# extract raw text, write line number information
#
python3 tex2txt.py --lang en --nums $file.lin $file > $file.txt

# call language checker, filter line numbers in output;
# LT produces: '1.) Line 25, column 13, ...'
#
java -jar ../LT/LanguageTool-4.4/languagetool-commandline.jar \
        --language en-GB --disable WHITESPACE_RULE $file.txt \
    | python3 -c "$repl_lines" '^\d+\.\) Line (\d+), column (\d+)' $file.lin

