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

#   Python3:
#   Extract raw text from LaTeX file, write result to standard output
#
#   . output suitable for check, e.g., with LanguageTool (LT)
#   . we make an effort to avoid creation of additional empty lines that
#     break sentences for LT; this keeps number of "false" LT warnings low
#   . line number changes caused by this approach can be compensated by
#     a small filter for LT messages using the file from option --nums
#   . interpunction in displayed equations can be checked to a certain extent
#
#   - argument:
#     name of file with input text; read standard input if missing
#   - option --nums file:   (file name)
#     file for storing original line numbers;
#     can be used later to correct line numbers in messages
#   - option --repl file:   (file name)
#     file with replacements performed at the end, namely after
#     changing, e.g., inline maths to $$, and german hyphen "= to - ;
#     see LAB:SPELLING below for line syntax
#   - option --extr ma[,mb,...]:    (list of macro names)
#     extract only arguments of these macros;
#     useful, e.g., for check of foreign-language text and footnotes
#   - option --lang xy:     (language de or en, default: de)
#     used for adaptation of equation replacements, math operator names,
#     proof titles, and replacement of foreign-language text;
#     see LAB:LANGUAGE below
#
#   Some actions:
#   - \begin{...} and \end{...} of environments are deleted;
#     tailored behaviour for some environment types listed below
#   - text in heading macros as \section{...} is extracted
#   - placeholders for \ref, \eqref, \pageref, and \cite
#   - "undeclared" macros are silently ignored
#   - inline math $...$ is reduced to $$ (variable parms.inline_math)
#   - equation environments are resolved in a way suitable for check of
#     interpunction, argument of \text{...} is included into output text;
#     see LAB:EQUATIONS below for example and detailed description
#   - rare LT warnings can be suppressed using \LTadd, \LTskip,
#     and \LTalter (see below) in the LaTeX text with suitable macro
#     definitions there, e.g. adding something for LT only:
#       \newcommand{\LTadd}[1]{}
#
#   Principle of operation:
#   - read complete input text into a string, then make replacements
#   - replacements are performed via the wrapper mysub() in order
#     to observe deletion and inclusion of line breaks
#   - in order to treat nested braces / brackets and some nested
#     environments, we construct regular expressions by iteration;
#     maximum recognized nesting depth (and thus length of these expressions)
#     is controlled by the variables max_depth_br and max_depth_env
#
#   Bugs:
#   - parsing with regular expressions is fun, but limited; as the
#     replacement argument of re.sub() may be a callable, one can plug in
#     some programming, however
#   - several related shortcomings are marked with BUG (for some
#     of them, warnings are generated)
#
#
#                                   Matthias Baumann, December 2018
#

class Parms: pass
parms = Parms()

#   these are macros with tailored treatment;
#   replacement only if not given in option --extr
#
#   Macro(name, args, repl=''):
#   args:
#       - A stands for an {...} argument
#       - O stands for an optional [...]
#   repl:
#       - replacement pattern, r'\d' (d: single digit) extracts text
#         from position d in args (counting from 1);
#         escape rules: see replacement argument of re.sub()
#       - repl empty: suppress generation of empty lines
#       - if refering to an optional argument, e.g.
#               Macro('xxx', 'OA', r'\1\2'),
#         Python version of at least 3.5 is required (non-matched group
#         yields empty string); otherwise re module may raise exceptions
#
parms.the_macros = lambda: (
    Macro('color', 'A'),
    Macro('comment', 'A'),
    Macro('colorbox', 'AA', r'\2'),
    Macro('documentclass', 'OA'),
    Macro('fcolorbox', 'AAA', r'\3'),
    Macro('footnote', 'A'),
    Macro('footnotetext', 'A'),
    Macro('framebox', 'OOA', r'\3'),
    Macro(r'hspace\*?', 'A'),
    Macro('includegraphics', 'OA'),
    Macro('input', 'A'),
    Macro('newcommand', 'AOA'),
    Macro('TBDoff', 'A'),
    Macro('textcolor', 'AA', r'\2'),
    Macro('usepackage', 'OA'),
    Macro(r'vspace\*?', 'A'),

    # suppress some LT warnings by altering the LaTeX text
    Macro('LTadd', 'A', r'\1'),
                    # for LaTeX, argument is ignored
    Macro('LTalter', 'AA', r'\2'),
                    # for LaTeX, first argument is used
    Macro('LTskip', 'A'),
                    # for LaTeX, first argument is used

    # macro for foreign-language text
    Macro(parms.foreign_lang_mac, 'A', parms.replace_frgn_lang_mac),

    # LAB:EQU:MACROS
    # necessary for correct parsing of equation environments
    # (might hide interpunction, see LAB:EQUATIONS)
    Macro('label', 'A'),
    Macro('mathrlap', 'A', r'\1'),
    Macro('nonumber', ''),
    Macro('notag', ''),
    Macro('qedhere', ''),
)

