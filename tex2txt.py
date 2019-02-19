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

#######################################################################
#
#   Python3:
#   Extract raw text from LaTeX file, write result to standard output
#
#   Usage and main operations:
#   - see README
#
#   Principle of operation:
#   - read complete input text into a string, then make replacements
#   - replacements are performed via the "re-implementation" mysub() of
#     re.sub() in order to observe deletion and inclusion of line breaks
#   - in order to treat nested braces / brackets and some nested
#     environments, we construct regular expressions by iteration;
#     maximum recognized nesting depth (and thus length of these expressions)
#     is controlled by the variables parms.max_depth_br and
#     parms.max_depth_env
#
#   Bugs:
#   - parsing with regular expressions is fun, but limited; as the
#     replacement argument of re.sub() may be a callable, one can plug in
#     some programming, however
#   - several related shortcomings are marked with BUG (for some
#     of them, warnings are generated)
#   - severe general problem: resolution of macros not in the order of
#     TeX (strictly left to right in the text);
#     work-arounds with hacks mark_begin_env and mark_deleted are used to
#     avoid consumption of too much space by macros without argument
#
#
#                                   Matthias Baumann, 2018-2019
#

class Aux: pass
parms = Aux()

#   these are macros with tailored treatment;
#   replacement only if not given in option --extr
#
#   Simple(name, repl=''):
#   abbreviation for Macro(name, '', repl)
#
#   Macro(name, args, repl=''):
#   args:
#       - A: mandatory {...} argument
#       - O: optional [...] argument
#       - P: mandatory [...] argument, see for instance \cite
#   repl:
#       - replacement pattern, r'\d' (d: single digit) extracts text
#         from position d in args (counting from 1)
#       - other escape rules: see escape handling at myexpand() below;
#         e.g., include a single backslash: repl=r'...\\...'
#       - inclusion of % only as escaped version r'\\%' accepted, will be
#         resolved to % at the end by resolve_escapes()
#       - inclusion of double backslash \\ and replacement ending with \
#         will be rejected
#
#   REMARKS:
#       - if a macro does not find its mandatory argument(s) in the text,
#         it is treated as unknown and can be seen with option --unkn
#       - if refering to an optional argument, e.g.
#               Macro('xxx', 'OA', r'\1\2'),
#         Python version of at least 3.5 is required (non-matched group
#         yields empty string); otherwise re module may raise exceptions
#
#
parms.project_macros = lambda: (

    # our LaTeX macro: \newcommand{\comment}[1]{}
    Macro('comment', 'A'),
    # non-breaking space in acronyms to avoid LT warning
    # our LaTeX macro: \newcommand{\zB}{z.\,B.\ }
    Simple('zB', 'z.~B. '),
    # Simple('zB', r'z.\\,B. '),

    # see LAB:VERBATIM below
    # Macro('verb', 'A', '[verbatim]'),
    Macro('verb', 'A', r'\1'),
    # Macro(r'verb\*', 'A', '[verbatim*]'),
    Macro(r'verb\*', 'A', r'\1'),

    # macros to suppress rare LT warnings by altering the LaTeX text
    Macro('LTadd', 'A', r'\1'),
                    # for LaTeX, argument is ignored
    Macro('LTalter', 'AA', r'\2'),
                    # for LaTeX, first argument is used
    Macro('LTskip', 'A'),
                    # for LaTeX, first argument is used

) + defs.project_macros


#   BUG: quite probably, some macro is missing here ;-)
#
parms.system_macros = lambda: (

    Macro('caption', 'OA', r'\2'),
    Macro('cite', 'A', '[1]'),
    Macro('cite', 'PA', r'[1, \1]'),
    Macro('color', 'A'),
    Macro('colorbox', 'AA', r'\2'),
    Macro('documentclass', 'OA'),
    Macro('eqref', 'A', '(7)'),
    Macro('fcolorbox', 'AAA', r'\3'),
    Macro('footnote', 'OA', '5'),
    Macro('footnotemark', 'O', '5'),
    Macro('footnotetext', 'OA'),
    Macro('framebox', 'OOA', r'\3'),
    Simple('hfill', ' '),
    Macro(r'hspace\*?', 'A'),
    Macro('includegraphics', 'OA'),
    Macro('input', 'A'),
    Macro('newcommand', 'AOA'),
    Simple('newline', ' '),
    Macro('pageref', 'A', '99'),
    Macro('ref', 'A', '13'),
    Macro('texorpdfstring', 'AA', r'\1'),
    # \textasciicircum: defined below
    # \textasciitilde: defined below
    # \textbackslash: defined below
    Macro('textcolor', 'AA', r'\2'),
    Macro('usepackage', 'OA'),
    Macro(r'vspace\*?', 'A'),

    Simple('ss', 'ß'),
    Simple('S', '§'),
    Simple('l', 'ł'),
    Simple('L', 'Ł'),
    Simple('aa', 'å'),
    Simple('AA', 'Å'),
    Simple('ae', 'æ'),
    Simple('AE', 'Æ'),
    Simple('oe', 'œ'),
    Simple('OE', 'Œ'),
    Simple('o', 'ø'),
    Simple('O', 'Ø'),

    # macro for foreign-language text
    Macro(parms.foreign_lang_mac, 'A', parms.replace_frgn_lang_mac),

    # LAB:EQU:MACROS
    # necessary for correct parsing of equation environments
    # (might hide interpunction, see LAB:EQUATIONS)
    Macro('label', 'A'),
    Macro('mathrlap', 'A', r'\1'),
    Simple('nonumber'),
    Simple('notag'),
    Simple('qedhere'),

) + defs.system_macros


#   heading macros with optional argument [...]:
#   copy content of {...} and add '.' if not ending with interpunction
#
parms.heading_macros_punct = '!?'
        # do not add '.' if ending with that;
        # title mistakenly ends with '.' --> '..' will lead to LT warning
parms.heading_macros = lambda: (

    r'chapter\*?',
    r'part\*?',
    r'section\*?',
    r'subsection\*?',
    r'subsubsection\*?',

) + defs.heading_macros


#   equation environments, partly from LaTeX package amsmath;
#   see comments at LAB:EQUATIONS below
#
#   EquEnv(name, args='', repl='')
#   - args: arguments at \begin, as for Macro()
#   - repl not empty: replace whole environment with this fix text;
#     if the actual content ends with a character from variable
#     parms.mathpunct (ignoring macros from LAB:EQU:MACROS and variable
#     parms.mathspace), then this sign is appended
#   - repl: plain string, no backslashs accepted
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

) + defs.equation_environments


