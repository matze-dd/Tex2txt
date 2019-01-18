
#   bash
#   Example for filtering line numbers
#

file=z.tex

#   Python3:
#   add original line numbers to messages
#   - argv[1]: RE search pattern; first () group must contain the number
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
                    + m.string[m.end(1):m.end(0)])
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
    | python3 -c "$repl_lines" '^\d+\.\) Line (\d+),' $file.lin