#   heading macros with optional argument [...]:
#   copy content of {...} and add '.' if not ending with interpunction
#
parms.heading_macros_punct = '!?'
parms.heading_macros = (
    r'chapter\*?',
    r'part\*?',
    r'section\*?',
    r'subsection\*?',
    r'subsubsection\*?',
)

#   theorem environments from package amsthm with optional argument [...]:
#   display a title and text in optional argument as (...) with final dot
#
parms.theorem_environments = (
    'Anmerkung',
    'Beispiel',
    'Definition',
    'Korollar',
    'Nachweis',
    'Proposition',
    'Satz',
)

#   equation environments, partly from LaTeX package amsmath;
#   see comments at LAB:EQUATIONS below
#
#   EquEnv(name, args='', repl='')
#   - args: arguments at \begin, as for Macro()
#   - repl not empty: replace whole environment with this fix text;
#     if the actual content ends with a character from variable
#     parms.mathpunct (ignoring macros from LAB:EQU:MACROS and variable
#     parms.mathspace), then this sign is appended
#
parms.equation_environments = lambda: (
    EquEnv(r'align'),
    EquEnv(r'align\*'),
            # extra pattern with *: safely match begin and end
    EquEnv(r'alignat', args='A'),
    EquEnv(r'alignat\*', args='A'),
    EquEnv(r'displaymath'),
    EquEnv(r'equation'),
    EquEnv(r'equation\*'),
    EquEnv(r'eqnarray'),
    EquEnv(r'eqnarray\*'),
    EquEnv(r'flalign', repl='[Komplex-Formelausdruck]'),
    EquEnv(r'flalign\*', repl='[Komplex-Formelausdruck]'),
)

#   these environments are deleted or replaced completely (with body)
#
#   EnvRepl(name, repl='')
#   - repl: if empty, then suppress creation of blank lines
#
parms.environments = lambda: (
    EnvRepl('table', '[Tabelle].'),
#   EnvRepl('XXX'),
)

#   at the end, we delete all unknown "standard" environment frames;
#   these are environments with options / arguments at \begin{...}
#
#   EnvBegArg(name, args)
#   - args: as for Macro()
#
parms.environments_with_args = lambda: (
    EnvBegArg('figure', 'O'),
    EnvBegArg('minipage', 'A'),
    EnvBegArg('tabular', 'A'),
)

#   a list of 2-tuples for other macros to be replaced
#       [0]: search pattern as regular expression
#       [1]: replacement text
#   utf8_xxx only defined below --> use function
#
parms.misc_replace = lambda: [
    (r'\\Arzela\b', 'Arzela'),
    (r'\\bzw\b', 'bzw.'),
#   (r'\\dphp\b', 'd.' + utf8_nbsp + 'h.'),
#   (r'\\dphpkomma\b', 'd.' + utf8_nbsp + 'h.,'),
            # LT only recognizes missing comma in fully written version
    (r'\\dphp\b', 'das heißt'),
    (r'\\dphpkomma\b', 'das heißt,'),
    (r'\\fpuep\b', 'f.' + utf8_nbsp + 'ü.'),
    (r'\\Han\b', 'Han-Name'),
            # place 'Han-Name' instead of 'Han' in private dictionary
    (r'\\hfill\b', ' '),
    (r'\\ipap\b', 'i.' + utf8_nbsp + 'A.'),
    (r'\\LaTeX\b', 'Latex'),
    (r'\\monthname\b', 'Oktober'),
    (r'\\Necas\b', 'Necas'),
    (r'\\numbera\b', 'B1'),
            # during later checks, we also look for single letters
    (r'\\numberb\b', 'B2'),
    (r'\\numberc\b', 'B3'),
    (r'\\numberd\b', 'B4'),
    (r'\\numbere\b', 'B5'),
    (r'\\numberf\b', 'B6'),
    (r'\\numberi\b', 'N1'),
    (r'\\numberii\b', 'N2'),
    (r'\\numberiii\b', 'N3'),
    (r'\\numberiv\b', 'N4'),
    (r'\\numberv\b', 'N5'),
    (r'\\numberI\b', 'N1'),
    (r'\\numberII\b', 'N2'),
    (r'\\Poincare\b', 'Poincare'),
    (r'\\Sp\b', 'Seite'),
    (r'\\the\\year\b', '2018'),
    (r'\\TBD\b', '[Hilfe]:'),
    (r'\\Thomee\b', 'Thomee'),
    (r'\\upap\b', 'u.' + utf8_nbsp + 'a.'),
    (r'\\usw\b', 'usw.'),
    (r'\\vgl\b', 'vgl.'),
    (r'\\vgV\b(\{\})?', 'v.' + utf8_nbsp + 'g.' + utf8_nbsp + 'V.'),
    (r'\\zB\b', 'z.' + utf8_nbsp + 'B.'),

    # delete '\!', '\-'
    (r'\\[!-]', ''),
    # delete "-
    (r'(?<!\\)"-', ''),     # r'(?<!x)y' matches 'y' not precceded by 'x'

    # "=    ==> -
    (r'(?<!\\)"=', '-'),
    # ~     ==> <space>
    (r'(?<!\\)~', ' '),
    # ---    ==> UTF-8 emdash
    (r'(?<!\\)---', utf8_emdash),
    # --    ==> UTF-8 endash
    (r'(?<!\\)--', utf8_endash),
    # ``    ==> UTF-8 double quotation mark (left)
    (r'(?<!\\)``', utf8_lqq),
    # ''    ==> UTF-8 double quotation mark (right)
    (r'(?<!\\)' + "''", utf8_rqq),
    # "`    ==> UTF-8 german double quotation mark (left)
    (r'(?<!\\)"`', utf8_glqq),
    # "'    ==> UTF-8 german double quotation mark (right)
    (r'(?<!\\)"' + "'", utf8_grqq),
]