#   these environments are deleted or replaced completely (with body)
#
#   EnvRepl(name, repl='')
#   - repl: plain string, no backslashs accepted
#
parms.environments = lambda: (

    EnvRepl('table', '[Tabelle].'),
#   EnvRepl('comment'),
#   EnvRepl('verbatim', '[verbatim]'),
#   EnvRepl(r'verbatim\*', '[verbatim*]'),

) + defs.environments


#   at the end, we delete all unknown "standard" environment frames;
#   here are environments with options / arguments at \begin{...},
#   or with a replacement text for \begin{...}
#
#   EnvBegin(name, args='', repl='')
#   - args: as for Macro()
#   - repl: as for Macro()
#
parms.environment_begins = lambda: (

    EnvBegin('figure', 'O'),
    EnvBegin('minipage', 'A'),
    EnvBegin('tabular', 'A'),
    EnvBegin('verbatim'),       # only, if not in parms.environments
    EnvBegin(r'verbatim\*'),    # only, if not in parms.environments

    # proof: try replacement with option, and only after that without
    EnvBegin('proof', 'P', r'\1.'),
    EnvBegin('proof', '', parms.proof_title + '.'),

    # theorems: same order as for proof
    ) + tuple(EnvBegin(env, 'P', title + r' 1.2 (\1).')
                    for (env, title) in parms.theorem_environments()
    ) + tuple(EnvBegin(env, '', title + ' 1.2.')
                    for (env, title) in parms.theorem_environments()

) + defs.environment_begins


#   theorem environments from package amsthm with optional argument [...]:
#   display a title and text in optional argument as (...) with final dot
#
parms.theorem_environments = lambda: (

    # (environment name, text title)
    ('Anmerkung', 'Anmerkung'),
    ('Beispiel', 'Beispiel'),
    ('Definition', 'Definition'),
    ('Korollar', 'Korollar'),
    ('Nachweis', 'Nachweis'),
    ('Proposition', 'Proposition'),
    ('Satz', 'Satz'),

    ('corollary', 'Corollary'),
    ('definition', 'Definition'),
    ('example', 'Example'),
    ('lemma', 'Lemma'),
    ('proposition', 'Proposition'),
    ('remark', 'Remark'),
    ('theorem', 'Theorem'),

) + defs.theorem_environments


#   a list of 2-tuples for other things to be replaced
#       [0]: search pattern as regular expression
#       [1]: replacement text
#   see also resolve_escapes() and LAB:SMALLMACS below
#
#   ATTENTION:
#   - prepend mark_deleted, if replacement may evaluate to empty string
#     or white space
#   - do not use replacement that
#       - ends with a backslash
#       - may insert a double backslash
#       - may instert an unescaped % sign
#     (see comments at Macro() above and compare checks in re_code_args())
#
parms.misc_replace = lambda: (

    # \[    ==> ... 
    (r'\\\[', r'\\begin{equation*}'),
    # \]    ==> ... 
    (r'\\\]', r'\\end{equation*}'),

    # ---    ==> UTF-8 emdash
    (r'(?<!\\)---', utf8_emdash),   # (?<!x)y matches y not preceded by x
    # --    ==> UTF-8 endash
    (r'(?<!\\)--', utf8_endash),
    # ``    ==> UTF-8 double quotation mark (left)
    (r'(?<!\\)``', utf8_lqq),
    # ''    ==> UTF-8 double quotation mark (right)
    (r'(?<!\\)' + "''", utf8_rqq),

) + parms.misc_replace_lang() + defs.misc_replace


parms.misc_replace_de = lambda: (

    # "=    ==> -
    (r'(?<!\\)"=', '-'),
    # "`    ==> UTF-8 german double quotation mark (left)
    (r'(?<!\\)"`', utf8_glqq),
    # "'    ==> UTF-8 german double quotation mark (right)
    (r'(?<!\\)"' + "'", utf8_grqq),
    # "-    ==> delete
    (r'(?<!\\)"-', mark_deleted),

)

parms.misc_replace_en = lambda: (
)


#   macro for "plain text" in equation environments;
#   its argument will be copied, see LAB:EQUATIONS below
#
parms.text_macro = 'text'           # LaTeX package amsmath


#   maximum nesting depths
#
parms.max_depth_br = 20         # for {} braces and [] brackets
parms.max_depth_env = 10        # for environments of the same type


#   see LAB:ITEMS below
#
parms.keep_item_labels = True
parms.default_item_lab = ''


#   message on warnings / errors that should be found by LT;
#   don't include line breaks: will disrupt line number tracking
#
parms.warning_error_msg = ' WARNINGORERROR '


#   LAB:LANGUAGE
#
def set_language_de():

    # properties of these replacements for inline formulas:
    #   - no need to add to LT dictionary
    #   - absent leading / trailing space causes spelling erros
    #   - LT accepts e.g. 'mit einer Konstanten $C$ folgt', 'für alle $x$',
    #     'für ein $x$'
    #   - LT recognizes mistakes like 'die $\epsilon$-Argument'
    #   - word repetitions are detected
    #   - resulting text can be checked for single letters (German)
    # other variant: AInlA, BInlB, ... (but has to be added to dictionary)
    parms.inline_math = ('I1I', 'I2I', 'I3I', 'I4I', 'I5I', 'I6I')
    # parms.inline_math = ('AInlA', 'BInlB', 'CInlC',
    #                       'DInlD', 'EInlE', 'FInlF')

    # replacements for math parts in displayed formulas
    parms.display_math = ('D1D', 'D2D', 'D3D', 'D4D', 'D5D', 'D6D')
    # parms.display_math = ('ADsplA', 'BDsplB', 'CDsplC',
    #                       'DDsplD', 'EDsplE', 'FDsplF')

    # LAB:CHECK_EQU_REPLS
    # this check is important if replacements had to be added to dictionary
    parms.check_equation_replacements = True

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

    # language-dependent part of parms.misc_replace
    parms.misc_replace_lang = parms.misc_replace_de


def set_language_en():
    # see comments in set_language_de()
    parms.inline_math = ('B', 'C', 'D', 'E', 'F', 'G')
    parms.display_math = ('U', 'V', 'W', 'X', 'Y', 'Z')
    parms.check_equation_replacements = False
    parms.mathoptext = {'+': ' plus ', '-': ' minus ',
                        '*': ' times ', '/': ' over ',
                        None: ' equal '}
    parms.proof_title = 'Proof'
    parms.foreign_lang_mac = 'foreign'
    parms.replace_frgn_lang_mac = '[foreign]'
    parms.misc_replace_lang = parms.misc_replace_en


