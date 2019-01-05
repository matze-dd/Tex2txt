Release 1.3.1
-------------
- fixed bug: macro without argument won't consume leading space that is part
  of a subsequent environment
  (see also section 'Inplementation issues' in REAMDE.md)
- before ouptut: resolve backslash escapes for {, }, $, %

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