#   macro for "plain text" in equation environments;
#   its argument will be copied, see LAB:EQUATIONS below
#
parms.text_macro = 'text'           # LaTeX package amsmath

#   see LAB:ITEMS below
#
parms.keep_item_labels = True

#   message on warnings / errors that should be found by LT
#
parms.warning_error_msg = '\n\nWARNINGORERROR\n\n'

#   further replacements performed below:
#
#   - replacement of $...$ inline math
#   - proof environment
#   - macros for cross references
#   - handling of displayed equations including \[ ... \]
#   - some treatment of \item[...] labels (see LAB:ITEMS)
#   - environments not listed above: \begin{...} and \end{...} deleted
#   - macros not listed:
#     \xxx is deleted, content of a possible braced argument is copied


#######################################################################
#######################################################################

import argparse, re, sys

#   first of all ...
#
def fatal(msg, detail=None):
    sys.stdout.write(parms.warning_error_msg)
    sys.stdout.flush()
    err = '\n*** Internal error: ' + msg + '\n'
    if detail:
        err += detail + '\n'
    raise Exception(err)
def warning(msg, detail=None):
    sys.stdout.write(parms.warning_error_msg)
    sys.stdout.flush()
    err = '\n*** ' + sys.argv[0] + ': warning: ' + msg + '\n'
    if detail:
        err += detail + '\n'
    sys.stderr.write(err)

#   when deleting e.g. environment frames, we do not want to create
#   new empty lines that break sentences for LT;
#   thus also delete line break if rest of line is empty
#
eat_eol =r'(?:[ \t]*(?:(?P<eateol>\n(?!\s))|\n))?'
def eol2space(m):
    # replace the consumed line break with ' ', if next line does not
    # start with space
    if m.group('eateol'):
        return ' '
    return ''


begin_lbr = r'\\begin\s*\{'
end_lbr = r'\\end\s*\{'

#   regular expression for nested {} braces
#   BUG (but error message on overrun): the nesting limit is unjustified
#
max_depth_br = 20
    # maximum nesting depth
def re_braced(max_depth, inner_beg, inner_end):
    atom = r'[^\\{}]|\\.'
    braced = inner_beg + r'\{(?:' + atom + r')*\}' + inner_end
        # (?:...) is (...) without creation of a reference
    for i in range(max_depth - 2):
        braced = r'\{(?:' + atom + r'|' + braced + r')*\}'
    braced = r'(?<!\\)\{((?:' + atom + r'|' + braced + r')*)\}'
        # outer-most (...) for reference at substitutions below
        # '(?<!x)y' matches 'y' not preceded by 'x'
    return braced
braced = re_braced(max_depth_br, '', '')

#   the same for [] brackets
#   BUG (without warning): enclosed {} pairs are not recognized
#
def re_bracketed(max_depth, inner_beg, inner_end):
    atom = r'[^]\\[]|\\.'
    bracketed = inner_beg + r'\[(?:' + atom + r')*\]' + inner_end
    for i in range(max_depth - 2):
        bracketed = r'\[(?:' + atom + r'|' + bracketed + r')*\]'
    bracketed = r'(?<!\\)\[((?:' + atom + r'|' + bracketed + r')*)\]'
    return bracketed