#   further replacements performed below:
#
#   - translation of $$...$$ to equation* environment
#   - replacement of $...$ inline math
#   - macros \textbackslash, \textasciicircum, \textasciitilde
#   - treatment of text-mode accents
#   - handling of displayed equations
#   - some treatment of \item[...] labels
#   - environments not listed above: \begin{...} and \end{...} deleted
#   - macros not listed:
#     \xxx is deleted, content of a possible braced argument is copied


#######################################################################
#######################################################################
#
#   Implementation part
#
#######################################################################
#######################################################################

import argparse
import re
import sys
import unicodedata

#   first of all ...
#
def fatal(msg, detail=None):
    sys.stdout.write(parms.warning_error_msg)
    sys.stdout.flush()
    err = '\n*** Internal error:\n' + msg + '\n'
    if detail:
        err += detail + '\n'
    sys.stderr.write(err)
    exit(1)
def warning(msg, detail=None):
    sys.stdout.write(parms.warning_error_msg)
    sys.stdout.flush()
    err = '\n*** ' + sys.argv[0] + ': warning:\n' + msg + '\n'
    if detail:
        err += detail + '\n'
    sys.stderr.write(err)
def myopen(f, mode='r'):
    try:
        return open(f, mode=mode)
    except:
        fatal('could not open file "' + f + '"')

#   for internal marks: cannot apear in text after removal of % comments
#
mark_internal_pre = '%%%%'      # CROSS-CHECK with re_code_args()
mark_internal_post = '%%'       # CROSS-CHECK with re_code_args()

#   when deleting macros or environment frames, we do not want to create
#   new empty lines that break sentences for LT;
#   thus replace deleted text with tag in mark_deleted which is removed
#   at the end;
#   this also protects space behind a macro already resolved from being
#   consumed by a macro in front
#
mark_deleted = mark_internal_pre + 'D' + mark_internal_post

#   after resolution of an environment frame, we leave this mark;
#   it will avoid that a preceding macro that is treated later will
#   consume too much space;
#   see also variable skip_space_macro
#
mark_begin_env = r'\begin{' + mark_internal_pre + r'}'
mark_end_env = r'\end{' + mark_internal_pre + r'}'
# if replacement argument of ..sub():
mark_begin_env_sub = r'\\begin{' + mark_internal_pre + r'}'
mark_end_env_sub = r'\\end{' + mark_internal_pre + r'}'

#   internal representation of double backslash \\
#
mark_linebreak = mark_internal_pre + 'L' + mark_internal_post

#   mark for internal representation of a single verbatim character,
#   will be resolved only at output by resolve_escapes()
#
mark_verbatim = (mark_internal_pre + 'V', 'V' + mark_internal_post)
mark_verbatim_tmp = ('____V', 'V__')    # before removal of % comments

#   space allowed inside of current paragraph, at most one line break
#
skip_space = r'(?:[ \t]*\n?[ \t]*)'

#   regular expression for nested {} braces
#   BUG (but error message on overrun): the nesting limit is unjustified
#
def re_braced(max_depth, inner_beg, inner_end):
    atom = r'[^\\{}]|\\.|\\\n'
    braced = inner_beg + r'\{(?:' + atom + r')*\}' + inner_end
        # (?:...) is (...) without creation of a reference
    for i in range(max_depth - 2):
        braced = r'\{(?:' + atom + r'|' + braced + r')*\}'
    braced = r'(?<!\\)\{((?:' + atom + r'|' + braced + r')*)\}'
        # outer-most (...) for reference at substitutions below
        # '(?<!x)y' matches 'y' not preceded by 'x'
    return braced
braced = re_braced(parms.max_depth_br, '', '')
sp_braced = skip_space + braced

#   the same for [] brackets
#   BUG (without warning): enclosed {} pairs are not recognized
#
def re_bracketed(max_depth, inner_beg, inner_end):
    atom = r'[^]\\[]|\\.|\\\n'
    bracketed = inner_beg + r'\[(?:' + atom + r')*\]' + inner_end
    for i in range(max_depth - 2):
        bracketed = r'\[(?:' + atom + r'|' + bracketed + r')*\]'
    bracketed = r'(?<!\\)\[((?:' + atom + r'|' + bracketed + r')*)\]'
    return bracketed
bracketed = re_bracketed(parms.max_depth_br, '', '')
sp_bracketed = skip_space + bracketed

#   regular expression for an environment
#   BUG (but error message on overrun): the nesting limit is unjustified
#
begin_lbr = r'\\begin' + skip_space + r'\{'
end_lbr = r'\\end' + skip_space + r'\{'
def re_nested_env(s, max_depth, arg):
    env_begin = begin_lbr + s + r'\}'
    env_end = end_lbr + s + r'\}'
    # important here: non-greedy *? repetition
    env = r'(?P<inner>' + env_begin + r'(?:.|\n)*?' + env_end + r')'
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
def Simple(name, repl=''):
    return (name, '', repl)
def EquEnv(name, args='', repl=''):
    return (name, args, repl)
def EnvRepl(name, repl=''):
    return (name, repl)
def EnvBegin(name, args='', repl=''):
    return (name, args, repl)
def re_code_args(args, repl, who, s, no_backslash=False):
    # return regular expression for 'OAA' code in args,
    # do some checks for replacment string repl
    # CROSS-CHECK with mark_internal_pre und mark_internal_post
    ret = ''
    for a in args:
        if a == 'A':
            ret += sp_braced
        elif a == 'O':
            ret += r'(?:' + sp_bracketed + r')?'
        elif a == 'P':
            ret += sp_bracketed
        else:
            fatal(who + "('" + s + "',...): bad argument code '" + args + "'")
    def err(e):
        fatal('error in replacement for ' + who + "('" + s + "', ...):\n" + e)
    if no_backslash and repl.count('\\'):
        err('no backslashs allowed')
    for m in re.finditer(r'(?<!\\)(?:\\\\)*\\(\d)', repl):
        # avoid exceptions from re module
        n = int(m.group(1))
        if n < 1 or n > len(args):
            err('invalid reference "\\' + m.group(1) + '"')
    if re.search(r'(?<!\\\\)%', repl):
        # ensure that mark_linebreak and mark_deleted do work
        err(r"please use r'\\%' to insert escaped percent sign")
    if repl.endswith('\\') or repl.count('\\\\\\\\'):
        # ensure that double backslashs do not appear in text
        err('backslash at end or insertion of double backslash')
    return ret

