#
#   Tex2txt, a flexible LaTeX filter
#   Copyright (C) 2018-2020 Matthias Baumann
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
#   - see README.md
#
#   Principle of operation:
#   - read complete input text into a string, then make replacements
#   - replacements are performed via the "reimplementation" mysub() of
#     re.sub() in order to observe deletion and inclusion of line breaks
#   - in order to treat nested braces / brackets and some nested
#     environments, we construct regular expressions by iteration;
#     maximum recognised nesting depth (and thus length of these expressions)
#     is controlled by the variables parms.max_depth_br and
#     parms.max_depth_env
#

class Aux:
    pass
parms = Aux()

#   LAB:MACROS
#   these are macros with tailored treatment;
#   replacement only if not given in option --extr
#
#   Simple(name, repl='', extr=''):
#   abbreviation for Macro(name, '', repl, extr)
#
#   Macro(name, args, repl='', extr=''):
#   name:
#       - macro name without leading backslash
#       - characters with special meaning in regular expressions, e.g. '*',
#         may need to be escaped; see for example declaration of \hspace,
#         and use only unreferenced groups (?:...), see \renewcommand
#   args:
#       - string that codes argument sequence
#       - A: a mandatory {...} argument
#       - O: an optional [...] argument
#       - P: a mandatory [...] argument, see for instance \cite
#   repl:
#       - replacement pattern, r'...\d...' (d: single digit) extracts text
#         from position d in args (counting from 1)
#       - other escape rules: see escape handling at myexpand() below;
#         e.g., include a single backslash: repl=r'...\\...'
#       - inclusion of % only accepted as escaped version r'...\\%...',
#         will be resolved to % at the end by before_output()
#       - inclusion of double backslash \\ and replacement ending with \
#         will be rejected
#       - reference by r'\d' to an optional argument will be refused
#   extr:
#       - append this replacement (specified as in repl) at the end
#         of the text, separated by blank lines
#
#   REMARKS:
#       - if a macro does not find its mandatory argument(s) in the text,
#         it is treated as unknown and can be seen with option --unkn
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
            # for LaTeX, argument is ignored: \newcommand{\LTadd}[1]{}
    Macro('LTalter', 'AA', r'\2'),
            # for LaTeX, first argument is used: \newcommand{\LTalter}[2]{#1}
    Macro('LTskip', 'A'),
            # for LaTeX, first argument is used: \newcommand{\LTskip}[1]{#1}

) + defs.project_macros


#   BUG: quite probably, some macro is missing here ;-)
#
parms.system_macros = lambda: (

    Macro('caption', 'OA', extr=r'\2'),         # extract to end of text
    Macro('cite', 'A', '[1]'),
    Macro('cite', 'PA', r'[1, \1]'),
    Macro('color', 'A'),
    Macro('colorbox', 'AA', r'\2'),
    Macro('documentclass', 'OA'),
    Macro('eqref', 'A', '(7)'),
    Macro('fcolorbox', 'AAA', r'\3'),
    Macro('footnote', 'OA', extr=r'\2'),        # extract to end of text
    Macro('footnotemark', 'O'),
    Macro('footnotetext', 'OA', extr=r'\2'),    # extract to end of text
    Macro('framebox', 'OOA', r'\3'),
    Simple('hfill', ' '),
    Macro(r'hspace\*?', 'A'),
    Macro('include', 'A'),
    Macro('includegraphics', 'OA'),
    Macro('input', 'A'),
    # \label: see LAB:EQU_MACROS
    # \mathrlap: see LAB:EQU_MACROS
    # \medspace: treated at LAB:SPACE, parms.mathspace
    Simple('newline', ' '),
    # \nonumber: see LAB:EQU_MACROS
    # \notag: see LAB:EQU_MACROS
    Macro('pageref', 'A', '99'),
    Simple('par', r'\n\n'),
    # \qedhere: see LAB:EQU_MACROS
    # \qquad: treated at LAB:SPACE, parms.mathspace
    # \quad: treated at LAB:SPACE, parms.mathspace
    Macro('ref', 'A', '13'),
    Macro('(?:re)?newcommand\*?', 'AOOA'),
    Macro('texorpdfstring', 'AA', r'\1'),
    # \textasciicircum: defined below
    # \textasciitilde: defined below
    # \textbackslash: defined below
    Macro('textcolor', 'AA', r'\2'),
    # \thickspace: treated at LAB:SPACE, parms.mathspace
    # \thinspace: treated at LAB:SPACE, parms.mathspace
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

    # LAB:EQU_MACROS
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
#   (avoids false positives from LanguageTool)
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
    r'title',

) + defs.heading_macros


#   equation environments, partly from LaTeX package amsmath;
#   see comments at LAB:EQUATIONS below
#
#   EquEnv(name, args='', repl='')
#   - args: arguments at \begin, as for Macro()
#   - repl not empty: replace whole environment with this fix text;
#     if the actual content ends with a character from variable
#     parms.mathpunct (ignoring macros from LAB:EQU_MACROS and variable
#     parms.mathspace), then this sign is appended
#   - repl: plain string, no backslashes accepted
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
#   - repl: plain string, no backslashes accepted
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
#   ATTENTION:  do not include itemize and enumerate here,
#               see label LAB:ENUMERATE below
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
#   see also LAB:SPACE and before_output() below
#
#   ATTENTION:
#   - prepend mark_deleted, if replacement may evaluate to empty string
#     or begin with white space
#   - do not use replacement that
#       - ends with a backslash
#       - may insert a double backslash
#       - may insert an unescaped % sign
#     (see comments at Macro() above and compare checks in re_code_args())
#
parms.misc_replace = lambda: (

    # \[    ==> ... 
    (r'\\\[', r'\\begin{equation*}'),
    # \]    ==> ... 
    (r'\\\]', r'\\end{equation*}'),

    # ---    ==> UTF-8 em dash
    (r'(?<!\\)---', utf8_emdash),   # (?<!x)y matches y not preceded by x
    # --    ==> UTF-8 en dash
    (r'(?<!\\)--', utf8_endash),
    # ``    ==> UTF-8 double quotation mark (left)
    (r'(?<!\\)``', utf8_lqq),
    # ''    ==> UTF-8 double quotation mark (right)
    (r'(?<!\\)' + "''", utf8_rqq),
    # \! \- ==> delete
    (r'\\[!-]', mark_deleted),

) + parms.misc_replace_lang() + defs.misc_replace