bracketed = re_bracketed(max_depth_br, '', '')

#   regular expression for an environment
#   BUG (but error message on overrun): the nesting limit is unjustified
#
max_depth_env = 10
def re_nested_env(s, max_depth, arg):
    env_begin = begin_lbr + s + r'\}'
    env_end = end_lbr + s + r'\}'
    # important here: non-greedy *? repetition
    env = r'(' + env_begin + r'(?:.|\n)*?' + env_end + r')'
    for i in range(max_depth - 2):
        # important here: non-greedy *? repetition
        env = env_begin + r'(?:(?:' + env + r')|.|\n)*?' + env_end
    env = (env_begin + arg + r'(?P<body>(?:(?:' + env + r')|.|\n)*?)'
                    + env_end)
    return env

#   helpers for "declaration" of macros and environments
#
def Macro(name, args, repl=''):
    return (name, args, repl)
def EquEnv(name, args='', repl=''):
    return (name, args, repl)
def EnvRepl(name, repl=''):
    return (name, repl)
def EnvBegArg(name, args=''):
    return (name, args)
def re_code_args(args, who, s):
    # return regular expression for 'OAA' code
    ret = ''
    for a in args:
        if a == 'A':
            ret += r'\s*' + braced
        elif a == 'O':
            ret += r'(?:\s*' + bracketed + r')?'
        else:
            fatal(who + "('" + s + "',...): bad argument code '" + args + "'")
    return ret

#   these RE match beginning and end of arbitrary "standard" environments,
#   and those with arguments at \begin as declared above
#
re_begin_env, op = '', ''
for (name, args) in parms.environments_with_args():
    expr = begin_lbr + name + r'\}' + re_code_args(args, 'EnvBegArg', name)
    re_begin_env += op + r'(?:' + expr + r')'
    op = r'|'
re_begin_env += op + r'(?:' + begin_lbr + r'[a-zA-Z]+\})'
re_begin_env = r'(?:' + re_begin_env + r')'
re_end_env = end_lbr + r'[a-zA-Z]+' + r'\}'

#   UTF-8 characters;
#   name lookup, if char given e.g. from copy-and-paste:
#       import unicodedata
#       print(unicodedata.name('„'))
#
utf8_endash = '\N{EN DASH}'
utf8_emdash = '\N{EM DASH}'
utf8_lqq = '\N{LEFT DOUBLE QUOTATION MARK}'
utf8_rqq = '\N{RIGHT DOUBLE QUOTATION MARK}'
utf8_glqq = '\N{DOUBLE LOW-9 QUOTATION MARK}'
utf8_grqq = '\N{LEFT DOUBLE QUOTATION MARK}'
utf8_nbsp = '\N{NO-BREAK SPACE}'


#######################################################################
#
#   This wrapper for re.sub() operates a small machinery for
#   line number tracking.
#   Argument text is a 2-tuple.
#       text[0]: the text as string
#       text[1]: list (tuple) with line numbers
#   Return value: tuple (string, number list)
#   As for re.sub(), argument repl may be a callable.
#   Argument extract: function for extracting replacements
#
#   For each line in the current text string, the number list
#   contains the original line number (before any changes took place).
#   On deletion of line breaks, the corresponding entries in the number
#   list are removed. On creation of an additional line, a negative
#   placeholder is inserted in the number list.
#
#   BUG (without warning): for joined lines as e.g. in
#       This i%     (original line number: 5)
#       s a te%     (original line number: 6)
#       st          (original line number: 7)
#   the resulting one-line text 'This is a test' is related to
#   line number 7 (instead of 5+).
#
def mysub(expr, repl, text, flags=0, extract=None):
    if type(text) is not tuple:
        fatal('wrong arg for mysub()')
    txt = text[0]
    numbers = text[1]
    res = ''
    last = 0
    for m in re.finditer(expr, txt, flags=flags):
        t = m.group(0)
        if type(repl) is str:
            r = m.expand(repl)
        else:   # repl is a callable
            r = repl(m)
        res += txt[last:m.start(0)]
        last = m.end(0)
        # lin: first line number of current replacement action
        lin = len(re.findall(r'\n', res))
        res += r
        # number of line breaks in match of original text ...
        nt = len(re.findall('\n', t))
        # ... and in replacement text
        nr = len(re.findall('\n', r))
        if extract:
            extract(r, numbers[lin:lin+nr+1])
        if nt != 0 or nr != 0:
            # ll: original line number of line lin
            ll = abs(numbers[lin])
            numbers = numbers[:lin] + (-ll,) * nr + numbers[lin+nt:]
    return (res + txt[last:], numbers)