#   this is an eligible name of a "normal" macro
#
macro_name = r'[a-zA-Z]+'

#   the expression r'\\to\b' does not work as necessary for \to0
#   --> use r'\\to' + end_mac
#
end_mac = r'(?![a-zA-Z])'

#   space that can be consumed after a macro without argument:
#   only consume line break, if non-space on next line found,
#   and if line break not in front of a \begin for environment
#
skip_space_macro = (r'(?:[ \t]*(?:\n(?=[ \t]*\S)(?![ \t]*\\begin'
                            + end_mac + r'))?[ \t]*)')

#   these RE match beginning and end of arbitrary "standard" environments
#
environ_name = r'[^\\{}\n]+'
re_begin_env = begin_lbr + environ_name + r'\}'
re_end_env = end_lbr + environ_name + r'\}'

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
utf8_nnbsp = '\N{NARROW NO-BREAK SPACE}'

#   create internal verbatim representation of a string
#
def verbatim(s, mark, ast):
    ret = ''
    for c in s:
        if ast and c == ' ':
            c = '⊔'
        ret += mark[0] + str(ord(c)) + mark[1]
        if c == '\n':
            # for line number tracking, compare resolve_escapes()
            ret += c
    return ret


#######################################################################
#
#   This "re-implementation" of re.sub() operates a small machinery for
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
def mysub(expr, repl, text, flags=0, extract=None):
    if type(text) is not tuple:
        fatal('wrong arg for mysub()')
    txt = text[0]
    numbers = text[1]
    res = ''
    last = 0
    for m in re.finditer(expr, txt, flags=flags):
        t = m.group(0)
        if not t:
            continue
        if type(repl) is str:
            ex = myexpand(m, repl, text)
        else:
            ex = repl(m)
        if type(ex) is tuple:
            # replacement contains line number information
            r = ex[0]
            nums2 = ex[1]
        else:
            r = ex
            nums2 = None
        res += txt[last:m.start(0)]
        last = m.end(0)
        # lin: first line number of current replacement action
        lin = res.count('\n')
        nt = t.count('\n')
        nr = r.count('\n')
        if extract:
            extract(r, numbers[lin:lin+nr+1])
        if nt != 0 or nr != 0:
            # ll: original line number of line lin
            ll = abs(numbers[lin])
            if nr > 0 or not r:
                if nums2:
                    # replacement with line number information
                    numbers = calc_numbers(res, r, numbers, lin, nt, nums2)
                else:
                    numbers = numbers[:lin] + (-ll,) * nr + numbers[lin+nt:]
            else:
                # join to single line: keep correct line number
                numbers = numbers[:lin] + (-ll,) + numbers[lin+nt+1:]
        res += r
    return (res + txt[last:], numbers)

#   helper function for mysub()
#
def calc_numbers(res, repl, numbers, lin, nt, nums2):
    t = text_combine((res, numbers[:lin+1]), ('', nums2))
    t = text_combine((repl, t[1]), ('', numbers[lin+nt:]))
    return t[1]

#   combine (add) two text elements with line number information
#
def text_combine(text1, text2):
    space = (r'\A(' + mark_deleted + r'|' + re_begin_env
                + r'|' + re_end_env + r'|\s)*\Z')
    (t1, n1) = text1
    (t2, n2) = text2
    if n1[-1] == n2[0] or re.search(space, t1[t1.rfind('\n')+1:]):
        # same line numbers at junction or
        # only "space" after last line break in text1:
        # use first line number from text2 at junction
        n = n1[:-1] + n2
    else:
        # use last line number from text1 at junction
        n = n1[:-1] + (-abs(n1[-1]),) + n2[1:]
    return (t1 + t2, n)

#   prepend and append plain strings to a text with line number information
#
def text_add_frame(pre, post, text):
    return (
        pre + text[0] + post,
        (text[1][0],) * pre.count('\n') + text[1]
                + (text[1][-1],) * post.count('\n')
    )

#   extract text with line number information from a group of a match
#
def text_from_match(m ,grp, text):
    if m.string is not text[0]:
        fatal('text_from_match(): bad match object')
    beg = m.string[:m.start(grp)].count('\n')
    end = beg + m.group(grp).count('\n') + 1
    return (m.group(grp), text[1][beg:end])

#   expansion of a match from replacement template repl:
#   returned text element provides line number information,
#   if repl contains a reference to a capturing group
#
def myexpand(m, repl, text):
#   return m.expand(repl)       # fail-save version
    if not repl:
        return ''

    # first parse repl: build list 'ops' of
    # (strings) and (numbers of referenced capturing groups)
    # - compare parse_template() in /usr/lib/python?.?/sre_parse.py
    escapes = {
        'a': '\a', 'b': '\b', 'f': '\f', 'n': '\n',
        'r': '\r', 't': '\t', 'v': '\v', '\\': '\\'
    }
    ops = []
    first = None
    cur_str = ''
    i = 0
    while i < len(repl):
        c = repl[i]
        i += 1
        if c != '\\':
            cur_str += c
            continue
        if i >= len(repl):
            cur_str += '\\'
            break
        c = repl[i]
        i += 1
        if c in escapes:
            cur_str += escapes[c]
        elif c in '0g':
            fatal('myexpand(): escape sequences \\0... and \\g<...>'
                            + ' not implemented')
        elif c.isdecimal():
            if cur_str:
                ops += [cur_str]
                cur_str = ''
            if first is None:
                first = len(ops)
            ops += [int(c)]
        else:
            cur_str += '\\' + c
    if cur_str:
        ops += [cur_str]

    if first is None:
        # no group reference found, repl == '' was excluded above
        return ops[0]

    # build replacement text with line number information
    t = text_from_match(m, ops[first], text)
    if first > 0:
        t = text_add_frame(ops[0], '', t)
    for i in range(first + 1, len(ops)):
        if type(ops[i]) is int:
            t2 = text_from_match(m, ops[i], text)
            t = text_combine(t, t2)
        else:
            t = text_add_frame('', ops[i], t)
    return t

def mysearch(expr, text, flags=0):
    if type(text) is not tuple:
        fatal('wrong arg for mysearch()')
    return re.search(expr, text[0], flags=flags)
def text_get_txt(text):
    return text[0]
def text_get_num(text):
    return text[1]


#######################################################################
#
#   parse command line, read complete input into 'text'
#
parser = argparse.ArgumentParser()
parser.add_argument('file', nargs='?')
parser.add_argument('--repl')
parser.add_argument('--nums')
parser.add_argument('--defs')
parser.add_argument('--extr')
parser.add_argument('--lang')
parser.add_argument('--unkn', action='store_true')
cmdline = parser.parse_args()

