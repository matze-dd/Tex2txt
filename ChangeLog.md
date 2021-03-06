Version 1.7.0
-------------
- tex2txt.py: fixed bug in RE for macro \\(re)newcommand
  (problematic escape sequence detected by pytest)
- shell.py
    - new option --list-unknown: show unknown macros and environments
    - new option variant '--server stop': stop a local LT server
      (currently only works under Linux and Cygwin)
- added tests
    - for tex2txt.py
    - a simple test for shell.py
- all Python scripts: use sys.exit() instead of exit()
- README.md: updated, included reference to pandoc

Version 1.6.9
-------------
- shell.py
    - added mode argument to option --server: can use a local LT server
    - new option --textgears: use TextGears server
    - added option --lt-options: passes further options to LT
    - added option --lt-server-options: further options for local LT server
    - added some translation between CLI options for --lt-options and
      HTML request fields, see script variable lt\_option\_map
    - added config file, name in script variable config\_file
    - index in HTML report: use red colour for files with problems
      <br><br>
    - tidied up script options
- README.md: updated

Version 1.6.8
-------------
- tex2txt.py: changed equation replacements for English and German,
  compare [Issue #22](../../issues/22)
- checks.sh: adapted to new equation replacements (exception patterns for
  single letters)
- shell.py
    - new option --server: use LT's Web server instead of local installation
    - new option --single-letters accept: check for single letters,
      accepting occurences in given patterns
    - new option --equation-punctuation: hack for finding missing dots at
      the end of equations in English texts
    - HTML report: slightly adapted tooltip format
    - HTML report: display line numbers for overlapping LT messages, too
      (was: only shown in corresponding tooltip)
    - HTML report: if highlighting of a word is unsure (yellow colour),
      then mark till end of word (was: mark only one character)
    - text report: sort messages according to position in LaTeX text
      <br><br>
    - text report: apply LT's JSON interface, too
    - catch exceptions when using Java or LT server
    - fixed [Issue #21](../../issues/21) and a similar problem
      (less "unsure localisation", yellow colour)
- shell2.py: added usage comments, simpler call of os.getenv()
- Example.md, Example2.md: updated with new equation replacements
- shell.png: updated
- README.md: updated

Version 1.6.7
-------------
- tex2txt.py
    - added second optional argument to macro \\newcommand
    - added macro \\renewcommand
- new application script shell.py: combined version of old scripts
  shell2.py and shell2-html.py, mainly controlled by command-line options
    - option --include: tracking of file inclusions
    - option --extract: allows to check marked foreign-language text
    - option --skip: exclude certain input files
    - option --link: in HTML report, a Web link provided by LT message can
      be opened with left-click on corresponding highlighted place
    - option --plain: do not evaluate LaTeX syntax
    - added error checks for JSON output from LT
- slightly simplified shell2.py
- removed shell2-html.py
- README.md
    - changed introductory example, added screen shot of HTML report
    - added documentation for shell.py
    - removed description of shell2.py, shell2-html.py

Release 1.6.6
-------------
- added demo file HTML-report.md for application script shell2-html.py
- tested with Python version 3.8 and LanguageTool version 4.7
- simpler and faster implementation of function mysub\_combine\_char()
- fixed bug: 'x\\footnotemark\<line break\>\\section{Title}'
  produced 'xTitle.'
- Remark: the simple scheme with mark\_enforce\_linebreak can perhaps replace
  the rather complicated and error-prone mechanism with mark\_begin\_env,
  mark\_end\_env and spkip\_space\_macro (protects beginnings of environments)
- README.md: added reference to pylatexenc

Release 1.6.5
-------------
- tex2txt.py:
    - added option --ienc for input encoding
    - ensure UTF-8 encoding for stdout under Windows, too
    - added macro \\title to collection parms.heading\_macros
    - fixed problem in [issue #7](../../issues/7), BUT has to be activated
      in variable parms.recognise\_braces\_in\_brackets
    - function myopen() requires mandatory argument 'encoding'
    - read\_definitions() and read\_replacements() require 'encoding' argument
- shell2-html.py:
    - only display excerpts from input text together with line numbers,
      controlled by variable context\_lines
    - enforce UTF-8 encoded standard output, added HTML \<meta\> tag for
      UTF-8 encoding
- shell2\*.py:
    - input encoding set by variable input\_encoding
    - explicitly use "encoding='utf-8'" for encode(), decode()
- README.md: added details for shell2-html.py and encoding problems

Release 1.6.4
-------------
- added macro \\par to collection in parms.system\_macros
- inline equations: trailing interpunction from parms.mathpunct is appended
  to placeholder
- better Python practice: explicitly close used files
- fixed bug: tex2txt() changed globals and didn't restore them;
  would pose problems, if one reimplemented Bash script checks.sh in Python
  <br><br>
- shell2-html.py:
    - use '\&ensp;' instead of '\&nbsp;' as space character:
      long lines will be broken in browser
    - add border to highlighted places: delimits subsequent ones
    - use different highlighting colour in case of unsure problem localisation
- shell2.py: detect usage under Windows from environment variable OS
- README.md: introductory summary and section on principal limitations,
  other minor additions

Release 1.6.3
-------------
- version that also can be used as Python module:
  starting at the creation of the 2-tuple (text string, number array),
  all code has been put into a large function tex2txt()
- added functions for translation of line and column numbers
- enforce UTF-8 encoding in myopen(): otherwise, native Windows Python may
  cause problems
- stored Python scripts in Windows CRLF format
  <br><br>
- shell2.py: an example application that is equivalent to Bash script
  shell2.sh; no auxiliary files are created
- shell2-html.py: generation of HTML report similar to TeXtidote
- README.md: added sections on usage as module, and on working directly
  under Windows

Release 1.6.2
-------------
- improved character position tracking for line join by % comment
- reimplemented handling of \\verb macro and verbatim environment:
  fixed bugs from [issue #19](../../issues/19)
- reopen of stdout was redundant (but that for stdin is not)

Release 1.6.1
-------------
- added option --char: number file from option --nums will contain
  character offsets
- [shell2.sh](shell2.sh): new Bash script with output filter for line and
  column numbers
- [Example2.md](Example2.md): demonstration of script [shell2.sh](shell2.sh)
- checks.sh: added option --columns for column number correction
  <br><br>
- heading macros like \\section: better line tracking
- application of changed function text\_new()
- use list instead of tuple for position number array; tailoring in mysub()
  then allows speed-up for large files on option --char
- reopen stdin and stdout: handling of '\\r' as for text files

Release 1.6.0
-------------
- functions Macro() and Simple(): new optional argument 'extr';
  applied for macros \\caption, \\footnote, \\footnotetext
- on option --repl: respect paragraph boundaries during phrase replacement
- added '\\\<tab\>' to spacing macro collection in parms.mathspace,
  as well as macros \\thinspace, \\medspace, and \\thickspace
- checks.sh: simplified thanks to new argument 'extr' of Macro()
  <br><br>
- fixed bug in parse\_equ(): trailing space as '\\ ' could hide interpunction
  (has been solved in release 1.0.1 and re-introduced :-( in release 1.5.6)
- fixed bug in mysub\_check\_nested(): detection of "dangerous" replacements
  was a bit sloppy
- function mysub(): merged arguments 'extract' and 'track\_repl'
- restructured code for script output
- functions like Macro(): in replacements, do not accept r'\\d' references
  to optional arguments
- fixed bug from [issue #17](../../issues/17): function text\_combine()
  did not recognise case of falling line numbers;
  fixed now uncovered problem with out-of-order replacement for item labels

Release 1.5.9
-------------
- fixed bug triggered e.g. by 'python3 tex2txt.py --extr , t.tex':
  was not treated as empty list of macros
- fixed bugs from [issue #16](../../issues/16): function before\_output()
  now collects all final clearing steps
- revised error messages
- shell.sh: LaTeX file name now given as script parameter
- Example.md: updated accordingly

Release 1.5.8
-------------
- fixed bug from [issue #15](../../issues/15) for "undeclared" macros, too

Release 1.5.7
-------------
- fixed bug with option --unkn: itemize and enumerate environments
  are not listed as undeclared any more
- function parse\_equ():
    - now avoid zero-width matches
      --> corresponding missplaced check in mysub() could be removed
    - recognize \\\\ directly at end of an equation environment, e.g. as \\\\%
- fixed bugs in text mode: \\quad did not work, and a lonely \\; could leave
  a blank line
- fixed bug in split\_sec(): problem appeared e.g. on
  \\\[ ... \\text{for\\quad} x ... \\\]
- fixed bug from [issue #15](../../issues/15): modifications in function
  re\_code\_args()
- checks.sh: fixed bug, tracking of file inclusions with option --recurse
  now takes account of definitions from $tex2txt\_defs

Release 1.5.6
-------------
- fixed bug in function calc\_numbers(), shifted its code into now
  simplified function mysub()
- simplified function text\_combine()
- change in parse\_equ(): better line number tracking for last equation
  in an equation environment
- added default label collection parms.default\_item\_enum\_labs
  for \\item in enumerate environment
- added variable parms.item\_label\_repeat\_punct to control repetition
  of preceding punctuation after an \\item\[...\] label
- Example.md: updated
- README.md: added section on declaration of LaTeX macros, updated

Release 1.5.5
-------------
- better % comment handling on line join: leading space on next line will
  be skipped (like TeX, one could skip leading space in general, but this
  would unnecessarily reduce similarity of input and output text)
- improved protection against inclusion of unescaped % signs during
  macro expansion (function re\_code\_args())
- handling of \\caption{...} in own text flow (like footnotes)
    - tex2txt.py: do not copy argument of macro caption
    - checks.sh: extract caption argument to file with footnote texts

Release 1.5.4
-------------
- fixed bug: \\footnote and \\footnotemark should not leave a number,
  this may hide mistakes or cause false positives
- inline math \\(...\\) treated like $...$
- Bash script checks.sh:
    - added check that auxiliary files are created inside of $txtdir
    - added option --recurse, will recursively track \\input{...} macros
    - only adapt LT's files spelling.txt and prohibit.txt on option --adapt-lt
    - renamed other command-line options
    - added license header, shifted documentation to README.md

Release 1.5.3
-------------
- closed issue #5 (once again :-(): now {} braces and \[\] brackets as well
  as \\begin and \\end of environments are checked during macro expansion and
  fix-text replacement of environments
- fixed bug: macro now also won't consume line break in front of \\end{...}
  (variable skip\_space\_macro)

Release 1.5.2
-------------
- merged commit from pull request #11, **thanks to** symphorien:
  inline math $...$ should not be replaced with 'A' in English
- closed issue #5: nesting depths now are checked, if a macro substitution
  inserts additional {} braces

Release 1.5.1
-------------
- closed issue #3: now line number tracking in multi-line macro arguments
  does work better
- fixed bug (issue #4): now reject insertion of raw % in file from --repl
- filter in shell.sh now ignores column numbers; Example.md updated;
  same change in checks.sh

Release 1.5.0
-------------
- improved line number tracking inside of displayed equations:
  closed issue #2, updated Example.md
- added macros \\verb(\*) and environments verbatim(\*), see LAB:VERBATIM
- added macros \\textbackslash, \\textasciicircum and \\textasciitilde:
  the raw characters \\ and \^ and \~ cannot be obtained via escaping
- slightly re-organized comment removal and replacement of double
  backslash \\\\

Release 1.4.2
-------------
- fixed bug: sequence backslash-linebreak ('\\\\\\n') now creates ' ' space
    - added to parms.mathspace
    - allowed in regular expressions for nested \{...\}, \[...\],
      and for \$...\$
- fixed bug: tilde ~ inside of equations was not considered as math space
- fixed bug: do not expand german-language macros like \"\= and \"\'
  for other language of option --lang
- Example.md: added script output with filtered LT messages

Release 1.4.1
-------------
- removed use of lambda in file of option --defs: allows for better error
  messages
- added missing replacements:
    - escaped hash \\\# substituted by raw \#
    - escaped ampersand \\\& substituted by raw \& and raw \& by space
    - narrow space \\, substituted by UTF8 narrow non-breaking space instead
      of ASCII space
- Example.md: removed unneccesary space in \\text in cases environment
- exceptions from file operations now are caught
- changed function fatal(): simply print message and exit, no exception

Release 1.4.0
-------------
- fixed bug: expansion of a macro declared with mandatory arguments but
  actually used without any arguments enclosed in braces or brackets
  (could even lead to exceptions for Python \< 3.5);
  now, these macros are treated as unknown and listed by option --unkn
- shifted expansion of declared macros to the beginning, improved handling of
  recursion
- added checks for macro and environment replacement strings: they should
  not insert \\\\ or unescaped % signs
- remarkable speed-up from using string.count('\\n') instead of
  len(re.findall(r'\\n', string))
  <br><br>
- added option --defs for reading additional declarations from file
- removed some 'private' macro declarations from Python script
- now replace \~ by UTF8 non-breaking space instead of ASCII ' '
- updated Bash script checks.sh

Release 1.3.7
-------------
- fixed bug: line number tracking was incorrect when joining lines
- fixed bug: handling of option \[...\] for \\\\ was restricted
- internal representation of \\\\ changed \[again :-(\] to now %%L%%
  (this is save, because unescaped % signs are deleted at the beginning)
- resolution of \\\_ shifted to resolve\_escapes()
- removed "historical" eat\_eol and eol2space

Release 1.3.6
-------------
- fixed bug: internal representation of '\\\\' was '\\newline';
  changed to '\_\_\_'
    - 'X\\\\Y' internally became 'X\\newlineY' und then quite probably 'X'
    - '\\\\' could consume white space till braced text on next line
    - confusion with real macro \\newline
- fixed bug: do not join lines at unescaped % sign that follows non-space
    - if next line is empty
    - if a \\macro is just in front of %
- centralized more regular expressions in variables
- README: added section on handling of displayed equations

Release 1.3.5
-------------
- fixed bug: $...$ must contain at least one character
- $$...$$ handled like equation* environment

Release 1.3.4
-------------
- added accents as \\', \v, ... in text mode;
  warning, if corresponding UTF8 character is not available
- added macros as \ae, \L, ... for special characters and ligatures
- fixed bug: parms.mathpunct did not exclude \\.
- changed variable parms.warning_error_msg

Release 1.3.3
-------------
- added argument code 'P' for Macro(), allows for instance simpler handling
  of \cite macro
- related: harmonized treatment of theorem environments, proof environment,
  and environments with arguments at \begin
- added English theorem environments
- removed introductory Python script comments that are duplicated in README
- Bash script checks.sh: subdirectories in $txtdir created, if necessary

Release 1.3.2
-------------
- fixed similar bug as in 1.3.1; avoid for instance that<br>
  'A\notag \color{red} B' produces 'AB',<br>
  since '\color' is removed first and '\notag' consumes the space till 'B'
- simplified mechanism for suppression of new empty lines

Release 1.3.1
-------------
- fixed bug: macro without argument won't consume leading space that is part
  of a subsequent environment
  (see also section 'Implementation issues' in REAMDE.md)
- before output: resolve backslash escapes for {, }, $, %

Release 1.3.0
-------------
- fixed bug: between macro name and its arguments no paragraph break allowed;
  the same holds for elements of an environment frame
  (arbitrary space was accepted before)
- fixed bug: after a macro without arguments, now arbitrary white space in
  current paragraph is consumed (was before: only space removal if rest of
  line is empty)
- related: now replacement of space from parms.mathspace and ~ by ' '
  as well as deletion of \!, \- and "- only after macro treatment
- fixed bug: \item[...] will skip arbitrary following white space
- introduced variable parms.default_item_lab
- re-work of mechanism for suppression of new empty lines
  (eat_eol and eol2space)
- added option --unkn: print list of "undeclared" macros and environments

Release 1.2.0
-------------
- simpler treatment of \\[...\\]: equivalent to begin/end of equation*
  environment; allows to better tailor equation replacement
- with option --extr, optional macro arguments \[...\] are skipped;
  e.g., for extracting from \footnote\[n\]{...}
- declaration of title names for environments in parms.theorem_environments;
  used before: capitalized version of environment name
- for consistency, now all collections parms.xyz use lambdas
- variables max_depth_xyz for maximum nesting depths shifted to object parms
- simpler implementation for %-comment if joining lines
- checked with LanguageTool 4.4 (de-DE) and large 'text under test'

Release 1.1.1
-------------
- fixed bug (missing recognition of macro name boundary):
  with option '--extr m', the input 'aa\m{\mm{xyz}}bb' produced output
  '\mm{xyz}' instead of 'xyz'
- check for interpunction '!' and '?' at LAB:ITEMS
- simpler implementation of rotating equation replacements
- reduced code redundancy for creation of line number file

Release 1.1.0
-------------
- shifted language settings to "declaration" section
- replacements for inline equations and math parts in displayed equations
  rotate from given collections;<br>
  this avoids unnecessary warnings due to word repetition;<br>
  missing interpunction / operators can be detected as before
- see file 'Example' and LAB:EQUATIONS in the script for summary of operation
- (for German LanguageTool, moving from fixed '$$' and '§§' replacement
  to this scheme detected a few more shortcomings in the 'text under test')

Release 1.0.1
-------------
- fixed bug: in equations, trailing space r'\ ' of math parts was
  not recognized;<br>
  also understand \mbox{} in front of an operator (additionally to {})

Release 1.0.0
-------------
- added collection 'parms.project_macros' for project-specific macros,
  renamed 'parms.the_macros' to 'parms.system_macros'
- added helper Simple() for declaration of macros without arguments
- fixed bug: macro names end at digits; for instance, \to0 now is correctly
  recognized as equivalent with \to 0

Release 0.2.0
-------------
- more flexible declaration of macros / environments with tailored treatment
- recognize \\[...\\] displayed equations
- only delete environment \begin{...} with option or argument, if declared
  (was a bit sloppy before)
- check nesting depths of {} braces, \[\] brackets, and environments
- warnings / errors will print a mark to be found by the language checker

Release 0.1.0
-------------
- added templates for macros with 2 and 3 arguments to be ignored or
  with last argument to be kept
- \LTskip, \item without \[\], and \newcommand{}\[\]{} won't leave blank line
- corrected some typos in comments

Initial Version
---------------
- first upload