def mysearch(expr, text, flags=0):
    if type(text) is not tuple:
        fatal('wrong arg for mysearch()')
    return re.search(expr, text[0], flags=flags)


#######################################################################
#
#   parse command line, set language-dependent variables
#
parser = argparse.ArgumentParser()
parser.add_argument('file', nargs='?')
parser.add_argument('--repl')
parser.add_argument('--nums')
parser.add_argument('--extr')
parser.add_argument('--lang')
cmdline = parser.parse_args()

#   label LAB:LANGUAGE
if not cmdline.lang or cmdline.lang == 'de':
    # replacement for inline formulas;
    # this allows e.g. '... mit einer Konstanten $C$ ...'
    #
    parms.inline_math = '$$'
    # parts in displayed formulas, see LAB:EQUATIONS below;
    # single '§' does not lead to LT warnings on missing
    # interpunction between two equations of an equation array
    #
    parms.display_math = '§§'
    # texts for math operators; default: key None
    parms.mathoptext = {'+': ' plus ', '-': ' minus ',
                        '*': ' mal ', '/': ' durch ',
                        None: ' gleich '}
    # proof environment:
    parms.proof_title = 'Beweis'
    # macro to mark foreign language:
    parms.foreign_lang_mac = 'engl'
    # replacement for this macro:
    parms.replace_frgn_lang_mac = '[englisch]'

elif cmdline.lang == 'en':
    parms.inline_math = 'FBI'
    parms.display_math = 'NSA'
    parms.mathoptext = {'+': ' plus ', '-': ' minus ',
                        '*': ' times ', '/': ' over ',
                        None: ' equal '}
    parms.proof_title = 'Proof'
    parms.foreign_lang_mac = 'foreign'
    parms.replace_frgn_lang_mac = '[foreign]'

else:
    fatal('unrecognized language "' + cmdline.lang
            + '" given in option')

if cmdline.extr:
    cmdline.extr = cmdline.extr.strip(',')
    cmdline.extr_re = cmdline.extr.replace(',', '|')
    cmdline.extr_list = cmdline.extr.split(',')
else:
    cmdline.extr_list = []


#######################################################################
#
#   read complete input into 'text'
#
if cmdline.file:
    text = open(cmdline.file).read()
else:
    text = sys.stdin.read()

#   the initial list of line numbers: in fact "only" a tuple
#
numbers = tuple(range(1, len(re.findall(r'\n', text)) + 1))

#   for mysub():
#   text becomes a 2-tuple of text string and number list
#
text = (text, numbers)

#   first replace \\ and \\[...] by \newline; \newline is needed for
#   parsing of equation environments below
#   --> afterwards, no double \ anymore
#
text = mysub(r'\\\\(\[[\w.]+\])?', r'\\newline', text)

#   then remove % comments
#   - line beginning with % is completely removed
#
text = mysub(r'^[ \t]*%.*\n', '', text, flags=re.M)

#   - if no space in front of first unescaped %:
#     join current and next lines (except after \\ alias \newline)
#
text = mysub(r'^(([^\n\\%]|\\.)*[^ \t\n\\%])(?<!\\newline)%.*\n',
                r'\1', text, flags=re.M)
    # r'(?<!x)y' matches 'y' not preceeded by 'x'
    # the previous replacement does not join lines on '\%%'
    # --> re-try
text = mysub(r'^(([^\n\\%]|\\.)*\\%)%.*\n', r'\1', text, flags=re.M)

#   - "normal case": just remove rest of line, keeping the line break
#
text = mysub(r'(?<!\\)%.*$', '', text, flags=re.M)


#   check nesting limits for braces, brackets, and environments
#
for m in re.finditer(re_braced(max_depth_br + 1, '(', ')'), text[0]):
    if m.group(2):
        # inner-most {} braces did match
        fatal('maximum nesting depth for {} braces exceeded,'
                + ' max_depth_br=' + str(max_depth_br), m.group(0))
for m in re.finditer(re_bracketed(max_depth_br + 1, '(', ')'), text[0]):
    if m.group(2):
        fatal('maximum nesting depth for [] brackets exceeded,'
                + ' max_depth_br=' + str(max_depth_br), m.group(0))

for env in (
    parms.equation_environments()
    + parms.environments()
):
    expr = re_nested_env(env[0], max_depth_env + 1, '')
    for m in re.finditer(expr, text[0]):
        if m.group(2):
            fatal('maximum nesting depth for environments exceeded,'
                    + ' max_depth_env=' + str(max_depth_env), m.group(0))