if cmdline.nums:
    cmdline.nums = myopen(cmdline.nums, mode='w')

if not cmdline.lang or cmdline.lang == 'de':
    set_language_de()
elif cmdline.lang == 'en':
    set_language_en()
else:
    fatal('unrecognized language "' + cmdline.lang
            + '" given in option')

if cmdline.extr:
    cmdline.extr = cmdline.extr.strip(',')
    cmdline.extr_re = cmdline.extr.replace(',', '|')
    cmdline.extr_list = cmdline.extr.split(',')
else:
    cmdline.extr_list = []

defs = Aux()
defs.project_macros = ()
defs.system_macros = ()
defs.heading_macros = ()
defs.environments = ()
defs.equation_environments = ()
defs.environments = ()
defs.environment_begins = ()
defs.theorem_environments = ()
defs.misc_replace = ()
if cmdline.defs:
    s = myopen(cmdline.defs).read()
    try:
        exec(s)
    except BaseException as e:
        import traceback
        i = 0 if isinstance(e, SyntaxError) else -1
        s = traceback.format_exc(limit=i)
        s = re.sub(r'"<string>"', '"' + cmdline.defs + '"', s)
        s = re.sub(r'in <module>', '', s)
        s = re.sub(r'Traceback \(most recent call last\):\n', '', s)
        fatal('problem in file "' + cmdline.defs + '"', s)

if cmdline.file:
    text = myopen(cmdline.file).read()
else:
    text = sys.stdin.read()

#   the initial list of line numbers: in fact "only" a tuple
#
numbers = tuple(range(1, text.count('\n') + 2))

#   for mysub():
#   text becomes a 2-tuple of text string and number list
#
text = (text, numbers)


#######################################################################
#
#   LAB:VERBATIM
#   treat verbatim(*) environments and \verb(*) macros
#   (the given verbatim text is expanded to a coded version that is only
#    resolved directly at output by resolve_escapes())
#
#   - expanded content of verbatim(*) environment is enclosed in
#     \begin{verbatim(*)}...\end{verbatim(*)}
#       --> can be removed or replaced by fixed text with 'verbatim'
#           or r'verbatim\*' entry in parms.environments
#       --> complete removal without paragraph break:
#           \LTskip{\begin{verbatim}...\end{verbatim}}
#           or \LTalter{...}{replacement}
#   - expanded text of \verb(*) macro is enclosed in \verb(*){...}
#       --> can be removed or replaced with Macro('verb', 'A', ...)
#           or Macro(r'verb\*', 'A', ...) in parms.*_macros
#   - BUG: \verb(*) not handled correctly but treated as unknown macro,
#     if used in replacement for a declared macro of parms.*_macros
#       --> won't work: Simple('textbackslash', r'\\verb?\\?')
#
def f(m):
    # enclose coded text in \begin{verbatim(*)}...\end{verbatim(*)},
    # enforce heading and trailing empty lines for environment content,
    # even in case of single line like `A\begin{verbatim}X\end{verbatim}B'
    def g(m):
        return verbatim(m.group(0), mark_verbatim_tmp, verb_asterisk)
    t = text_from_match(m, 3, text)
    t = mysub(r'.|\n', g, t)
    return text_add_frame(
            m.group(1) + '\n\n\\begin{verbatim' + verb_asterisk + '}',
            '\\end{verbatim' + verb_asterisk + '}\n\n', t)
verb_asterisk = '*'
text = mysub(r'^(([^\n\\%]|\\.)*)' + begin_lbr + r'verbatim\*\}((.|\n)*?)'
                + r'\\end\{verbatim\*\}', f, text, flags=re.M)
                        # important: non-greedy repetition *?
verb_asterisk = ''
text = mysub(r'^(([^\n\\%]|\\.)*)' + begin_lbr + r'verbatim\}((.|\n)*?)'
                + r'\\end\{verbatim\}', f, text, flags=re.M)
                        # important: non-greedy repetition *?

def f(m):
    # enclose coded text in \verb(*){...}
    return (m.group(1) + '\\verb' + verb_asterisk + '{'
                + verbatim(m.group(4), mark_verbatim_tmp, verb_asterisk) + '}')
verb_asterisk = '*'
text = mysub(r'^(([^\n\\%]|\\.)*)\\verb\*(\S)(.*?)\3',
                f, text, flags=re.M)
                        # important: non-greedy repetition *?
verb_asterisk = ''
text = mysub(r'^(([^\n\\%]|\\.)*)\\verb' + end_mac + r'(\S)(.*?)\3',
                f, text, flags=re.M)
                        # important: non-greedy repetition *?


#######################################################################
#
#   remove % comments
#   - line beginning with % is completely removed
#
text = mysub(r'^[ \t]*%.*\n', '', text, flags=re.M)

#   - join current and next lines, if no space before first unescaped %
#       + not, if next line is empty
#       + not, if \macro call directly before %
#
def f(m):
    if re.search(r'(?<!\\)(\\\\)*\\' + macro_name + r'\Z', m.group(1)):
        # \macro call before %: do no remove line break
        return m.group(0)
    return m.group(1)
text = mysub(r'^(([^\n\\%]|\\.)*)(?<![ \t\n])%.*\n(?![ \t]*\n)',
                        f, text, flags=re.M)
                # r'(?<!x)y' matches 'y' not preceded by 'x'

#   - "normal case": just remove rest of line, keeping the line break
#
text = mysub(r'^(([^\n\\%]|\\.)*)%.*$', r'\1', text, flags=re.M)

#   now we can replace \\ with mark_linebreak
#   which is needed for parsing of equation environments below
#   --> no double backslash \\ from here on
#
text = mysub(r'\\\\', mark_linebreak, text)

#   only afterwards remove option \\[...]:
#   in expression bracketed, we do not account for \\
#
text = mysub(mark_linebreak + sp_bracketed, mark_linebreak, text)

#   replace temporary marks for verbatim characters
#
text = mysub(mark_verbatim_tmp[0] + r'(\d+)' + mark_verbatim_tmp[1],
                mark_verbatim[0] + r'\1' + mark_verbatim[1], text)


#######################################################################
#
#   check nesting limits for braces, brackets, and environments;
#   we construct regular expressions for a larger nesting depth and
#   test, whether the innermost group matches
#
for m in re.finditer(re_braced(parms.max_depth_br + 1, '(?P<inner>', ')'),
                            text_get_txt(text)):
    if m.group('inner'):
        # innermost {} braces did match
        fatal('maximum nesting depth for {} braces exceeded,'
            + ' parms.max_depth_br=' + str(parms.max_depth_br), m.group(0))
