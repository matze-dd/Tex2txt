# Tex2txt: a flexible LaTeX filter with tracking of line numbers or character positions
[General description](#general-description)&nbsp;\|
[Selected actions](#selected-actions)&nbsp;\|
[Command line](#command-line)&nbsp;\|
[Usage under Windows](#usage-under-windows)&nbsp;\|
[Tool integration](#tool-integration)&nbsp;\|
[Encoding problems](#encoding-problems)&nbsp;\|
[Declaration of LaTeX macros](#declaration-of-latex-macros)&nbsp;\|
[Handling of displayed equations](#handling-of-displayed-equations)&nbsp;\|
[Application as Python module](#application-as-python-module)&nbsp;\|
[Remarks on implementation](#remarks-on-implementation)

**Summary and example.**
This Python software extracts plain text from LaTeX documents.
Due to the following characteristics, it is suitable for integration with
a proofreading software:
- tracking of line or character positions during text manipulations,
- simple inclusion of own LaTeX macros and environments with tailored
  treatment,
- careful conservation of text flows,
- detection of interpunction in displayed equations.

For instance, the LaTeX input
```
This is\footnote{A footnote may be set
in \textcolor{red}{redx colour.}}
is the main text.
```
will lead to the subsequent output from example application script
[shell2.py](shell2.py) described in section
[Application as Python module](#application-as-python-module).
As proofreading software, the script uses
[LanguageTool](https://www.languagetool.org).
```
test.tex
========
1.) Line [1], column [6], Rule ID: ENGLISH_WORD_REPEAT_RULE
Message: Possible typo: you repeated a word
Suggestion: is
This is is the main text.    A footnote may be set in r...
     ^^^^^                                             

test.tex
========
2.) Line [2], column [20], Rule ID: MORFOLOGIK_RULE_EN_GB
Message: Possible spelling mistake found
Suggestion: red; Rex; reds; redo; Red; Rede; redox; red x
...s the main text.    A footnote may be set in redx colour. 
                                                ^^^^        
```

## General description
This is a modest, self-contained [Python](https://www.python.org)
script for the extraction of plain text from
[LaTeX](https://www.latex-project.org) documents.
It can also be used as Python module.
In some sense, it relates to tools like
[OpenDetex](https://github.com/pkubowicz/opendetex),
[TeXtidote](https://github.com/sylvainhalle/textidote), and
[tex2txt](http://hackage.haskell.org/package/tex2txt).
For the naming conflict with the latter project, we want to apologise.

While virtually no text should be dropped by the filter,
our aim is to provoke as few as possible “false” warnings when the result
is fed into a proofreading software.
The goal especially applies to documents containing displayed equations.
Problems with interpunction and case sensitivity would arise, if
equation environments were simply removed or replaced by fixed text.
Altogether, the script can help to create a compact report from language
examination of a single file or a complete document tree.
Simple and more complete applications are addressed in sections
[Tool integration](#tool-integration) and
[Application as Python module](#application-as-python-module) below.

For ease of problem localisation, we implement a mechanism that tracks
line number changes during the text manipulations.
Unnecessary creation of empty lines therefore can be avoided, sentences
and paragraphs remain intact.
This is demonstrated in file [Example.md](Example.md).
Reconstruction of both line and column numbers is possible with script
option --char, which activates position tracking for each single character
of input.
File [Example2.md](Example2.md) shows such an application.
Very large input texts can lead to slow operation, however.

The first part of the Python script gathers LaTeX macros and environments
with tailored treatment, which is shortly described
in section [Declaration of LaTeX macros](#declaration-of-latex-macros).
Some standard macros and environments are already included, but very probably
the collections have to be complemented.
With option --defs, definitions also can be extended by an additional file.

Unknown LaTeX macros and environments are silently ignored while keeping their
arguments and bodies, respectively; script option --unkn will list them.
Declared macros can be used recursively.
As in TeX, macro expansion consumes white space (possibly including a line
break) between macro name and next non-space character within the current
paragraph.

Extra text flows like footnotes are normally appended to the end of the
main text flow, each separated by blank lines.
The introductory summary above shows an example.
Activation of this behaviour is demonstrated for macro \\caption{...}
in section [Declaration of LaTeX macros](#declaration-of-latex-macros).
Script option --extr provides another possibility, which is also useful for
the extraction of foreign-language text.

An optional speciality is some parsing of LaTeX environments for displayed
equations.
Therefore, one may check embedded \\text{...} parts (macro from LaTeX package
amsmath), and trailing interpunction of these equations
can be taken into account during language check of the main text flow.
Further details are given in section
[Handling of displayed equations](#handling-of-displayed-equations).
An example is shown in file [Example.md](Example.md), operation is summarised
in the script at label LAB:EQUATIONS.

Application as Python module is shortly described in section
[Application as Python module](#application-as-python-module) below.

The Python script may be seen as an exercise in application of regular
expressions.
Its internal design could be more orderly.
Currently, it is mainly structured by comments, and it mixes definitions of
variables and functions with statements that actually perform text replacement
operations.
In section [Remarks on implementation](#remarks-on-implementation),
some general techniques and problems are addressed.

If you use this tool and encounter a bug or have other suggestions
for improvement, please leave a note under category [Issues](../../issues),
or initiate a pull request.
Many thanks in advance.
(See, for example, the problem in section
[Replacements in English documents](#replacements-in-english-documents)
below.)

Happy TeXing!

[Back to top](#tex2txt-a-flexible-latex-filter-with-tracking-of-line-numbers-or-character-positions)

## Selected actions
Here is a list of the most important script operations.

- flexible treatment of own macros with arbitrary LaTeX-style arguments;
  see section [Declaration of LaTeX macros](#declaration-of-latex-macros),
  and label LAB:MACROS in script
- “undeclared” macros are silently ignored, keeping their arguments
  with enclosing \{\} braces removed
- frames \\begin\{...\} and \\end\{...\} of environments are deleted;
  tailored behaviour for environment types listed in script
- text in heading macros as \\section\{...\} is extracted with
  added interpunction (suppresses false positives from LanguageTool)
- suitable placeholders for \\ref, \\eqref, \\pageref, and \\cite
- inline maths $...$ and \\(...\\) is replaced with text from rotating
  collection in variable parms.inline\_math in script
- equation environments are resolved in a way suitable for check of
  interpunction and spacing, argument of \\text\{...\} is included into output
  text; \\\[...\\\] and $$...$$ are same as environment equation\*;
  see the section
  [Handling of displayed equations](#handling-of-displayed-equations),
  file [Example.md](Example.md), and LAB:EQUATIONS in script
- some treatment for specified \\item\[...\] labels, see LAB:ITEMS in script
- default \\item labels in enumerate environment are taken from rotating
  collection in script variable parms.default\_item\_enum\_labs
- letters with text-mode accents as '\\\`' or '\\v' are translated to 
  corresponding UTF-8 characters, see LAB:ACCENTS in script
- replacement of things like double quotes '\`\`' and dashes '\-\-' with
  corresponding UTF-8 characters;
  replacement of '\~' and '\\,' by UTF-8 non-breaking space and
  narrow non-breaking space
- treatment of \\verb(\*) macros and verbatim(\*) environments,
  see LAB:VERBATIM in script; note, however, [issue #6](../../issues/6)
- handling of % comments near to TeX: skipping of line break under certain
  circumstances, see LAB:COMMENTS in script
- rare warnings from proofreading program can be suppressed using \\LTadd{},
  \\LTskip{}, \\LTalter{}{} in the LaTeX text with suitable macro definition
  there; e.g., adding something that only the proofreader should see:
  \newcommand{\\LTadd}\[1\]{}

[Back to top](#tex2txt-a-flexible-latex-filter-with-tracking-of-line-numbers-or-character-positions)

## Command line
The script expects the following parameters.
```
python3 tex2txt.py [--nums file] [--char] [--repl file] [--defs file] \
                   [--extr list] [--lang xy] [--unkn] [texfile]
```
- without positional argument `texfile`: read standard input
- option `--nums file`<br>
  file for storing original position numbers;
  if option --char not given: for each line of output text, the file contains
  a line with the estimated original line number;
  can be used later to correct line numbers in messages
- option `--char`<br>
  activates character position tracking; if option --nums is given, then
  the file contains the estimated input position for each character of
  output; may be slow for very large texts
- option `--repl file`<br>
  file with phrase replacements performed at the end, for instance after
  changing inline maths to text, and German hyphen "= to - ;
  see LAB:SPELLING in script for line syntax
- option `--defs file`<br>
  file with additional declarations, example file content (defs members,
  given without lambda, are “appended” to corresponding parms members;
  compare section
  [Declaration of LaTeX macros](#declaration-of-latex-macros)):<br>
  `defs.project_macros = (Macro(name='swap', args='AA', repl=r'\2\1'),)`
- option `--extr ma[,mb,...]` (comma-separated list of macro names)<br>
  extract only first braced argument of these macros;
  useful, e.g., for check of foreign-language text and footnotes,
  or for tracking of file inclusions
- option `--lang xy`<br>
  language de or en, default: de;
  used for adaptation of equation replacements, maths operator names,
  proof titles, for handling of macros like \"\=, and for replacement
  of foreign-language text;
  see LAB:LANGUAGE in script
- option `--unkn`<br>
  print list of undeclared macros and environments outside of equations;
  declared macros do appear here, if a mandatory argument is missing
  in input text

[Back to top](#tex2txt-a-flexible-latex-filter-with-tracking-of-line-numbers-or-character-positions)

## Usage under Windows
The software has been developed under Linux and tested additionally under
Cygwin on Windows&nbsp;7.
Some encoding problems for the latter case are addressed in section
[Encoding problems](#encoding-problems).

If Python and Java are installed under Windows, then the main Python
program [tex2txt.py](tex2txt.py) may be directly used in a Windows command
console or script.
Furthermore, at least the two application scripts [shell2.py](shell2.py)
and [shell2-html.py](shell2-html.py) from section
[Application as Python module](#application-as-python-module) can be run,
if the LanguageTool software is present.
For example, this could look like
```
"c:\Program Files\Python\Python37\python.exe" shell2-html.py t.tex > t.html
```
The file tex2txt.py must reside in the current directory, and variable
'ltjar' in script shell2-html.py has to be customised.

[Back to top](#tex2txt-a-flexible-latex-filter-with-tracking-of-line-numbers-or-character-positions)

## Tool integration
The Python script is meant as small utility that performs a limited task
with good quality.
Integration with a proofreading software and features like tracking of
\\input{...} directives have to be implemented “on top”.
Apart from application in Bash scripts, extension is also possible like
in section [Application as Python module](#application-as-python-module).

### Simple scripts
A first Bash script that checks a single LaTeX file is given in
file [shell.sh](shell.sh).
The command
```
bash shell.sh file_name
```
will read the specified LaTeX file and create plain text and line number
files with additional extensions .txt and .lin, respectively.
Then it will call [LanguageTool](https://www.languagetool.org)
and filter line numbers in output messages.
File [Example.md](Example.md) demonstrates the script.

A variant correcting both line and column numbers is given in
file [shell2.sh](shell2.sh) with application example in file
[Example2.md](Example2.md).

We assume that [Java](https://java.com) is installed, and that the directory
with relative path ../LT/ contains an unzipped archive of the LanguageTool
software.
This archive, for example LanguageTool-4.4.zip, can be obtained
from [here](https://www.languagetool.org/download).

### More complete integration
A Bash script for language checking of a whole document tree is proposed
in file [checks.sh](checks.sh).
For instance, the command
```
bash checks.sh Banach/*.tex > errs
```
will check the main text and extracted foreign-language parts in all these
files.
The result file 'errs' will contain names of files with problems together
with filtered messages from the proofreader.

With option --recurse, file inclusions as \\input{...} will be tracked
recursively.
Exceptions are listed at LAB:RECURSE in the Bash script.
Note, however, the limitation sketched in [issue #12](../../issues/12).

It is assumed that the Bash script is invoked at the “root directory”
of the LaTeX project, and that all LaTeX documents are placed directly there
or in subdirectories.
For safety, the script will refuse to create auxiliary files outside of
the directory specified by variable $txtdir (see below).
Thus, an inclusion like \\input{../../generics.tex}
probably won't work with option --recurse.

Apart from [Python](https://www.python.org),
the [Bash](https://www.gnu.org/software/bash) script
uses [Java](https://java.com) together with
[LanguageTool's](https://www.languagetool.org)
desktop version for offline use,
[Hunspell](https://github.com/hunspell/hunspell),
and some standard [Linux](https://www.linux.org) tools.
Before application, variables in the script have to be customised.
For placement of intermediate text and line number files, the script uses an
auxiliary directory designated by variable $txtdir.
This directory and possibly necessary subdirectories will be created
without request.
They can be deleted with option --delete.

### Actions of the Bash script
- convert content of given LaTeX files to plain text, extract foreign-language
  parts
- call LanguageTool (or Hunspell on --no-lt) for native-language main text
- check foreign-language text using Hunspell
- only if variable $check\_for\_single\_letters set to 'yes':
  look for single letters, excluding abbreviations in script variable $acronyms
  (useful, for instance, in German)

### Usage of the Bash script
```
bash checks.sh [--recurse] [--adapt-lt] [--no-lt] \
               [--columns] [--delete] [files]
```
- no positional arguments `files`:
  use files from script variable $all\_tex\_files
- option `--recurse`<br>
  track file inclusions; see LAB:RECURSE in script for exceptions
- option `--adapt-lt`<br>
  prior to checks, back up LanguageTool's files spelling.txt (additional
  accepted words) and prohibit.txt (words raising an error), and append
  corresponding private files; see LAB:ADAPT-LT in script
- option `--no-lt`<br>
  do not use LanguageTool but instead Hunspell for native-language checks;
  perform replacements from script variable $repls\_hunspell beforehand
- option `--columns`<br>
  correct both line and column numbers in messages from LanguageTool;
  this may be slow for very large LaTeX files
- option `--delete`<br>
  only remove auxiliary directory in script variable $txtdir, and exit

[Back to top](#tex2txt-a-flexible-latex-filter-with-tracking-of-line-numbers-or-character-positions)

## Encoding problems
The LaTeX files have to be encoded as plain ASCII or UTF-8.

Files with Windows style line endings (CRLF) are accepted, but the text
output will be Unix style (LF only), unless a Windows Python interpreter
is used.
The output filters as in Bash script [shell2.sh](shell2.sh) will work
properly, however.

Under Cygwin with Java from the Windows installation, LanguageTool will
produce Latin-1 output, even if option '--encoding utf-8' is specified.
Therefore, a translator to UTF-8 has to be placed in front of a Python filter
for line or column numbers.
This is shown in Bash function LTfilter() in file [checks.sh](checks.sh).
A similar approach is taken in example Python script [shell2.py](shell2.py)
from section
[Application as Python module](#application-as-python-module).

With option --json, LanguageTool always delivers UTF-8 encoded text.
JSON output is used in application script [shell2-html.py](shell2-html.py).

[Back to top](#tex2txt-a-flexible-latex-filter-with-tracking-of-line-numbers-or-character-positions)

## Declaration of LaTeX macros
The first section of the Python script consists of collections for
LaTeX macros and environments.
The central “helper function” Macro() declares a LaTeX macro, see the
synopsis below, and is applied in the collections
parms.project\_macros and parms.system\_macros.
Here is a short extract from the definition of standard LaTeX macros already
included.
(The lambda construct allows us to use variables and functions introduced
only later.)
```
parms.system_macros = lambda: (
    Macro('caption', 'OA', extr=r'\2'),         # extract to end of text
    Macro('cite', 'A', '[1]'),
    Macro('cite', 'PA', r'[1, \1]'),
    Macro('color', 'A'),
    Macro('colorbox', 'AA', r'\2'),
    Macro('documentclass', 'OA'),
    ...
```
Other collections, e.g. for LaTeX environments, use functions similar
to Macro().
Project specific extension of all these collections is possible with
option --defs and an additional Python file.
The corresponding collections there, for instance defs.project\_macros,
have to be defined using simple tuples without lambda construct;
compare the example in section [Command line](#command-line).

Synopsis of `Macro(name, args, repl='', extr='')`:
- argument `name`:
    - macro name without leading backslash
    - characters with special meaning in regular expressions, e.g. '\*',
      may need to be escaped; see for example declaration of macro \\hspace
- argument `args`:
    - string that encodes argument sequence
    - A: a mandatory \{...\} argument
    - O: an optional \[...\] argument
    - P: a mandatory \[...\] argument, see for instance macro \\cite
- optional argument `repl`:
    - replacement pattern, r'...\\d...' (d: single digit) extracts text
      from position d in args (counting from 1)
    - other escape rules: see escape handling at function myexpand();
      e.g., include a single backslash: repl=r'...\\\\...'
    - inclusion of % only accepted as escaped version r'...\\\\%...',
      will be resolved to % at the end by function before\_output()
    - inclusion of double backslash \\\\ and replacement ending with \\
      will be rejected
    - reference by r'\\d' to an optional argument will be refused
- optional argument `extr`:
    - append this replacement (specified as in argument repl) to the end
      of the main text, separated by blank lines

[Back to top](#tex2txt-a-flexible-latex-filter-with-tracking-of-line-numbers-or-character-positions)

## Handling of displayed equations
Displayed equations should be part of the text flow and include the
necessary interpunction.
At least the German version of
[LanguageTool](https://www.languagetool.org) (LT)
will detect a missing dot
in the following snippet, where 'a' to 'd' stand for arbitrary mathematical
terms (meaning: “We conclude maths Therefore, ...”).
```
Wir folgern
\begin{align}
    a   &= b \\
    c   &= d
\end{align}
Daher ...
```
In fact, LT complains about the capital “Daher” that should start a
new sentence.

### Trivial version
With the entry
```
    EnvRepl('align', repl=''),
```
in parms.environments of the Python script (but no 'align' entry in
parms.equation\_environments), the equation environment is simply removed.
We get the following script output which will probably cause a problem,
even if the equation ends with a correct interpunction sign.
```
Wir folgern
Daher ...
```

### Simple version
With the entry
```
    EquEnv('align', repl='  Relation'),
```
in parms.equation\_environments of the script, one gets:
```
Wir folgern
  Relation
Daher ...
```
Adding a dot “= d.” in the equation will lead to “Relation.” in the output.
This will also hold true, if the interpunction sign is followed by maths space
or by macros as \\label and \\nonumber.

### Full version
With the entry
```
    EquEnv('align'),
```
we obtain (“gleich” means equal, and option --lang en will print “equal”):
```
Wir folgern
  D1D  gleich D2D
  D2D  gleich D3D.
Daher ...
```
The replacements 'D1D' to 'D3D' are taken from the collection in script
variable parms.display\_math that depends on option --lang, too.
Now, LT will complain about repetition of D2D.
Finally, writing “= b,” in the equation leads to the output:
```
Wir folgern
  D1D  gleich D2D,
  D3D  gleich D4D.
Daher ...
```
The rules for this equation parsing are described at LAB:EQUATIONS
in the Python script.
They ensure that variations like
```
    a   &= b \\
        &= c.
```
and
```
    a   &= b \\
        &\qquad -c.
```
also will work properly.
In contrast, the text
```
    a   &= b \\
    -c  &= d.
```
will again produce an LT warning due to the missing comma after b,
since the script replaces both b and -c by D2D without intermediate text.

In rare cases, manipulation with \\LTadd{} or \\LTskip{} may be necessary
to avoid false warnings from the proofreader.
See also file [Example.md](Example.md).

### Inclusion of “normal” text
In variant “Full version”, the argument of \\text\{...\}
(variable for macro name in script: parms.text\_macro) is directly copied.
Outside of \\text, only maths space like \\; and \\quad is considered as space.
Therefore, one will get warnings from the proofreading program, if subsequent
\\text and maths parts are not properly separated.
See file [Example.md](Example.md).

### Replacements in English documents
The replacement collection in variable parms.display\_math works
quite well, if German is the main language.
Requirements for replacements are summarised in the script in function
set\_language\_de().
Till now, we could not yet select replacements that work equally well
with the English version of LanguageTool.
For example, sensitivity is not good with the collection provided in function
set\_language\_en() in these cases:
- missing final dot in an equation, if something like 'Therefore'
  is following;
- lower-case text continuation after an equation with final dot.

Currently (LanguageTool version 4.5), only the second case is detected in
only variant “Simple version” above, e.g.:
```
EquEnv('align', repl='  relation'),
```

[Back to top](#tex2txt-a-flexible-latex-filter-with-tracking-of-line-numbers-or-character-positions)

## Application as Python module
The script can be extended with Python's module mechanism.
In order to use `import tex2txt`, this module has to reside in the same
directory as the importing script, or environment variable PYTHONPATH
has to be set accordingly.

### Module interface
The module provides the following central function.
```
(plain, nums) = tex2txt.tex2txt(tex, options)
```
Argument 'tex' is the LaTeX text as string, return element 'plain' is the
plain text as string.
Array 'nums' contains the estimated original line or character positions,
counting from one.
Negative values indicate that the actual position may be larger.
Argument 'options' can be created with class
```
tex2txt.Options(...)
```
which takes arguments similar to the command-line options of the script.
They are documented at the definition of class 'Options', see LAB:OPTIONS.
The parameters 'defs' and 'repl' for this class can be set using functions
tex2txt.read\_definitions(fn) and tex2txt.read\_replacements(fn), both
expecting 'None' or a file name as argument.

Two additional functions support translation of line and column numbers
in case of character position tracking.
Translation is performed by
```
ret = tex2txt.translate_numbers(tex, plain, nums, starts, lin, col)
```
with strings 'tex' and 'plain' containing LaTeX and derived plain texts.
Argument 'nums' is the number array returned by function tex2txt(),
'lin' and 'col' are the integers to be translated.
Argument 'starts' has to be obtained beforehand by the call
```
starts = tex2txt.get_line_starts(plain)
```
and contains positions in string 'plain' that start a new line.
The return value 'ret' above is 'None', if translation was not successful.
On success, 'ret' is a small object.
Integers 'ret.lin' and 'ret.col' indicate line and column numbers, and
boolean 'ret.flag' equals 'True', if the actual position may be larger.

Finally, function
```
tex2txt.myopen(filename, mode='r')
```
is similar to standard function open(), but it enforces UTF-8 decoding
and converts a possible exception into an error message.

### Application examples
The module interface is demonstrated in function main(), which is activated
when running the script directly.

An example application is shown in Python script [shell2.py](shell2.py)
which resembles the Bash script [shell2.sh](shell2.sh) from section
[Simple scripts](#simple-scripts).
For instance, the Bash command
```
python3 shell2.py Banach/*.tex
```
will extract plain text from all these LaTeX files and call
[LanguageTool](https://www.languagetool.org) (LT).
(The path to LT has to be customised in script variable 'ltjar', compare
section [Simple scripts](#simple-scripts).)
Line and column numbers in LT's messages will be corrected, preceding each
message by the corresponding file name.
The script does not create auxiliary files.
In order to suppress purely diagnostic messages from LT, one can say
`python3 shell2.py Banach/*.tex 2>/dev/null`.
Files for additional macro definitions and phrase replacements may be read,
if the corresponding lines at 'options = ...' are uncommented and tailored. 

With example [shell2-html.py](shell2-html.py), the command
```
python3 shell2-html.py t.tex > t.html
```
will create an HTML file 't.html' from LaTeX file 't.tex'.
Opened in a browser, it displays the original LaTeX text, highlighting the
problems indicated by LT.
The content of corresponding LT messages can be seen when hovering the mouse
over these marked places.
This nice idea is due to Sylvain Hallé, who developed
[TeXtidote](https://github.com/sylvainhalle/textidote).

[Back to top](#tex2txt-a-flexible-latex-filter-with-tracking-of-line-numbers-or-character-positions)

## Remarks on implementation
Parsing with regular expressions is fun, but it remains a rather coarse
approximation of the “real thing”.
Nevertheless, it seems to work quite well for our purposes, and it inherits
high flexibility from the Python environment.
A stricter approach could be based on software like
[plasTeX](https://github.com/tiarno/plastex).

In order to parse nested structures, some regular expressions are constructed
by iteration.
At the beginning, we hence check for instance, whether nested {} braces of
the actual input text do overrun the corresponding regular expression.
In that case, an error message is generated, and the variable
parms.max\_depth\_br for maximum brace nesting depth has to be changed.
Setting control variables for instance to 100 does work, but also increases
resource usage.

A severe general problem is order of macro expansion.
While TeX strictly evaluates from left to right, the order of treatment by
regular expressions is completely different.
Additionally, we mimic TeX's behaviour in skipping white space between
macro name and next non-space character.
This calls for hacks like the regular expression in variable skip\_space\_macro
together with the temporary placeholder in mark\_begin\_env.
It avoids that a macro without arguments consumes leading space inside of
an already resolved following environment.
Besides, that protects a line break, for instance in front of an equation
environment.
Another issue emerges with input text like '\\y{a\\z} b' which can lead
to the output 'ab', if macro \\z is expanded after macro \\y{...} taking an
argument.
The workaround inserts the temporary placeholder in variable mark\_deleted
for each closing } brace or \] bracket, when a macro argument is expanded.

Our mechanism for line number tracking relies on a partial reimplementation
of the substitution function re.sub() from the standard Python module
for regular expressions.
Here, the manipulated text string is replaced by a pair of this same string
and an array of integers.
These represent the estimated original line numbers of the lines in the
current text string part.
During substitution, the line number array is adjusted upon deletion or
inclusion of line breaks.
The tracking of character positions for option --char works similarly.

Since creation of new empty lines may break the text flow, we avoid it
with a simple scheme.
Whenever a LaTeX macro is expanded or an environment frame is deleted,
the mark from variable mark\_deleted is left in the text string.
At the very end, these marks are deleted, and lines only consisting
of space and such marks are removed completely.
This also means that initially blank lines remain in the text (except
those only containing a % comment).

Under category [Issues](../../issues), some known shortcomings are listed.
Additionally, we have marked several problems as BUG in the script.

[Back to top](#tex2txt-a-flexible-latex-filter-with-tracking-of-line-numbers-or-character-positions)