#######################################################################
#
#   replacements: collected in list actions
#   list of 2-tuples:
#       [0]: search pattern as regular expression
#       [1]: replacement text
#
actions = parms.misc_replace()

for (name, repl) in parms.environments():
    env = re_nested_env(name, max_depth_env, '')
    if repl:
        actions += [(env, repl)]
    else:
        actions += [(env + eat_eol, eol2space)]

def f(m):
    txt = m.group(2)
    if txt and txt[-1] not in parms.heading_macros_punct:
        txt += '.'
    return txt
for s in parms.heading_macros:
    actions += [(
        r'\\' + s + r'\s*(?:' + bracketed + r')?\s*' + braced,
        f
    )]

for s in parms.theorem_environments:
    thm_text = s.capitalize()
    actions += [
        # first try with option ...
        (begin_lbr + s + r'\}\s*' + bracketed, thm_text + r' 1.2 (\1).'),
        # ... and then without
        (begin_lbr + s + r'\}', thm_text + r' 1.2.'),
        # delete \end{...}
        (end_lbr + s + r'\}' + eat_eol, eol2space),
    ]

# replace $...$ by variable parms.inline_math
# BUG (with warning): fails e.g. on $x \text{ for $x>0$}$
#
def f(m):
    if re.search(r'(?<!\\)\$', m.group(1)):
        warning('"$" in {} braces (macro argument?): not properly handled',
                    m.group(0))
    return parms.inline_math
actions += [(r'(?<!\\)\$((?:' + braced + r'|[^\\$]|\\.)*)\$', f)]

#   proof environment with optional [...]:
#   extract text in [...] and append '.'
#
actions += [
    # first try version with option ...
    (begin_lbr + r'proof\}\s*' + bracketed, r'\1.'),
    # ... then without
    (begin_lbr + r'proof\}', parms.proof_title + '.'),
    (end_lbr + r'proof\}' + eat_eol, eol2space)
]

#   replace \cite, \eqref, \ref, \pageref
#
actions += [
    (r'\\cite\s*' + bracketed + r'\s*' + braced, r'[1, \1]'),
    (r'\\cite\s*' + braced, '[1]'),
    (r'\\eqref\s*' + braced, '(7)'),
    (r'\\ref\s*' + braced, '13'),
    (r'\\pageref\s*' + braced, '99')
]

#   now perform the collected replacement actions
#
for (expr, repl) in actions:
    text = mysub(expr, repl, text, flags=re.M)

#   treat macros listed above
#
for (name, args, repl) in parms.the_macros():
    if name in cmdline.extr_list:
        continue
    expr = r'\\' + name
    if name[-1].isalpha():
        expr += r'\b'
    expr += re_code_args(args, 'Macro', name)
    for m in re.finditer(r'\\(\d)', repl):
        n = int(m.group(1))
        if n < 1 or n > len(args):
            fatal('inavlid "\\' + m.group(1) + '" in replacement for "'
                        + name + '"')
    if not repl:
        text = mysub(expr + eat_eol, eol2space, text)
    else:
        while mysearch(expr, text):
            text = mysub(expr, repl, text)


##################################################################
#
#   LAB:EQUATIONS: replacement of equation environments
#
##################################################################

##  example with --lang en:
#
#       Thus,
#       %
#       \begin{align}
#       \mu &= f(x) \quad\text{for all } \mu\in\Omega, \notag \\
#       x   &= \begin{cases}
#               0 & \text{ for} \ y>0, \\
#               1 & \text{ in case} y\le 0.
#                   \end{cases}     \label{lab}
#       \end{align}
#
##  becomes:
#
#       Thus,
#         NSA  equal NSA for all NSA, 
#         NSA  equal NSA  for NSA, 
#         NSA  in caseNSA. 
#
##

#   - argument of \text{...} (variable parms.macro_text) is reproduced
#     without change
#
#   - intermediate math parts are replaced by '§§', see variable
#     parms.display_math
#     (§§ is suitable, since it avoids warnings, if an equation starting
#     with §§ follows text ending with $$)
#   - interpunction signs (see variable parms.mathpunct) at end of a
#     math part are appended to §§
#     (missing or wrong interpunction then is detected by LT)
#   - relational operators at beginning of a math part are prepended
#     as ' gleich §§', if math part is not first on line ('&' is a part);
#     other operators like +, -, *, / are prepended e.g. as ' minus §§';
#     see variables parms.mathop and parms.mathoptext
#     (missing operators then are detected by LT)
#
#   - math space (see variable parms.mathspace) like \quad
#     is replaced by ' '