for m in re.finditer(re_bracketed(parms.max_depth_br + 1, '(?P<inner>', ')'),
                            text_get_txt(text)):
    if m.group('inner'):
        fatal('maximum nesting depth for [] brackets exceeded,'
            + ' parms.max_depth_br=' + str(parms.max_depth_br), m.group(0))

for env in (
    parms.equation_environments()
    + parms.environments()
):
    expr = re_nested_env(env[0], parms.max_depth_env + 1, '')
    for m in re.finditer(expr, text_get_txt(text)):
        if m.group('inner'):
            fatal('maximum nesting depth for environments exceeded,'
                    + ' parms.max_depth_env=' + str(parms.max_depth_env),
                        m.group(0))

#   check whether equation replacements appear in original text
#
if parms.check_equation_replacements:
    for repl in parms.inline_math + parms.display_math:
        m = re.search(r'^.*' + re.escape(repl) + r'.*$',
                        text_get_txt(text), flags=re.M)
        if m:
            warning('equation replacement "' + repl
                + '" found in input text,'
                + ' see LAB:CHECK_EQU_REPLS in script', m.group(0))


#######################################################################
#
#   resolve macros and special environment starts listed above
#   ( possible improvement:
#     - gather macros with same argument pattern and replacement string:
#       lists of names in a dictionary with tuple (args, repl) as key
#     - handle macros in a dictionary entry with one replacement run
#   )
#
list_macs_envs = []
for (name, args, repl) in (
    parms.system_macros()
    + parms.project_macros()
):
    if name in cmdline.extr_list:
        continue
    expr = r'\\' + name + end_mac
    re_args = re_code_args(args, repl, 'Macro', name)
    if not args:
        # consume all space allowed after macro without arguments
        expr += skip_space_macro
    elif args == 'O' * len(args):
        # do the same, if actually no optional argument is following
        expr = (r'(?:(?:' + expr + r'(?!' + skip_space + r'\[)'
                    + skip_space_macro + r')|(?:' + expr + re_args + r'))')
    else:
        # at least one mandatory argument expected
        expr += re_args
    list_macs_envs.append((expr, mark_deleted + repl))
for (name, args, repl) in parms.environment_begins():
    expr = begin_lbr + name + r'\}' + re_code_args(args, repl,
                                                    'EnvBegin', name)
    list_macs_envs.append((expr, mark_begin_env_sub + repl))

flag = True
cnt = 1
match = None
while flag:
    # loop until no more replacements performed
    if cnt > 2 * parms.max_depth_br:
        fatal('infinite recursion in macro definition?',
                        match.group(0) if match else '')
    cnt += 1
    flag = False
    for (expr, repl) in list_macs_envs:
        m = mysearch(expr, text)
        if m:
            match = m
            flag = True
            text = mysub(expr, repl, text)


##################################################################
#
#   other replacements: collected in list actions
#   list of 2-tuples:
#       [0]: search pattern as regular expression
#       [1]: replacement text
#
actions = list(parms.misc_replace())

for (name, repl) in parms.environments():
    env = re_nested_env(name, parms.max_depth_env, '')
    re_code_args('', repl, 'EnvRepl', name, no_backslash=True)
    actions += [(env, mark_begin_env_sub + repl + mark_end_env_sub)]

def f(m):
    txt = m.group(2)
    if txt and txt[-1] not in parms.heading_macros_punct:
        txt += '.'
    return txt
for s in parms.heading_macros():
    actions += [(
        r'\\' + s + r'(?:' + sp_bracketed + r')?' + sp_braced,
        f
    )]

#   replace $$...$$ by equation* environment
#
dollar_dollar_flag = False
def f(m):
    global dollar_dollar_flag
    dollar_dollar_flag = not dollar_dollar_flag
    if dollar_dollar_flag:
        return r'\begin{equation*}'
    return r'\end{equation*}'
actions += [(r'(?<!\\)\$\$', f)]

# replace $...$ by text from variable parms.inline_math
# BUG (with warning): fails e.g. on $x \text{ for $x>0$}$
#
def f(m):
    if re.search(r'(?<!\\)\$', m.group(1)):
        warning('"$" in {} braces (macro argument?): not properly handled',
                    m.group(0))
    parms.inline_math = parms.inline_math[1:] + parms.inline_math[:1]
    return parms.inline_math[0]
actions += [(r'(?<!\\)\$((?:' + braced + r'|[^\\$]|\\.|\\\n)+)\$', f)]

#   macros \textxxx
#
for (m, c) in (
    ('textbackslash', '\\'),
    ('textasciicircum', '^'),
    ('textasciitilde', '~'),
):
    actions += [(r'\\' + m + end_mac + skip_space_macro,
                        verbatim(c, mark_verbatim, ''))]

#   now perform the collected replacement actions
#
for (expr, repl) in actions:
    text = mysub(expr, repl, text, flags=re.M)


##################################################################
#
#   LAB:ACCENTS
#   translate text-mode accents to corresponding UTF8 characters
#   - if not found: raise warning and keep accent macro in text
#
def replace_accent(mac, accent, text):
    def f(m):
        # find the UTF8 character for the matched letter [a-zA-Z]
        # with the accent given in argument of replace_accent()
        c = m.group(2)
        if c.islower():
            t = 'SMALL'
        else:
            t = 'CAPITAL'
        u = 'LATIN ' + t + ' LETTER ' + c.upper() + ' WITH ' + accent
        try:
            return unicodedata.lookup(u)
        except:
            warning('could not find UTF8 character "' + u
                    + '"\nfor accent macro "' + m.group(0) + '"')
            return m.group(0)
    if mac.isalpha():
        # ensure space or brace after macro name
        mac += end_mac
    else:
        mac = re.escape(mac)
    # accept versions with and without {} braces
    return mysub(r'\\' + mac + skip_space + r'(\{)?([a-zA-Z])(?(1)\})',
                                f, text)

for (mac, acc) in (
    ("'", 'ACUTE'),
    ('`', 'GRAVE'),
    ('^', 'CIRCUMFLEX'),
    ('v', 'CARON'),
    ('~', 'TILDE'),
    ('"', 'DIAERESIS'),
    ('r', 'RING ABOVE'),
    ('=', 'MACRON'),
    ('b', 'LINE BELOW'),
    ('u', 'BREVE'),
    ('H', 'DOUBLE ACUTE'),
    ('.', 'DOT ABOVE'),
    ('d', 'DOT BELOW'),
    ('c', 'CEDILLA'),
    ('k', 'OGONEK'),
):
    text = replace_accent(mac, acc, text)


