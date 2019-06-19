# Tex2txt: a flexible LaTeX filter with conservation of text flow and tracking of line numbers
[General description](#general-description)<br>
[Selected actions](#selected-actions)<br>
[Command line](#command-line)<br>
[Tool integration](#tool-integration)<br>
[Declaration of LaTeX macros](#declaration-of-latex-macros)<br>
[Handling of displayed equations](#handling-of-displayed-equations)<br>
[Remarks on implementation](#remarks-on-implementation)

<a name="general-description"></a>
This is a Python script for the extraction of plain text from LaTeX documents.
In some sense, it compares to tools like OpenDetex, TeXtidote, and
the Haskell software Tex2txt.
For the naming conflict with the latter project, we want to apologize.

While virtually no text should be dropped by the filter,
the aim is to provoke only few “false” warnings when feeding the result into
a language checker.
The goal especially applies to documents containing displayed equations.
Problems with interpunction and case sensitivity would arise, if
equation environments were simply removed or replaced by fixed text.
Altogether, the script can help to create a single compact report
from language examination of a complete document tree.

For ease of problem localisation, we make an effort to track line numbers.
Unnecessary creation of empty lines therefore can be avoided, sentences
and paragraphs remain intact.
This is demonstrated in file [Example.md](Example.md),
and a more complete application of the script is addressed
in section [Tool integration](#tool-integration) below.

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

An optional speciality is some parsing of LaTeX environments for displayed
equations.
Therefore, one may check embedded \\text{...} parts (macro from LaTeX package
amsmath), and trailing interpunction of these equations
can be taken into account during language check of the main text flow.
Further details are given in section
[Handling of displayed equations](#handling-of-displayed-equations).
An example is shown in file [Example.md](Example.md), operation is summarized
in the script at label LAB:EQUATIONS.

The Python script may be seen as an exercise in usage of regular expressions.
Its internal design could be more orderly, but formal structuring with usage,
e.g., of classes would probably increase the program size
(currently, less than 900 effective lines of code).
In section [Remarks on implementation](#remarks-on-implementation),
some general issues are mentioned.

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
  added interpunction
- suitable placeholders for \\ref, \\eqref, \\pageref, and \\cite
- inline math $...$ and \\(...\\) is replaced with text from rotating
  collection in variable parms.inline\_math in script
- equation environments are resolved in a way suitable for check of
  interpunction and spacing, argument of \\text\{...\} is included into output
  text; \\\[...\\\] and $$...$$ are same as environment equation\*;
  see the section
  [Handling of displayed equations](#handling-of-displayed-equations),
  file [Example.md](Example.md), and LAB:EQUATIONS in script
- some treatment for \item\[...\] labels, see LAB:ITEMS in script
- letters with text-mode accents as '\\`' or '\\v' are translated to 
  corresponding UTF8 characters, see LAB:ACCENTS in script
- replacement of things like double quotes '\`\`' and dashes '\-\-' with
  corresponding UTF8 characters;
  replacement of '\~' and '\\,' by UTF8 non-breaking space and
  narrow non-breaking space
- treatment of \\verb(\*) macros and verbatim(\*) environments,
  see LAB:VERBATIM in script; note, however, [issue #6](../../issues/6)
- handling of % comments near to TeX: skipping of line break under certain
  circumstances
- rare warnings from language checker can be suppressed using \\LTadd{},
  \\LTskip{}, \\LTalter{}{} in the LaTeX text with suitable macro definition
  there; e.g., adding something that only the language checker should see:
  \newcommand{\\LTadd}\[1\]{}

## Command line
`python3 tex2txt.py [--nums file] [--repl file] [--defs file] [--extr list] [--lang xy] [--unkn] [file]`

- without argument file: read standard input
- option `--nums file`<br>
  file for storing original line numbers:
  for each line of output text, the file contains a line with the estimated
  original line number;
  can be used later to correct line numbers in messages
- option `--repl file`<br>
  file with phrase replacements performed at the end, for instance after
  changing inline math to text, and German hyphen "= to - ;
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
  used for adaptation of equation replacements, math operator names,
  proof titles, for handling of macros like \"\=, and for replacement
  of foreign-language text;
  see LAB:LANGUAGE in script
- option `--unkn`<br>
  print list of undeclared macros and environments outside of equations;
  declared macros do appear here, if a mandatory argument is missing
  in input text

## Tool integration
The Python script is meant as small utility that performs a limited task
with good quality.
Integration with a language checker and features like tracking of
\\input{...} directives have to be implemented “on top”.

A Bash script for language checking of a whole document tree is proposed
in file [checks.sh](checks.sh).
For instance, the command<br>
`bash checks.sh Banach/*.tex > errs`<br>
will check the main text, extracted footnotes and captions (with their own
text flows), as well as foreign-language text in all these files.
The result file 'errs' will contain names of files with problems together
with filtered messages from the language checker.

With option --recurse, file inclusions as \\input{...} will be tracked
recursively.
Exceptions are listed at LAB:RECURSE in the Bash script.
Note, however, the limitation sketched in [issue #12](../../issues/12).

It is assumed that the Bash script is invoked at the “root directory”
of the LaTeX project, and that all LaTeX documents are placed directly there
or in subdirectories.
For safety, the script will refuse to create auxiliary files outside of
the directory specified by $txtdir (see below).
Thus, an inclusion like \\input{../../generics.tex}
probably won't work with option --recurse.

Apart from [Python](https://www.python.org),
the [Bash](https://www.gnu.org/software/bash) script
uses [Java](https://java.com) together with
[LanguageTool's](https://www.languagetool.org)
desktop version for offline use,
[Hunspell](https://github.com/hunspell/hunspell),
and some standard [Linux](https://www.linux.org) tools.
Before application, variables in the script have to be customized.
For placement of intermediate text and line number files, the script uses an
auxiliary directory designated by variable $txtdir.
This directory and possibly necessary subdirectories will be created
without request.
They can be deleted with option --delete.

### Actions of the Bash script
- convert content of given LaTeX files to plain text
- call LanguageTool for native-language main text and separately for footnotes
  and captions
- check foreign-language text using Hunspell
- only if variable $check\_for\_single\_letters set to 'yes':
  look for single letters, excluding abbreviations in script variable $acronyms

### Usage of the Bash script
`bash checks.sh [--recurse] [--adapt-lt] [--no-lt] [--delete] [files]`

- no argument files: use files from script variable $all\_tex\_files
- option `--recurse`<br>
  track file inclusions; see LAB:RECURSE in script for exceptions
- option `--adapt-lt`<br>
  prior to checks, back up LanguageTool's files spelling.txt (additional
  accepted words) and prohibit.txt (words raising an error), and append
  corresponding private files; see LAB:ADAPT-LT in script
- option `--no-lt`<br>
  do not use LanguageTool but instead Hunspell for native-language checks;
  perform replacements from script variable $repls\_hunspell beforehand
- option `--delete`<br>
  only remove auxiliary directory in script variable $txtdir, and exit

## Declaration of LaTeX macros
The first section of the Python script consists of collections for
LaTeX macros and environments.
The central “helper function” Macro(...) declares a LaTeX macro, see the
synopsis below, and is applied in the collections
parms.project\_macros and parms.system\_macros.
Here is a short extract from the definition of standard LaTeX macros already
included.
(The lambda construct allows us to use variables and functions introduced
only later.)

```
parms.system_macros = lambda: (
    Macro('caption', 'OA'),         # own text flow, use option --extr
    Macro('cite', 'A', '[1]'),
    Macro('cite', 'PA', r'[1, \1]'),
    Macro('color', 'A'),
    Macro('colorbox', 'AA', r'\2'),
    Macro('documentclass', 'OA'),
    ...
```

Other collections, e.g. for LaTeX environments, use similar
“helper functions”.
Project specific extension of all these collections is possible with
option --defs and an additional Python file.
The corresponding collections there, for instance defs.project\_macros,
have to be defined using simple tuples (x,y,z,) without lambda construct.

Synopsis of `Macro(name, args, repl='')`:
- argument `name`:
    - macro name without leading backslash
    - characters with special meaning in regular expressions, e.g. '\*',
      may need to be escaped; see for example declaration of macro \\hspace
- argument `args`:
    - string that codes argument sequence
    - A: a mandatory \{...\} argument
    - O: an optional \[...\] argument
    - P: a mandatory \[...\] argument, see for instance macro \\cite
- optional argument `repl`:
    - replacement pattern, r'...\\d...' (d: single digit) extracts text
      from position d in args (counting from 1)
    - other escape rules: see escape handling at myexpand();
      e.g., include a single backslash: repl=r'...\\\\...'
    - inclusion of % only accepted as escaped version r'...\\\\%...',
      will be resolved to % at the end by resolve_escapes()
    - inclusion of double backslash \\\\ and replacement ending with \\
      will be rejected

## Handling of displayed equations
Displayed equations should be part of the text flow and include the
necessary interpunction.
At least the German version of LanguageTool (LT) will detect a missing dot
in the following snippet, where 'a' to 'd' stand for arbitrary mathematical
terms (meaning: “We conclude math Therefore, ...”).
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
This will also hold true, if the interpunction sign is followed by math space
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
again will produce an LT warning due to the missing comma after b,
since the script replaces both b and -c by D2D without intermediate text.

In rare cases, manipulation with \\LTadd{} or \\LTskip{} may be necessary
to avoid false warnings from the language checker.
See also file [Example.md](Example.md).

### Inclusion of “normal” text
The argument of \\text\{...\} (variable for macro name in script:
parms.text\_macro) is directly copied.
Outside of \\text, only math space like \\; and \\quad is considered as space.
Therefore, one will get warnings from the language checker, if subsequent
\\text and math parts are not properly separated.
See file [Example.md](Example.md).

## Remarks on implementation
Parsing with regular expressions is fun, but it remains a rather coarse
approximation of the “real thing”.
Nevertheless, it seems to work quite well in practice, and it inherits high
flexibility from Python.

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
This calls for hacks like the regular expression in skip\_space\_macro
together with the placeholder mark\_begin\_env.
It aims to avoid that a macro without arguments consumes leading space
inside of an already resolved following environment.

Under [category Issues](../../issues), some known shortcomings are listed.