#   Assumptions:
#   - \\ has been changed to \newline
#   - macros from LAB:EQU:MACROS already have been deleted
#   - \text{...} has been resolved not yet
#   - mathematical space as \; and \quad (variable parms.mathspace)
#     is still present

parms.mathspace = r'(?:\\[ ,;:]|\\q?quad\b)'
parms.mathop = (
    r'\+|-|\*|/'
    + r'|=|<|>|(?<!\\):=?'          # accept ':=' and ':'
    + r'|\\[gl]eq?\b'
    + r'|\\su[bp]set(?:eq)?\b'
    + r'|\\Leftrightarrow\b'
    + r'|\\to\b'
    + r'|\\stackrel\s*' + braced + r'\s*\{=\}'
    + r'|\\c[au]p\b'
)
parms.mathpunct = r'(?:(?<!\\)[;,]|\.)'

#   replace a math part by suitable raw text
#
def math2txt(txt, first_on_line):
    txt = txt.strip()
    if not txt:
        return ''

    # check for leading operator, possibly after mathspace;
    # there also might be a '{}' for making e.g. '-' binary
    m = re.match(r'(' + parms.mathspace + r'|\{\}|\s)*'
                    + r'(' + parms.mathop + ')', txt)
    if m and not first_on_line:
        # starting with operator, not first on current line
        pre = parms.mathoptext.get(m.group(2), parms.mathoptext[None])
        txt = txt[m.end(0):].strip()
    else:
        # check for leading mathspace
        m = re.match(r'((' + parms.mathspace + r'\s*)+)', txt)
        if m:
            pre = ' '
            txt = txt[m.end(0):].strip()
        else:
            pre = ''

    # check for trailing mathspace
    m = re.search(r'(\s*' + parms.mathspace + r')+\Z', txt)
    if m:
        post = ' '
        txt = txt[:m.start(0)].strip()
    else:
        post = ''
    if not txt:
        return pre + post

    # check for trailing punctuation
    m = re.search(r'(' + parms.mathpunct + r')\Z', txt)
    if not m:
        return pre + parms.display_math + post
    if txt == m.group(1):
        return pre + txt + post
    return pre + parms.display_math + m.group(1) + post

#   split a section between & delimiters into \text{...} and math parts
#
def split_sec(txt, first_on_line):
    last = 0
    res = ''
    # iterate over \text parts
    for m in re.finditer(r'\\' + parms.text_macro + r'\s*' + braced, txt):
        # math part between last and current \text
        res += math2txt(txt[last:m.start(0)], first_on_line)
        # content of \text{...}
        res += m.group(1)
        last = m.end(0)
        first_on_line = False
    # math part after last \text
    res += math2txt(txt[last:], first_on_line)
    return res

#   parse the text of an equation environment
#
def parse_equ(equ):
    # first resolve sub-environments (e.g. cases) in order
    # to see interpunction
    equ = re.sub(re_begin_env, '', equ)
    equ = re.sub(re_end_env, '', equ)

    # then split into lines delimited by \newline
    # BUG (with warning for braced macro arguments):
    # repl_line() and later repl_sec() may fail if \\ alias \newline
    # or later & are argument of a macro
    #
    for f in re.finditer(braced, equ):
        if re.search(r'\\newline|(?<!\\)&', f.group(1)):
            warning('"\\\\" or "&" in {} braces (macro argument?):'
                        + ' not properly handled',
                        re.sub(r'\\newline\b', r'\\\\', equ))
            break
    # important: non-greedy *? repetition
    line = r'((.|\n)*?)(\\newline\b|\Z)'
    # return replacement for RE line
    def repl_line(m):
        # finally, split line into sections delimited by '&'
        # important: non-greedy *? repetition
        sec = r'((.|\n)*?)((?<!\\)&|\Z)'
        first_on_line = True
        def repl_sec(m):
            nonlocal first_on_line
            # split this section into math and text parts
            # BUG (without warning):
            # we assume that '&' always creates white space
            ret = split_sec(m.group(1), first_on_line) + ' '
            first_on_line = False
            return ret
        return '  ' + re.sub(sec, repl_sec, m.group(1)) + '\n'

    return re.sub(line, repl_line, equ)

#   replace equation environments listed above
#
for (name, args, replacement) in parms.equation_environments():
    if not replacement:
        re_args = re_code_args(args, 'EquEnv', name)
        expr = re_nested_env(name, max_depth_env, re_args) + eat_eol
        text = mysub(expr, lambda m: parse_equ(m.group('body')), text)
        continue
    # environment with fixed replacement and added interpunction
    env = re_nested_env(name, max_depth_env, '')
    def f(m):
        txt = parse_equ(m.group('body')).strip()
        s = replacement
        m = re.search(r'(' + parms.mathpunct + r')\Z', txt)
        if m:
            s += m.group(1)
        return s
    text = mysub(env, f, text)