##################################################################
#
#   LAB:EQUATIONS: replacement of equation environments
#
##################################################################

#   example: see file Example.md
#
#   1. split equation environment into 'lines' delimited by \\
#      alias mark_linebreak
#   2. split each 'line' into 'sections' delimited by &
#   3. split each 'section' into math and \text parts
#
#   - argument of \text{...} (variable parms.macro_text) is reproduced
#     without change
#   - math parts are replaced by values from variable parms.display_math
#   - interpunction signs (see variable parms.mathpunct) at end of a
#     math part, ignoring parms.mathspace, are appended to replacement
#   - relational operators at beginning of a math part are prepended
#     as ' gleich ...', if math part is not first on line ('&' is a part)
#   - other operators like +, -, *, / are prepended e.g. as ' minus ...'
#   - see variables parms.mathop and parms.mathoptext for text replacements
#   - basic replacement steps to next value from parms.display_math,
#       if part includes a leading operator,
#       after intermediate \text{...},
#       and if last math part ended with interpunction
#           (the latter for parms.change_repl_after_punct == True)
#   - math space (variable parms.mathspace) like \quad is replaced by ' '

#   Assumptions:
#   - \\ has been changed to mark_linebreak, & is still present
#   - macros from LAB:EQU:MACROS already have been deleted
#   - \text{...} has been resolved not yet
#   - mathematical space as \; and \quad (variable parms.mathspace)
#     is still present
#   - math macros like \epsilon or \Omega that might constitute a
#     math part: still present or replaced with non-space

parms.mathspace = r'(?:\\[ ,;:\n]|(?<!\\)~|\\q?quad' + end_mac + r')'
parms.mathop = (
    r'\+|-|\*|/'
    + r'|=|<|>|(?<!\\):=?'          # accept ':=' and ':'
    + r'|\\[gl]eq?' + end_mac
    + r'|\\su[bp]set(?:eq)?' + end_mac
    + r'|\\Leftrightarrow' + end_mac
    + r'|\\to' + end_mac
    + r'|\\stackrel' + sp_braced + skip_space + r'\{=\}'
    + r'|\\c[au]p' + end_mac
)
parms.mathpunct = r'(?:(?<!\\)[;,.])'
parms.change_repl_after_punct = True

def display_math_update():
    parms.display_math = parms.display_math[1:] + parms.display_math[:1]
def display_math_get(update):
    if update:
        display_math_update()
    return parms.display_math[0]

#   replace a math part by suitable raw text
#
def math2txt(txt, first_on_line):
    # check for leading operator, possibly after mathspace;
    # there also might be a '{}' or r'\mbox{}' for making e.g. '-' binary
    m = re.search(r'\A(' + parms.mathspace
                    + r'|(?:\\mbox' + skip_space + r')?\{\}|\s)*'
                    + r'(' + parms.mathop + r')', txt)
    if m and not first_on_line:
        # starting with operator, not first on current line
        pre = parms.mathoptext.get(m.group(2), parms.mathoptext[None])
        txt = txt[m.end(0):]
        update = True
    else:
        # check for leading mathspace
        m = re.search(r'\A(' + skip_space + parms.mathspace + r')+', txt)
        if m:
            pre = ' '
            txt = txt[m.end(0):]
        else:
            pre = ''
        update = False

    # check for trailing mathspace
    m = re.search(r'(' + parms.mathspace + skip_space + r')+\Z', txt)
    if m:
        post = ' '
        txt = txt[:m.start(0)]
    else:
        post = ''
    txt = txt.strip()
    if not txt:
        return pre + post

    # check for trailing interpunction
    m = re.search(r'(' + parms.mathpunct + r')\Z', txt)
    if not m:
        return pre + display_math_get(update) + post
    if txt == m.group(1):
        ret = pre + txt + post
    else:
        ret = pre + display_math_get(update) + m.group(1) + post
    if parms.change_repl_after_punct:
        # after interpunction: next part with different replacement
        display_math_update()
    return ret

#   split a section between & delimiters into \text{...} and math parts
#
def split_sec(txt, first_on_line):
    last = 0
    res = ''
    # iterate over \text parts
    for m in re.finditer(r'\\' + parms.text_macro + sp_braced, txt):
        # math part between last and current \text
        res += math2txt(txt[last:m.start(0)], first_on_line)
        # content of \text{...}
        res += m.group(1)
        last = m.end(0)
        first_on_line = False
        display_math_update()
    # math part after last \text
    res += math2txt(txt[last:], first_on_line)
    return res

#   parse the text of an equation environment
#
def parse_equ(equ):
    # first resolve sub-environments (e.g. cases) and mark_deleted
    # in order to see interpunction
    d = (r'((' + re_begin_env + r')|(' + re_end_env
                    + r')|(' + mark_deleted + r'))')
    equ = mysub(d, '', equ)

    # then split into lines delimited by \\ alias mark_linebreak
    # BUG (with warning for braced macro arguments):
    # repl_line() and later repl_sec() may fail if \\ alias mark_linebreak
    # or later & are argument of a macro
    #
    for f in re.finditer(braced, text_get_txt(equ)):
        if re.search(mark_linebreak + r'|(?<!\\)&', f.group(1)):
            warning('"\\\\" or "&" in {} braces (macro argument?):'
                        + ' not properly handled',
                        re.sub(mark_linebreak, r'\\\\', text_get_txt(equ)))
            break

    # important: non-greedy *? repetition
    line = skip_space + r'((.|\n)*?)(' + mark_linebreak + r'|\Z)'
    # return replacement for RE line
    def repl_line(m):
        # finally, split line into sections delimited by '&'
        # important: non-greedy *? repetition
        sec = r'((.|\n)*?)((?<!\\)&|\Z)'
        flag = Aux()
        flag.first_on_line = True
        def repl_sec(m):
            # split this section into math and text parts
            # BUG (without warning):
            # we assume that '&' always creates white space
            ret = split_sec(m.group(1), flag.first_on_line) + ' '
            flag.first_on_line = False
            return ret
        t = text_from_match(m, 1, equ)
        t = mysub(sec, repl_sec, t)
        return text_add_frame('  ', '\n', t)

    return mysub(line, repl_line, equ)