parms.misc_replace_de = lambda: (

    # "=    ==> -
    (r'(?<!\\)"=', '-'),
    # "`    ==> UTF-8 German double quotation mark (left)
    (r'(?<!\\)"`', utf8_glqq),
    # "'    ==> UTF-8 German double quotation mark (right)
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

#   recognise {} braces inside of [] brackets?
#   - generates really large regular expressions
#
parms.recognise_braces_in_brackets = False

#   keep \item labels, if given in [...] option?
#   (if set to False: use default labels defined next)
#
parms.keep_item_labels = True

#   default \item labels in itemize environment
#   (used for \item without [...], or if not parms.keep_item_labels)
#
parms.default_item_labs = ('',)

#   default \item labels in enumerate environment
#   (used for \item without [...], or if not parms.keep_item_labels)
#
parms.default_item_enum_labs = ('1.', '2.', '3.', '4.', '5.',
                                '6.', '7.', '8.', '9.', '10.')
# parms.default_item_enum_labs = ('',)    # turn labels off

#   repeat punctuation sign in front of an \item with [...] option?
#   see LAB:ITEMS
#
parms.item_label_repeat_punct = True


#   message on warnings / errors that should be found by LT;
#   don't include line breaks: will disrupt line number tracking
#
parms.warning_error_msg = ' WARNINGORERROR '


#   LAB:LANGUAGE
#
def set_language_de():

    # properties of these replacements for inline formulas:
    #   - no need to add to LT dictionary
    #   - absent leading / trailing space causes spelling errors
    #   - LT accepts e.g. 'mit einer Konstanten $C$ folgt', 'für alle $x$',
    #     'für ein $x$'
    #   - LT recognises mistakes like 'die $\epsilon$-Argument'
    #   - word repetitions are detected
    #   - resulting text can be checked for single letters (German)
    # other variant: AInlA, BInlB, ... (but has to be added to dictionary)
    # parms.inline_math = ('I1I', 'I2I', 'I3I', 'I4I', 'I5I', 'I6I')
    # parms.inline_math = ('AInlA', 'BInlB', 'CInlC',
    #                       'DInlD', 'EInlE', 'FInlF')

    # replacements for maths parts in displayed formulas
    # parms.display_math = ('D1D', 'D2D', 'D3D', 'D4D', 'D5D', 'D6D')
    # parms.display_math = ('ADsplA', 'BDsplB', 'CDsplC',
    #                       'DDsplD', 'EDsplE', 'FDsplF')

    # compare Issue #22
    parms.inline_math = ('B-B-B', 'C-C-C', 'D-D-D', 'E-E-E', 'F-F-F', 'G-G-G')
    parms.display_math = ('U-U-U', 'V-V-V', 'W-W-W', 'X-X-X', 'Y-Y-Y', 'Z-Z-Z')

    # LAB:CHECK_EQU_REPLS
    # this check is important if replacements had to be added to dictionary
    parms.check_equation_replacements = True

    # texts for maths operators; default: key None
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
#   parms.inline_math = ('B', 'C', 'D', 'E', 'F', 'G')
#   parms.display_math = ('U', 'V', 'W', 'X', 'Y', 'Z')
    # compare Issue #22
    parms.inline_math = ('B-B-B', 'C-C-C', 'D-D-D', 'E-E-E', 'F-F-F', 'G-G-G')
    parms.display_math = ('U-U-U', 'V-V-V', 'W-W-W', 'X-X-X', 'Y-Y-Y', 'Z-Z-Z')

    parms.check_equation_replacements = False
    parms.mathoptext = {'+': ' plus ', '-': ' minus ',
                        '*': ' times ', '/': ' over ',
                        None: ' equal '}
    parms.proof_title = 'Proof'
    parms.foreign_lang_mac = 'foreign'
    parms.replace_frgn_lang_mac = '[foreign]'
    parms.misc_replace_lang = parms.misc_replace_en


#   parameters used for parsing of equations
#   see LAB:EQUATIONS
#
def set_math_parms():
    parms.mathspace = (r'(?:\\[ ,;:\n\t]|(?<!\\)~'
                            + r'|\\(?:q?quad|(?:thin|med|thick)space)'
                            + end_mac + skip_space_macro + r')')
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


#   further replacements performed below:
#
#   - translation of $$...$$ to equation* environment
#   - replacement of $...$ and \(...\) inline maths
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
    raise_error('internal error', msg, detail, xit=1)
def warning(msg, detail=None):
    raise_error('warning', msg, detail)
def myopen(f, encoding, mode='r'):
    try:
        return open(f, mode=mode, encoding=encoding)
    except:
        raise_error('problem', 'could not open file "' + f + '"', xit=1)
warning_or_error = Aux()
warning_or_error.msg = ''
def raise_error(kind, msg, detail=None, xit=None):
    warning_or_error.msg = parms.warning_error_msg
    err = '\n*** ' + sys.argv[0] + ': ' + kind + ':\n' + msg + '\n'
    if detail:
        err += strip_internal_marks(detail) + '\n'
    sys.stderr.write(err)
    if xit is not None:
        exit(xit)
def strip_internal_marks(s):
    # will be redefined below
    return s

#   for internal marks: cannot appear in text after removal of % comments
#   (has to be asymmetrical)
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

#   this mark enforces a line break without creating a new blank line
#
mark_enforce_linebreak = mark_deleted + '\n' + mark_deleted

#   internal representation of double backslash \\
#
mark_linebreak = mark_internal_pre + 'L' + mark_internal_post

#   mark for internal representation of a single verbatim character,
#   will be resolved only at output by before_output()
#
mark_verbatim = (mark_internal_pre + 'V', 'V' + mark_internal_post)
mark_verbatim_tmp = ('____V', 'V__')    # before removal of % comments

#   only for error messages: remove internal marks
#
def strip_internal_marks(s):
    s = re.sub(mark_deleted, '', s)
    s = re.sub(mark_linebreak, r'\\\\', s)
    s = re.sub(mark_verbatim[0], r'\\verb.', s)
    s = re.sub(mark_verbatim[1], r'.', s)
    s = re.sub(re.escape(mark_begin_env), r'\\begin{.}', s)
    s = re.sub(re.escape(mark_end_env), r'\\end{.}', s)
    return s

#   space allowed inside of current paragraph, at most one line break
#
skip_space = r'(?:[ \t]*\n?[ \t]*)'

#   regular expression for nested {} braces
#   BUG (but error message on overrun): the nesting limit is unjustified
#
def re_braced(max_depth, inner_beg, inner_end, outer_beg='(', outer_end=')'):
    atom = r'[^\\{}]|\\.|\\\n'
    braced = inner_beg + r'\{(?:' + atom + r')*\}' + inner_end
        # (?:...) is (...) without creation of a reference
    for i in range(max_depth - 2):
        braced = r'\{(?:' + atom + r'|' + braced + r')*\}'
    braced = (r'(?<!\\)\{' + outer_beg + r'(?:' + atom + r'|' + braced + r')*'
                    + outer_end + r'\}')
        # outer-most (...) for reference at substitutions below
        # '(?<!x)y' matches 'y' not preceded by 'x'
    return braced
braced = re_braced(parms.max_depth_br, '', '')
sp_braced = skip_space + braced

#   the same for [] brackets
#
def re_bracketed(max_depth, inner_beg, inner_end):
    if parms.recognise_braces_in_brackets:
        atom = (r'[^][{\\]|\\.|\\\n|'
                    + re_braced(parms.max_depth_br, '', '', '(?:', ')'))
    else:
        atom = r'[^][\\]|\\.|\\\n'
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
def Macro(name, args, repl='', extr=''):
    return (name, args, repl, extr)
def Simple(name, repl='', extr=''):
    return (name, '', repl, extr)
def EquEnv(name, args='', repl=''):
    return (name, args, repl)
def EnvRepl(name, repl=''):
    return (name, repl)
def EnvBegin(name, args='', repl=''):
    return (name, args, repl)
def re_code_args(args, repl, who, s, no_backslash=False):
    # return regular expression for 'OAA' code in args, and modified
    # replacement string repl
    # - do some checks for replacement string repl:
    #   CROSS-CHECK with mark_internal_pre and mark_internal_post
    # - modify replacement:
    #   append mark_deleted to each expanded argument, otherwise problem in
    #   ... \textcolor{red}{This\xyz} is ...
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
        err('no backslashes allowed')
    for m in re.finditer(r'(?<!\\)(?:\\\\)*\\(\d)', repl):
        # avoid exceptions from re module
        n = int(m.group(1))
        if n < 1 or n > len(args) or args[n - 1] not in 'AP':
            err('invalid reference "\\' + m.group(1) + '"')
    if re.search(r'(?<!\\)\\(?:\\\\)*%', repl):
        # ensure that mark_linebreak and mark_deleted do work
        err(r"please use r'\\%' to insert escaped percent sign")
    if repl.endswith('\\') or repl.count('\\\\\\\\'):
        # ensure that double backslashes do not appear in text
        err('backslash at end or insertion of double backslash')

    repl = re.sub(r'((?<!\\)(?:\\\\)*\\(\d))', r'\1' + mark_deleted, repl)
    return (ret, repl)

#   this is an eligible name of a "normal" macro
#
macro_name = r'[a-zA-Z]+'

#   the expression r'\\to\b' does not work as necessary for \to0
#   --> use r'\\to' + end_mac
#
end_mac = r'(?![a-zA-Z])'

#   space that can be consumed after a macro without argument:
#   only consume line break, if non-space on next line found,
#   and if line break not in front of a \begin or \end for environment
#
skip_space_macro = (r'(?:[ \t]*(?:\n(?=[ \t]*\S)(?![ \t]*\\(?:begin|end)'
                            + end_mac + r'))?[ \t]*)')

#   now all is defined to call ...
#
set_math_parms()

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
            # for line number tracking, compare before_output()
            ret += c
    return ret


#######################################################################
#
#   This "reimplementation" of re.sub() operates a small machinery for
#   line number tracking.
#   Argument text is a 2-tuple.
#       text[0]: the text as string
#       text[1]: array with line numbers
#   Return value: tuple (string, number array)
#   As for re.sub(), argument repl may be a callable.
#   Argument track_repl: function for extraction of replacements
#                        and detection of inserted braces etc.
#   Argument only_one: perform at most one replacement
#
#   For each line in the current text string, the number array
#   contains the original line number (before any changes took place).
#   On deletion of line breaks, the corresponding entries in the number
#   array are removed. On creation of an additional line, a negative
#   placeholder is inserted in the number array.
#
def mysub(expr, repl, text, flags=0, track_repl=None, only_one=False):
    (txt, numbers) = text
    res = ''
    last = 0
    for m in re.finditer(expr, txt, flags=flags):
        t = m.group(0)
        if type(repl) is str:
            ex = myexpand(m, repl, text)
        else:
            ex = repl(m)
        if type(ex) is tuple:
            # replacement contains line number information
            (r, nums2) = ex
        else:
            (r, nums2) = (ex, None)

        res += txt[last:m.start(0)]
        last = m.end(0)
        (lin, nt, nr) = mysub_offsets(res, t, r)
        if nums2 is None:
            ll = numbers[lin]
            nums2 = [ll,] + [-abs(ll),] * nr

        if track_repl:
            track_repl((t, numbers[lin:lin+nt+1]), (r, nums2))

        (res, numbers) = mysub_combine(lin, res, r, nt, nr,
                                            numbers, nums2, text)
        if only_one:
            break

    return (res + txt[last:], numbers)

#   will be changed for tracking of character positions
#
def mysub_offsets_lins(res, t, r):
    return (res.count('\n'), t.count('\n'), r.count('\n'))

#   will be changed for tracking of character positions
#
def mysub_combine_lins(lin, res, r, nt, nr, numbers, nums2, text):
    tmp = text_combine((res, numbers[:lin+1]), (r, nums2))
    return text_combine(tmp, ('', numbers[lin+nt:]))

#   combine (add) two text elements with line number information
#   ATTENTION:
#   mysub() depends on the fact that we only look backwards in text1,
#   but not forwards in text2
#
def text_combine_lins(text1, text2):
    (t1, n1) = text1
    (t2, n2) = text2
    if n1[-1] == n2[0] or not t1[t1.rfind('\n')+1:].strip():
        # same line numbers at junction or
        # only space after last line break in text1:
        # use first line number from text2 at junction
        n = n1[:-1] + n2
    else:
        # use last line number from text1 at junction,
        # but attention in case of decreasing line numbers
        j = min(abs(n1[-1]), abs(n2[0]))
        n = n1[:-1] + [-j,] + n2[1:]
    return (t1 + t2, n)

#   prepend and append plain strings to a text with line number information
#
def text_add_frame_lins(pre, post, text):
    return (
        pre + text[0] + post,
        [text[1][0],] * pre.count('\n') + text[1]
                + [text[1][-1],] * post.count('\n')
    )

#   extract text with line number information from a group of a match
#
def text_from_match_lins(m ,grp, text):
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
    (txt, n) = text
    return re.search(expr, txt, flags=flags)
def text_get_txt(text):
    return text[0]
def text_get_num(text):
    return text[1]
def text_new_lins(s=None):
    if s is None:
        return ('', [-1,])
    return (s, list(range(1, s.count('\n') + 2)))


#######################################################################
#
#   the same machinery for tracking of character offset
#
def mysub_offsets_char(res, t, r):
    return (len(res), len(t), len(r))

def mysub_combine_char(pos, res, r, nt, nr, numbers, nums2, text):
    if numbers is text[1]:
        # myexpand() in mysub() still needs the original array
        numbers = numbers.copy()
    numbers[pos:pos+nt] = nums2[:nr]
    return (res + r, numbers)

def text_combine_char(t1, t2):
    return (t1[0] + t2[0], t1[1][:-1] + t2[1])

def text_add_frame_char(pre, post, text):
    return (
        pre + text[0] + post,
        [text[1][0],] * len(pre) + text[1] + [text[1][-1],] * len(post)
    )

def text_from_match_char(m ,grp, text):
    if m.string is not text[0]:
        fatal('text_from_match_char(): bad match object')
    return (m.group(grp), text[1][m.start(grp):m.end(grp)+1])

def text_new_char(s=None):
    if s is None:
        return ('', [-1,])
    return (s, list(range(1, len(s) + 2)))


#######################################################################
#
#   text2txt(): collects all actual work on text input
#   - argument txt: input text string
#   - argument options: options
#   - return: tuple (text string, number array)
#
#######################################################################

def tex2txt(txt, options):

    global mysub_offsets, mysub_combine, text_combine
    global text_add_frame, text_from_match, text_new
    if options.char:
        # track character offsets instead of line numbers
        mysub_offsets = mysub_offsets_char
        mysub_combine = mysub_combine_char
        text_combine = text_combine_char
        text_add_frame = text_add_frame_char
        text_from_match = text_from_match_char
        text_new = text_new_char
    else:
        mysub_offsets = mysub_offsets_lins
        mysub_combine = mysub_combine_lins
        text_combine = text_combine_lins
        text_add_frame = text_add_frame_lins
        text_from_match = text_from_match_lins
        text_new = text_new_lins

    if not options.lang or options.lang == 'de':
        set_language_de()
    elif options.lang == 'en':
        set_language_en()
    else:
        raise_error('problem', 'unrecognized language "' + options.lang
                        + '" given in option --lang', xit=1)

    if options.extr:
        options.extr_list = [m for m in options.extr.split(',') if m]
        options.extr_re = '|'.join(options.extr_list)
    else:
        options.extr_list = []

    global defs
    defs = options.defs

    #   for mysub():
    #   text becomes a 2-tuple of text string and number array
    #
    text = text_new(txt)


    #######################################################################
    #
    #   LAB:VERBATIM
    #   treat verbatim(*) environments and \verb(*) macros
    #   (the given verbatim text is expanded to a coded version that is only
    #    resolved directly at output by before_output())
    #
    #   - expanded content of verbatim(*) environment is enclosed in
    #     \begin{verbatim(*)}...\end{verbatim(*)}
    #       --> blank lines are inserted before and behind this environment
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

    verb_macro_tmp = mark_verbatim_tmp[0] + 'verb' + mark_verbatim_tmp[1]
    verbatim_beg_tmp = (mark_verbatim_tmp[0] + 'verbatim_beg'
                            + mark_verbatim_tmp[1])
    verbatim_end_tmp = (mark_verbatim_tmp[0] + 'verbatim_end'
                            + mark_verbatim_tmp[1])

    # we have to squeeze both variants into one regular expression, because
    # the order of appearance is unknown;
    # vital are the non-greedy repetitions *? in the bodies of \verb and
    # verbatim, as well as in front (group 1); the latter is important in
    # case of nesting
    expr = (r'^(([^\n\\%]|\\.)*?)'
                + r'(?:(\\verb' + end_mac + r'(\*?)([^\s*])(.*?)\5)'
                + r'|(?:' + begin_lbr + r'verbatim(\*?)\}((?:.|\n)*?)'
                        + r'\\end\{verbatim\7\}))')
    def f(m):
        if m.group(3):
            # \verb macro
            ast = m.group(4)
            pre = verb_macro_tmp + ast + '{'
            grp = 6
            post = '}'
        else:
            # verbatim environment
            ast = m.group(7)
            pre = '\n\n' + verbatim_beg_tmp + ast + '}'
            grp = 8
            post = verbatim_end_tmp + ast + '}\n\n'
        def h(m):
            return verbatim(m.group(0), mark_verbatim_tmp, ast)
        verb = mysub(r'.|\n', h, text_from_match(m, grp, text))
        verb = text_add_frame(pre, post, verb)
        return text_combine(text_from_match(m, 1, text), verb)

    # need a loop for replacement
    # - otherwise, e.g., a \verb?%? could hide a \verb later in same line
    # - this calls for verb_macro_tmp etc., as we want to retain \verb etc.
    # - without only_one=True for mysub(), we would fail with:
    #   \verb?%? \begin{verbatim}
    #   \verb?x?
    #   \end{verbatim}
    while mysearch(expr, text, flags=re.M):
        text = mysub(expr, f, text, flags=re.M, only_one=True)

    text = mysub(verb_macro_tmp, r'\\verb', text)
    text = mysub(verbatim_beg_tmp, r'\\begin{verbatim', text)
    text = mysub(verbatim_end_tmp, r'\\end{verbatim', text)


    #######################################################################
    #
    #   LAB:COMMENTS
    #   remove % comments
    #   - line beginning with % is completely removed
    #
    text = mysub(r'^[ \t]*%.*\n', '', text, flags=re.M)

    #   - join current and next lines, if no space before first unescaped %;
    #     skip then leading white space on next line
    #       + not, if next line is empty
    #       + not, if \macro call directly before %
    #
    def f(m):
        if re.search(r'(?<!\\)(\\\\)*\\' + macro_name + r'\Z', m.group(1)):
            # \macro call before %: do no remove line break
            return text_from_match(m, 0, text)
        return text_from_match(m, 1, text)
    text = mysub(r'^(([^\n\\%]|\\.)*)(?<![ \t\n])%.*\n[ \t]*(?!\n)',
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
    def check_nesting_limits(text):
        for m in re.finditer(re_braced(parms.max_depth_br + 1,
                                '(?P<inner>', ')'), text_get_txt(text)):
            if m.group('inner'):
                # innermost {} braces did match
                fatal('maximum nesting depth for {} braces exceeded,'
                        + ' parms.max_depth_br=' + str(parms.max_depth_br),
                            m.group(0))
        for m in re.finditer(re_bracketed(parms.max_depth_br + 1,
                                    '(?P<inner>', ')'), text_get_txt(text)):
            if m.group('inner'):
                fatal('maximum nesting depth for [] brackets exceeded,'
                        + ' parms.max_depth_br=' + str(parms.max_depth_br),
                            m.group(0))
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

    check_nesting_limits(text)

    # check will be repeated during macro expansion and environment handling:
    # - detect insertion of braces, brackets, \begin, or \end
    # - recheck nesting depths
    #
    def mysub_check_nested(expr, repl, text):
        flag = Aux()
        def f(t, r):
            if re.search(r'(?<!\\)[][{}]|\\(begin|end)' + end_mac,
                                    text_get_txt(r)):
                flag.flag = True
        flag.flag = False
        text = mysub(expr, repl, text, track_repl=f)
        if flag.flag:
            check_nesting_limits(text)
        return text

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
    #     RATHER NOT:
    #     resolution order e.g. for \begin{proof}[...] and \begin{proof}?
    #   )
    #
    list_macs_envs = []
    for (name, args, repl, extr) in (
        parms.system_macros()
        + parms.project_macros()
    ):
        if name in options.extr_list:
            continue
        expr = r'\\' + name + end_mac
        (re_args, repl) = re_code_args(args, repl, 'Macro', name)
        if extr:
            (_, extr) = re_code_args(args, extr, 'Macro', name)
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
        list_macs_envs.append((expr, mark_deleted + repl, extr))
    for (name, args, repl) in parms.environment_begins():
        (re_args, repl) = re_code_args(args, repl, 'EnvBegin', name)
        expr = begin_lbr + name + r'\}' + re_args
        list_macs_envs.append((expr, mark_begin_env_sub + repl, ''))

    #   return a text element that only contains the replacements,
    #   separated by blank lines
    #
    def extract_repls(expr, repl, text):
        tmp = Aux()
        tmp.text = text_new()
        def f(t, r):
            r = text_add_frame('\n\n\n', '\n', r)
            tmp.text = text_combine(tmp.text, r)
        mysub(expr, repl, text, track_repl=f)
        return tmp.text

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
        for (expr, repl, extr) in list_macs_envs:
            m = mysearch(expr, text)
            if m:
                match = m
                flag = True
                if extr:
                    # append extracted text to the end of main text
                    e = extract_repls(expr, mark_deleted + extr, text)
                    text = mysub_check_nested(expr, repl, text)
                    text = mysub_check_nested(r'\Z', lambda m: e, text)
                else:
                    text = mysub_check_nested(expr, repl, text)


    ##################################################################
    #
    #   other replacements: collected in list actions
    #   list of 2-tuples:
    #       [0]: search pattern as regular expression
    #       [1]: replacement text
    #
    actions = list(parms.misc_replace())

    def f(m):
        ret = text_from_match(m, 2, text)
        txt = text_get_txt(ret)
        if txt and txt[-1] not in parms.heading_macros_punct:
            ret = text_add_frame('', '.', ret)
        # ensure that preceding and subsequent macros leave space
        return text_add_frame(mark_enforce_linebreak,
                                mark_enforce_linebreak, ret)
    for s in parms.heading_macros():
        actions += [(
            r'\\' + s + r'(?:' + sp_bracketed + r')?' + sp_braced,
            f
        )]

    #   replace $$...$$ by equation* environment
    #
    dollar_dollar_flag = Aux()
    dollar_dollar_flag.flag = False
    def f(m):
        dollar_dollar_flag.flag = not dollar_dollar_flag.flag
        if dollar_dollar_flag.flag:
            return r'\begin{equation*}'
        return r'\end{equation*}'
    actions += [(r'(?<!\\)\$\$', f)]

    # replace $...$ and \(...\) by text from variable parms.inline_math
    # BUG: raises unnecessary warning e.g. on $x \text{ for $x>0$}$
    #
    def f(m):
        m2 = re.search(r'(?<!\\)\$|\\\(|\\\)', m.group(1))
        if m2:
            warning('"' + m2.group(0)
                + '" in {} braces (macro argument?): not properly handled',
                m.group(0))
        # check for trailing interpunction
        m2 = re.search(parms.mathpunct + r'\Z', m.group(1))
        punct = m2.group(0) if m2 else ''
        # rotate placeholder
        parms.inline_math = parms.inline_math[1:] + parms.inline_math[:1]
        return parms.inline_math[0] + punct
    actions += [(r'(?<!\\)\$((?:' + braced + r'|[^\\$]|\\[^()])+)\$', f)]
    actions += [(r'\\\(((?:' + braced + r'|[^\\$]|\\[^()])*)\\\)', f)]

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

    #   fix-text replacements for environments:
    #   check for inclusion of {} etc.
    #
    for (name, repl) in parms.environments():
        env = re_nested_env(name, parms.max_depth_env, '')
        re_code_args('', repl, 'EnvRepl', name, no_backslash=True)
        text = mysub_check_nested(env,
                        mark_begin_env_sub + repl + mark_end_env_sub, text)


    ##################################################################
    #
    #   LAB:ACCENTS
    #   translate text-mode accents to corresponding UTF-8 characters
    #   - if not found: raise warning and keep accent macro in text
    #
    def replace_accent(mac, accent, text):
        def f(m):
            # find the UTF-8 character for the matched letter [a-zA-Z]
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
                warning('could not find UTF-8 character "' + u
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
    #   3. split each 'section' into maths and \text parts
    #
    #   - argument of \text{...} (variable parms.macro_text) is reproduced
    #     without change
    #   - maths parts are replaced by values from variable parms.display_math
    #   - interpunction signs (see variable parms.mathpunct) at end of a
    #     maths part, ignoring parms.mathspace, are appended to replacement
    #   - relational operators at beginning of a maths part are prepended
    #     as ' gleich ...', if maths part is not first on line ('&' is a part)
    #   - other operators like +, -, *, / are prepended e.g. as ' minus ...'
    #   - see variables parms.mathop & parms.mathoptext for text replacements
    #   - the basic replacement steps to next value from parms.display_math,
    #       - if the part includes a leading operator,
    #       - after intermediate \text{...},
    #       - and if last maths part ended with interpunction
    #         (this only for parms.change_repl_after_punct == True)
    #   - maths space (variable parms.mathspace) like \quad is replaced by ' '

    #   Assumptions:
    #   - \\ has been changed to mark_linebreak, & is still present
    #   - macros from LAB:EQU_MACROS already have been deleted
    #   - \text{...} has been resolved not yet
    #   - mathematical space as \; and \quad (variable parms.mathspace)
    #     is still present
    #   - maths macros like \epsilon or \Omega that might constitute a
    #     maths part: still present or replaced with non-space

    def display_math_update():
        parms.display_math = parms.display_math[1:] + parms.display_math[:1]
    def display_math_get(update):
        if update:
            display_math_update()
        return parms.display_math[0]

    #   replace a maths part by suitable raw text
    #
    def math2txt(txt, first_on_line):
        # check for leading operator, possibly after maths space;
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
            # check for leading maths space
            m = re.search(r'\A(' + skip_space + parms.mathspace + r')+', txt)
            if m:
                pre = ' '
                txt = txt[m.end(0):]
            else:
                pre = ''
            update = False

        # check for trailing maths space
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

    #   split a section between & delimiters into \text{...} and maths parts
    #
    def split_sec(txt, first_on_line):
        last = 0
        res = ''
        # iterate over \text parts
        for m in re.finditer(r'\\' + parms.text_macro + sp_braced, txt):
            # maths part between last and current \text
            res += math2txt(txt[last:m.start(0)], first_on_line)
            # content of \text{...}
            res += mark_deleted + m.group(1) + mark_deleted
                # avoid problem e.g. on ... \text{for\quad} x ...
            last = m.end(0)
            first_on_line = False
            display_math_update()
        # maths part after last \text
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

        # important: non-greedy *? repetition, and avoid zero-width matches
        # - do not disrupt trailing maths space like r'\ ' in equation line
        line = (skip_space + r'((.|\n)*?(?!\Z)|(.|\n)+?)(?<!\\)' + skip_space
                    + r'(' + mark_linebreak + r'|\Z)')
        # return replacement for RE line
        def repl_line(m):
            # finally, split line into sections delimited by '&'
            # important: non-greedy *? repetition, avoid zero-width matches
            sec = r'((.|\n)*?(?!\Z)|(.|\n)+?)((?<!\\)&|\Z)'
            flag = Aux()
            flag.first_on_line = True
            def repl_sec(m):
                # split this section into maths and text parts
                # BUG (without warning):
                # we assume that '&' always creates white space
                ret = split_sec(m.group(1), flag.first_on_line) + ' '
                flag.first_on_line = False
                return ret
            t = text_from_match(m, 1, equ)
            t = mysub(sec, repl_sec, t)
            return text_add_frame('  ', '\n', t)

        ret = mysub(line, repl_line, equ)
        if text_get_txt(equ).endswith(mark_linebreak):
            # for example: last equation ends with \\%
            ret = text_add_frame('', '\n', ret)
        return ret

    #   replace equation environments listed above
    #
    for (name, args, replacement) in parms.equation_environments():
        if not replacement:
            (re_args, _) = re_code_args(args, replacement, 'EquEnv', name)
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
        text = mysub_check_nested(env, f, text)

    #   LAB:SPACE
    #   replace space macros including ~, \, and &
    #   replace \\ placeholder
    #   - only after treatment of equation environments
    #
    text = mysub(r'\\,', mark_deleted + utf8_nnbsp, text)
    text = mysub(r'(?<!\\)~', mark_deleted + utf8_nbsp, text)
    text = mysub(r'(?<!\\)&', mark_deleted + ' ', text)
    text = mysub(parms.mathspace, mark_deleted + ' ', text)
    text = mysub(mark_linebreak, mark_deleted + ' ', text)


    #######################################################################
    #
    #   final clean-up
    #
    #######################################################################

    #   only print unknown macros and environments?
    #
    if options.unkn:
        unknowns = ''
        macsknown = (
            'begin', 
            'end',
            'item',
        )
        envsknown = (
            mark_internal_pre,      # compare mark_begin_env
            'itemize',
            'enumerate',
        )
        macs = []
        for m in re.finditer(r'\\(' + macro_name + r')', text_get_txt(text)):
            if m.group(1) not in macs:
                macs += [m.group(1)]
        macs.sort()
        for m in macs:
            if m not in macsknown:
                unknowns += '\\' + m + '\n'
        envs = []
        for m in re.finditer(begin_lbr + r'(' + environ_name + r')\}',
                                text_get_txt(text)):
            if m.group(1) not in envs:
                envs += [m.group(1)]
        envs.sort()
        for e in envs:
            if e not in envsknown:
                unknowns += r'\begin{' + e + '}' + '\n'
        return (unknowns, [])

    #   delete remaining \xxx macros unless given in --extr option;
    #   if followed by braced argument: copy its content
    #
    excl = r'begin|end|item'
    if options.extr:
        excl += r'|' + options.extr_re
    re_macro = r'\\(?!(?:' + excl + r')' + end_mac + r')' + macro_name
                # 'x(?!y)' matches 'x' not followed by 'y'
    re_macro_arg = re_macro + sp_braced
    while mysearch(re_macro_arg, text):
        # macros with braced argument might be nested
        text = mysub(re_macro_arg, mark_deleted + r'\1' + mark_deleted, text)
    text = mysub(re_macro + skip_space_macro, mark_deleted, text)

    #   handle \item without [...] option,
    #   or also with option, if not parms.keep_item_labels
    #   - in itemize environment:
    #     use values from parms.default_item_labs
    #   - LAB:ENUMERATE in enumerate environment:
    #     replace by values from parms.default_item_enum_labs
    #
    itemize_dict = {'itemize': parms.default_item_labs,
                    'enumerate': parms.default_item_enum_labs}

    # a stack to follow nested environments
    # - if a lonely \item appears: pretend to be in itemize
    itemize_stack = [itemize_dict['itemize']]

    # this regular expression matches an \item
    # (\item may skip arbitrary subsequent space) ...
    if parms.keep_item_labels:
        # do not match \item with [...] option (done below at LAB:ITEMS)
        expr = r'(\\item' + end_mac + r'(?!' + sp_bracketed + r')\s*)'
    else:
        # \item option may be present
        expr = r'(\\item' + end_mac + r'(?:' + sp_bracketed + r')?\s*)'
    # ... and \begin / \end for environments listed in itemize_dict
    expr += (r'|(?:\\(begin|end)' + skip_space
                + r'\{(' + r'|'.join(itemize_dict.keys()) + r')\})')

    def f(m):
        if m.group(1):
            # an \item: return value from active label collection, rotate
            lab = itemize_stack[-1][0]
            itemize_stack[-1] = itemize_stack[-1][1:] + itemize_stack[-1][:1]
            return ' ' + lab + ' '
        if m.group(3) == 'begin':
            # entering an environment (group 2 is in sp_bracketed)
            itemize_stack.append(itemize_dict[m.group(4)])
        elif len(itemize_stack) > 1:
            # leaving an environment
            itemize_stack.pop()
        return mark_deleted
    text = mysub(expr, f, text)

    #   delete remaining environment frames outside of equations
    #   - only after treatment of macros: protect line break before \begin;
    #     here we also delete placeholders \begin{%} from above
    #   - only after handling of itemize vs. enumerate
    #
    text = mysub(re_begin_env, mark_deleted, text)
    text = mysub(re_end_env, mark_deleted, text)

    #   LAB:ITEMS
    #   \item(s) with [.] label may pose problems with interpunction checking
    #   - one can simply remove the \item[...] label
    #       - active, if parms.keep_item_labels == False
    #   - one can look backwards in the text and repeat a present
    #     interpunction sign after the item label
    #       - active, if parms.item_label_repeat_punct == True
    #       - works well with (German version of) LanguageTool
    #       - this also checks text in the label
    #       - this should be done after removal of all environment frames
    #         between \item and a previous sentence
    #   (\item[...] may skip arbitrary subsequent space)
    #
    if parms.keep_item_labels:
        if parms.item_label_repeat_punct:
            # try with preceding interpunction [.,;:!?] ...
            def f(m):
                # "manually" build replacement for r'\1 \3\2 ':
                # otherwise, out-of-order inclusion r'\2' would deteriorate
                # line number tracking
                t1 = text_from_match(m, 1, text)
                t3 = text_from_match(m, 3, text)
                t3 = text_add_frame(' ', m.group(2) + ' ', t3)
                return text_combine(t1, t3)
            text = mysub(r'(((?<!\\)[.,;:!?])(?:\s|' + mark_deleted
                            + r')*)\\item' + sp_bracketed + r'\s*', f, text)
        # ... otherwise simply extract the text in \item[...]
        text = mysub(r'\\item' + sp_bracketed + r'\s*', r' \1 ', text)


    ##################################################################
    #
    #   LAB:SPELLING
    #
    ##################################################################

    #   perform replacements in file of option --repl
    #   line syntax:
    #   - '#': comment till end of line
    #   - the words (delimiter: white space) in front of first separated '&'
    #     are replaced by the words following this '&'
    #   - if no replacement given: just delete phrase
    #   - space in phrase to be replaced is arbitrary (but within current
    #     paragraph)
    #
    def do_option_repl(text):
        (lines, fname) = options.repl
        for lin in lines:
            i = lin.find('#')
            if i >= 0:
                lin = lin[:i]
            lin = lin.split()

            t = s = ''
            for i in range(len(lin)):
                if lin[i] == '&':
                    break
                t += s + re.escape(lin[i])
                        # protect e.g. '.' and '$'
                s = r'(?:[ \t]*\n[ \t]*|[ \t]+)'
                        # at least one space character, but stay in paragraph
            if not t:
                continue
            if t[0].isalpha():
                t = r'\b' + t       # require word boundary
            if t[-1].isalpha():
                t = t + r'\b'

            r = ' '.join(lin[i+1:])
            if re.search(r'(?<!\\)%', r):
                fatal('please use escaped \\% for replacement in file "'
                                    + fname + '"', r)
            r = re.sub('\\\\', '\\\\\\\\', r)       # \ ==> \\
            text = mysub(t, r, text)
        return text


    ##################################################################
    #
    #   output of results
    #
    ##################################################################

    #   work to be done just before output
    #
    def before_output(text):
        # if braces {...} did remain somewhere: delete them
        while mysearch(braced, text):
            text = mysub(braced, mark_deleted + r'\1' + mark_deleted, text)

        # remove mark_deleted:
        # delete a line, if it only contains such marks
        text = mysub(r'^([ \t]*' + mark_deleted + r'[ \t]*)+\n', '', text,
                            flags=re.M)
        text = mysub(mark_deleted, '', text)

        # option --repl
        if options.repl:
            text = do_option_repl(text)

        # resolve backslash escapes for {, }, $, %, _, &, #
        # resolve verbatim characters
        # - subsequent replacement runs would lead to mistakes
        def f(m):
            if m.group(1):
                return m.group(1)
            c = chr(int(m.group(2)))
            if c == '\n':
                # for line number tracking, compare verbatim()
                return ''
            return c
        text = mysub(r'\\([{}$%_&#])|' 
                + mark_verbatim[0] + r'(\d+)' + mark_verbatim[1], f, text)
        return text

    if options.extr:
        # on option --extr: only print arguments of these macros
        expr = (r'\\(?:' + options.extr_re + r')(?:' + sp_bracketed
                        + r')*' + sp_braced)
        text = extract_repls(expr, r'\2', text)

    text = before_output(text)
    if warning_or_error.msg:
        # there was a problem: include message, clear for next call
        text = text_add_frame(warning_or_error.msg, '', text)
        warning_or_error.msg = ''
    return text

####################################################
#
#   end of function tex2txt()
#
####################################################

#   output of text string and line number information
#
def write_output(text, ft, fn):
    if ft:
        ft.write(text_get_txt(text))
    if fn:
        for n in text_get_num(text):
            s = str(abs(n))
            if n < 0:
                s += '+'
            fn.write(s + '\n')

#   function for translation of line and column numbers
#
def translate_numbers(tex, plain, charmap, starts, lin, col):

    if lin < 1 or col < 1:
        return None

    # get start position of line number lin in plain
    if lin > len(starts):
        return None
    n = starts[lin - 1]

    # add column number col
    s = plain[n:]
    i = s.find('\n')
    if i >= 0 and col > i or i < 0 and col > len(s):
        # line is not that long
        return None
    n += col - 1

    # map to character position in tex
    if n >= len(charmap):
        return None
    n = charmap[n]
    if n < 0:
        flag = True
        n = -n
    else:
        flag = False

    # get line and column in tex
    if n > len(tex):
        return None
    s = tex[:n]
    lin = s.count('\n') + 1
    col = len(s) - (s.rfind('\n') + 1)

    r = Aux()
    r.lin = lin
    r.col = max(1, col)
    r.flag = flag
    return r

#   auxiliary function for translation of line and column numbers
#
def get_line_starts(s):
    return list(m.start(0) for m in re.finditer(r'\n', '\n' + s))

#   function for reading replacement file
#
def read_replacements(fn, encoding):
    if not fn:
        return None
    f = myopen(fn, encoding=encoding)
    lines = f.readlines()
    f.close()
    return (lines, fn)

#   function for reading definition file
#
def read_definitions(fn, encoding):
    if not fn:
        return Definitions(None, '?')
    f = myopen(fn, encoding=encoding)
    s = f.read()
    f.close()
    return Definitions(s, fn)

#   class for parsing of file from option --defs
#
class Definitions:
    def __init__(self, code, name):
        self.project_macros = ()
        self.system_macros = ()
        self.heading_macros = ()
        self.environments = ()
        self.equation_environments = ()
        self.environments = ()
        self.environment_begins = ()
        self.theorem_environments = ()
        self.misc_replace = ()
        if code:
            defs = self
            try:
                exec(code)
            except BaseException as e:
                import traceback
                i = 0 if isinstance(e, SyntaxError) else -1
                s = traceback.format_exc(limit=i)
                s = re.sub(r'\ATraceback \(most recent call last\):\n'
                                + r'  File "<string>"(, line \d+).*\n',
                                r'File "' + name + r'"\1\n', s)
                fatal('problem in file "' + name + '"\n' + s)

#   class for passing options to tex2txt()
#   LAB:OPTIONS
#
class Options:
    def __init__(self,
            repl=None,      # or set by read_replacements()
            char=False,     # True: character position tracking
            defs=None,      # or set by read_definitions()
            extr=None,      # or string: comma-separated macro list
            lang=None,      # or set to language code
            unkn=False):    # True: print unknowns
        self.repl = repl
        self.char = char
        self.defs = defs
        if not self.defs:
            # need default defs object
            self.defs = read_definitions(None, '?')
        self.extr = extr
        self.lang = lang
        self.unkn = unkn

#   function to be called for stand-alone script
#
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='?')
    parser.add_argument('--repl')
    parser.add_argument('--nums')
    parser.add_argument('--char', action='store_true')
    parser.add_argument('--defs')
    parser.add_argument('--extr')
    parser.add_argument('--lang')
    parser.add_argument('--ienc')
    parser.add_argument('--unkn', action='store_true')
    cmdline = parser.parse_args()

    if not cmdline.ienc:
        cmdline.ienc = 'utf-8'

    options = Options(
                repl=read_replacements(cmdline.repl, encoding=cmdline.ienc),
                char=cmdline.char,
                defs=read_definitions(cmdline.defs, encoding='utf-8'),
                                    # the Python code should be UTF-8
                extr=cmdline.extr,
                lang=cmdline.lang,
                unkn=cmdline.unkn)

    if cmdline.file:
        f = myopen(cmdline.file, encoding=cmdline.ienc)
        txt = f.read()
        f.close()
    else:
        # reopen stdin in text mode: handling of '\r', proper decoding
        txt = open(sys.stdin.fileno(), encoding=cmdline.ienc).read()

    if cmdline.nums:
        cmdline.nums = myopen(cmdline.nums, encoding='utf-8', mode='w')

    # ensure UTF-8 output under Windows, too
    sout = open(sys.stdout.fileno(), mode='w', encoding='utf-8')
    text = tex2txt(txt, options)
    write_output(text, sout, cmdline.nums)
    if cmdline.nums:
        cmdline.nums.close()

if __name__ == '__main__':
    # used as stand-alone script
    main()