#   replace \[ ... \] displayed equation
#
text = mysub(r'\\\[((.|\n)*?)\\\]' + eat_eol,
                lambda m: parse_equ(m.group(1)), text)
        # important: non-greedy *? repetition


#######################################################################
#
#   final clean-up
#
#######################################################################

#   delete remaining environments outside of equations,
#   possibly with argument and option at \begin{...}
#
text = mysub(re_begin_env + eat_eol, eol2space, text)
text = mysub(re_end_env + eat_eol, eol2space, text)

#   replace space macros
#
text = mysub(parms.mathspace, ' ', text)

#   LAB:ITEMS
#   item lists may pose problems with interpunction checking
#   - one can simply remove the \item[...] label
#   - one can look backwards in the text and repeat a present interpunction
#     sign after the item label
#       --> this also checks text in the label
#   - this should be done after removal of \begin{itemize},
#     but before removal of \item
#
if parms.keep_item_labels:
    # first try with preceding interpunction [.,;:] ...
    text = mysub(r'(((?<!\\)[.,;:])\s*)\\item\s*' + bracketed,
                    r'\1\3\2', text)
    # ... otherwise simply extract the text in \item[...]
    text = mysub(r'\\item\s*' + bracketed, r'\1', text)
else:
    text = mysub(r'\\item\s*' + bracketed + eat_eol, eol2space, text)
# finally, items without [...]
text = mysub(r'\\item\b' + eat_eol, eol2space, text)

#   delete remaining \xxx macros unless given in --extr option;
#   if followed by braced argument: copy its content
#
if cmdline.extr:
    re_macro = r'\\(?!(?:' + cmdline.extr_re + r'))[a-zA-Z]+'
        # 'x(?!y)' matches 'x' not followed by 'y'
else:
    re_macro = r'\\[a-zA-Z]+'
re_macro_arg = re_macro + r'\s*' + braced
while mysearch(re_macro_arg, text):
    # macros with braced argument might be nested
    text = mysub(re_macro_arg, r'\1', text)
text = mysub(r'\\newline\b', '', text)
text = mysub(re_macro + eat_eol, eol2space, text)


##################################################################
#
#   LAB:SPELLING
#
##################################################################

#   perform replacements in file of option --repl
#   line syntax:
#   - '#: comment till end of line
#   - the words (delimiter: white space) in front of first separated '&'
#     are replaced by the words following this '&'
#   - if no replacement given: just delete phrase
#   - space in phrase to be replaced is arbitrary (expression r'\s+')
#
if cmdline.repl:
    for lin in open(cmdline.repl):
        i = lin.find('#')
        if i >= 0:
            lin = lin[:i]
        lin = lin.split()

        t = s = ''
        for i in range(len(lin)):
            if lin[i] == '&':
                break
            t += s + re.escape(lin[i])  # protect e.g. '.' and '$'
            s = r'\s+'
        if not t:
            continue

        if t[0].isalpha():
            t = r'\b' + t       # require word boundary
        if t[-1].isalpha():
            t = t + r'\b'
        r = s = ''
        for i in range(i + 1, len(lin)):
            r += s + lin[i]
            s = ' '
        text = mysub(t, r, text)


##################################################################
#
#   output of results
#
##################################################################

#   on option --extr: only print arguments of these macros
#
if cmdline.extr:
    if cmdline.nums:
        fn = open(cmdline.nums, mode='w')
    def extr(t, n):
        global extract_list
        extract_list += [(t,n)]
    extract_list = []
    mysub(r'\\(?:' + cmdline.extr_re + r')\s*' + braced,
            r'\1', text, extract=extr)

    for (txt, nums) in extract_list:
        txt = txt.rstrip('\n') + '\n\n'
        sys.stdout.write(txt)
        if not cmdline.nums:
            continue
        for i in range(len(re.findall(r'\n', txt))):
            if i < len(nums):
                s = str(abs(nums[i]))
                if nums[i] < 0:
                    s += '+'
            else:
                s = '?'
            fn.write(s + '\n')
    exit()

#   if braces {...} did remain somewhere: delete
#
while mysearch(braced, text):
    text = mysub(braced, r'\1', text)


#   write text to stdout
#
txt = text[0]
numbers = text[1]
sys.stdout.write(txt)

#   if option --nums given: write line number information
#
if cmdline.nums:
    f = open(cmdline.nums, mode='w')
    for n in numbers:
        if n > 0:
            f.write(str(n) + '\n')
        else:
            f.write(str(-n) + '+\n')