#   replace equation environments listed above
#
for (name, args, replacement) in parms.equation_environments():
    if not replacement:
        re_args = re_code_args(args, replacement, 'EquEnv', name)
        expr = re_nested_env(name, parms.max_depth_env, re_args)
        def f(m):
            t = text_from_match(m, 'body', text)
            t = parse_equ(t)
            return text_add_frame(mark_begin_env, mark_end_env, t)
        text = mysub(expr, f, text)
        continue
    # environment with fixed replacement and added interpunction
    env = re_nested_env(name, parms.max_depth_env, '')
    re_code_args('', replacement, 'EquEnv', name, no_backslash=True)
    def f(m):
        txt = parse_equ(text_from_match(m, 'body', text))
        txt = text_get_txt(txt).strip()
        s = replacement
        m = re.search(r'(' + parms.mathpunct + r')\Z', txt)
        if m:
            s += m.group(1)
        return mark_begin_env + s + mark_end_env
    text = mysub(env, f, text)


#######################################################################
#
#   final clean-up
#
#######################################################################

#   only print unknown macros and environments?
#
if cmdline.unkn:
    macsknown = (
        'begin', 
        'end',
        'item',
    )
    macs = []
    for m in re.finditer(r'\\(' + macro_name + r')', text_get_txt(text)):
        if m.group(1) not in macs:
            macs += [m.group(1)]
    macs.sort()
    for m in macs:
        if m not in macsknown:
            print('\\' + m)
    envs = []
    for m in re.finditer(begin_lbr + r'(' + environ_name + r')\}',
                            text_get_txt(text)):
        if m.group(1) not in envs:
            envs += [m.group(1)]
    envs.sort()
    for e in envs:
        if e != mark_internal_pre:
            print(r'\begin{' + e + '}')
    exit()

#   delete remaining \xxx macros unless given in --extr option;
#   if followed by braced argument: copy its content
#
excl = r'begin|end|item'
if cmdline.extr:
    excl += r'|' + cmdline.extr_re
re_macro = r'\\(?!(?:' + excl + r')' + end_mac + r')' + macro_name
            # 'x(?!y)' matches 'x' not followed by 'y'
re_macro_arg = re_macro + sp_braced
while mysearch(re_macro_arg, text):
    # macros with braced argument might be nested
    text = mysub(re_macro_arg, mark_deleted + r'\1', text)
text = mysub(re_macro + skip_space_macro, mark_deleted, text)

#   delete remaining environment frames outside of equations
#   - only after treatment of macros: protect line break before \begin;
#     here we also delete placeholders \begin{%} from above
#
text = mysub(re_begin_env, mark_deleted, text)
text = mysub(re_end_env, mark_deleted, text)

#   LAB:ITEMS
#   item lists may pose problems with interpunction checking
#   - one can simply remove the \item[...] label
#   - one can look backwards in the text and repeat a present interpunction
#     sign after the item label
#       --> this also checks text in the label
#   - this should be done after removal of \begin{itemize}
#   \item[...] may skip arbitrary space
#
if parms.keep_item_labels:
    # first try with preceding interpunction [.,;:!?] ...
    text = mysub(r'(((?<!\\)[.,;:!?])(?:\s|' + mark_deleted
                + r')*)\\item' + sp_bracketed + r'\s*', r'\1 \3\2 ', text)
    # ... otherwise simply extract the text in \item[...]
    text = mysub(r'\\item' + sp_bracketed + r'\s*', r' \1 ', text)
else:
    text = mysub(r'\\item' + sp_bracketed + r'\s*',
                        ' ' + parms.default_item_lab + ' ', text)

# finally, items without [...]
text = mysub(r'\\item' + end_mac + r'\s*',
                        ' ' + parms.default_item_lab + ' ', text)

#   LAB:SMALLMACS
#   actions only after macro resolution: preceding macro could eat space
#   - replace space macros including ~, \, and &
#   - delete \!, \-
#
text = mysub(r'\\,', utf8_nnbsp, text)
text = mysub(r'(?<!\\)~', utf8_nbsp, text)
text = mysub(r'(?<!\\)&', ' ', text)
text = mysub(parms.mathspace, ' ', text)
text = mysub(r'\\[!-]', '', text)

#   - finally remove mark_deleted,
#     delete a line, if it only contains such marks;
#   - replace \\ placeholder
#
text = mysub(r'^([ \t]*' + mark_deleted + r'[ \t]*)+\n', '', text, flags=re.M)
text = mysub(mark_deleted, '', text)
text = mysub(mark_linebreak, ' ', text)


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
    for lin in myopen(cmdline.repl):
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

        r = ' '.join(lin[i+1:])
        if re.search(r'(?<!\\)%', r):
            fatal('please use escaped \\% for replacement in file "'
                                + cmdline.repl + '"', r)
        r = re.sub('\\\\', '\\\\\\\\', r)       # \ ==> \\
        text = mysub(t, r, text)


##################################################################
#
#   output of results
#
##################################################################

#   if option --nums: write line number information
#
def write_numbers(nums, mx):
    if not cmdline.nums:
        return
    for i in range(mx):
        if i < len(nums):
            s = str(abs(nums[i]))
            if nums[i] < 0:
                s += '+'
        else:
            s = '?'
        cmdline.nums.write(s + '\n')

#   - resolve backslash escapes for {, }, $, %, _, &, #
#   - resolve verbatim characters
#
def resolve_escapes(txt):
    # subsequent replacement runs would lead to mistakes
    def f(m):
        if m.group(1):
            return m.group(1)
        c = chr(int(m.group(2)))
        if c == '\n':
            # for line number tracking, compare verbatim()
            return ''
        return c
    return re.sub(r'\\([{}$%_&#])|' 
            + mark_verbatim[0] + r'(\d+)' + mark_verbatim[1], f, txt)

#   on option --extr: only print arguments of these macros
#
if cmdline.extr:
    def extr(t, n):
        global extract_list
        extract_list += [(t,n)]
    extract_list = []
    mysub(r'\\(?:' + cmdline.extr_re + r')(?:' + sp_bracketed
                    + r')*' + sp_braced, r'\2', text, extract=extr)

    for (txt, nums) in extract_list:
        txt = txt.rstrip('\n') + '\n\n'
        sys.stdout.write(resolve_escapes(txt))
        write_numbers(nums, txt.count('\n'))
    exit()

#   if braces {...} did remain somewhere: delete
#
while mysearch(braced, text):
    text = mysub(braced, r'\1', text)

#   write text to stdout
#
txt = text_get_txt(text)
numbers = text_get_num(text)
sys.stdout.write(resolve_escapes(txt))

#   if option --nums given: write line number information
#
write_numbers(numbers, len(numbers))

