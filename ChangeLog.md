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
