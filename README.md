Tex2txt, a filter for mathematical texts
========================================
Problem
-------
Unfortunately, there is a naming conflict with the related Haskell package.
We ask for apology.

Description
-----------
This is a Python script for extracting raw text from LaTeX documents with focus on mathematics.
The aim is to produce only few "false" warnings when feeding the text into a language checker.

In some sense, the script compares to tools like OpenDetex, TeXtidote and the above-mentioned Haskell software.
As in TeXtidote, we make an effort to track line numbers.
Unnecessary creation of empty lines is avoided, paragraphs and sentences remain intact.
The Bash script shell.sh shows an example for filtering messages from a language checker.

An optional speciality is some parsing of LaTeX environments for displayed equations.
Therefore, one can check embedded \text{...} parts (LaTeX package amsmath) and interpunction in—not too complex—displayed equations.
An example is shown in file Example, operation is summarized in the script at label LAB:EQUATIONS.

The starting section of the Python script lists macros and environments with tailored treatment.
This should ease adaptation to own needs.

A more complete Bash script for language checking of a whole document tree is checks.sh.

Usage
-----
python3 tex2txt.py \[--nums file\] \[--repl file\] \[--extr list\] \[--lang xy\] \[--unkn\] \[file\]

- without argument file: read standard input
- option --nums file<br>
  file for storing original line numbers;
  can be used later to correct line numbers in messages
- option --repl file<br>
  file with phrase replacements performed at the end, namely after
  changing inline maths to text, and German hyphen "= to - ;
  see LAB:SPELLING in script for line syntax
- option --extr ma\[,mb,...\] (list of macro names)<br>
  extract only first braced argument of these macros;
  useful, e.g., for check of foreign-language text and footnotes
- option --lang xy<br>
  language de or en, default: de;
  used for adaptation of equation replacements, math operator names,
  proof titles, and replacement of foreign-language text;
  see LAB:LANGUAGE in script
- option --unkn<br>
  print list of "undeclared" macros and environments outside of equations

Selected actions
----------------
- frames \begin{...} and \end{...} of environments are deleted;
  tailored behaviour for environment types listed in script
- flexible treatment of own macros with arbitrary arguments
- text in heading macros as \section{...} is extracted with
  added interpunction
- suitable placeholders for \ref, \eqref, \pageref, and \cite
- "undeclared" macros are silently ignored, keeping their arguments
- inline math $...$ is replaced with text from rotating collection
  in variable parms.inline_math
- equation environments are resolved in a way suitable for check of
  interpunction, argument of \text{...} is included into output text;
  \\[...\\] is same as environment equation*; <br>
  see file Example and LAB:EQUATIONS in the script for example and
  detailed description
- some treatment for \item\[...\] labels, see LAB:ITEMS in script
- characters with text mode accents as \\' are translated into 
  corresponding UTF8 characters
- rare warnings can be suppressed using \LTadd{}, \LTskip{},
  \LTalter{}{} in the LaTeX text with suitable macro definition there;
  e.g., adding something that only the language checker should see:<br>
  \newcommand{\LTadd}\[1\]{}

Implementation issues
---------------------
In order to parse with regular expressions, some of them are constructed by iteration.
At the beginning, we hence check for instance, whether nested {} braces of the actual input text do overrun the corresponding regular expression.
In that case, an error message is generated and the variable parms.max_depth_br for maximum brace nesting depth has to be changed.
Setting control variables for instance to 100 does work, but also increases resource consumption.

A severe general problem is order of macro resolution.
While TeX strictly evaluates from left to right, the order of treatment by
regular expressions is completely different.
This calls for hacks like the regular expression in skip_space_macro together
with the placeholder \begin{%};
it aims to avoid that a macro without arguments consumes leading space
inside of an already resolved following environment.

Overall, parsing with regular expressions is fun, but remains a rather coarse
approximation of the "real thing".
Nevertheless, it seems to work quite well in practice, and it gives good
flexibility.

