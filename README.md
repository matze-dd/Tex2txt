# Tex2txt, a filter for mathematical texts
## Table of contents
[General description](#description)<br>
[Selected actions](#actions)<br>
[Usage](#usage)<br>
[Handling of displayed equations](#equations)<br>
[Implementation issues](#implementation)

## Problem
Unfortunately, there is a naming conflict with the related Haskell package.
We ask for apology.

## General description<a name="description"></a>
This is a Python script for extracting raw text from LaTeX documents with focus on mathematics.
The aim is to produce only few "false" warnings when feeding the text into a language checker.

In some sense, the script compares to tools like OpenDetex, TeXtidote and the above-mentioned Haskell software.
As in TeXtidote, we make an effort to track line numbers.
Unnecessary creation of empty lines is avoided, paragraphs and sentences remain intact.
The Bash script shell.sh shows an example for filtering messages from a language checker.

An optional speciality is some parsing of LaTeX environments for displayed
equations.
Therefore, one can check embedded \text{...} parts (LaTeX package amsmath)
and interpunction in the text flow including—not too complex—displayed
equations.
Comments on that can be found [below](#equations).
An example is shown in file Example.md, operation is summarized in the script
at label LAB:EQUATIONS.

The starting section of the Python script lists macros and environments
with tailored treatment.
This should ease adaptation to own needs.

A more complete Bash script for language checking of a whole document tree
is checks.sh.
For instance, the command<br>
`bash checks.sh Banach/*.tex > errs`<br>
will check the main text, extracted footnotes and foreign-language text
in all these files.
The result file errs will contain names of files with problems together
with filtered messages from the language checker.<br>
Remark: Before application, variables in this script have to be customized.

## Selected actions<a name=actions></a>
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
  \\\[...\\\] and $$...$$ are same as environment equation\*;<br>
  see [below](#equations), file Example.md, and LAB:EQUATIONS in the script
- some treatment for \item\[...\] labels, see LAB:ITEMS in script
- letters with text-mode accents as \\' or \v are translated to 
  corresponding UTF8 characters, see LAB:ACCENTS in script
- rare warnings can be suppressed using \LTadd{}, \LTskip{},
  \LTalter{}{} in the LaTeX text with suitable macro definition there;
  e.g., adding something that only the language checker should see:<br>
  \newcommand{\LTadd}\[1\]{}

## Usage<a name="usage"></a>
`python3 tex2txt.py [--nums file] [--repl file] [--defs file] [--extr list] [--lang xy] [--unkn] [file]`

- without argument file: read standard input
- option `--nums file`<br>
  file for storing original line numbers;
  can be used later to correct line numbers in messages
- option `--repl file`<br>
  file with phrase replacements performed at the end, namely after
  changing inline maths to text, and German hyphen "= to - ;
  see LAB:SPELLING in script for line syntax
- option `--defs file`<br>
  file with additional declarations, example file content (defs members
  are appended to parms members):<br>
  `defs.project_macros = lambda: (Macro('xyz', 'AA', r'\2'),)`
- option `--extr ma[,mb,...]` (list of macro names)<br>
  extract only first braced argument of these macros;
  useful, e.g., for check of foreign-language text and footnotes
- option `--lang xy`<br>
  language de or en, default: de;
  used for adaptation of equation replacements, math operator names,
  proof titles, and replacement of foreign-language text;
  see LAB:LANGUAGE in script
- option `--unkn`<br>
  print list of undeclared macros and environments outside of equations;<br>
  declared macros do appear here, if a mandatory argument is missing in text

## Handling of displayed equations<a name="equations"></a>
### Rationale
Displayed equations should be part of the text flow and include the
necessary interpunction. At least the German version of LanguageTool (LT)
will detect a missing dot in the following snippet
(We conclude math Therefore,...).
```
Wir folgern
\begin{align}
    a   &= b \\
    c   &= d
\end{align}
Daher ...
```
In fact, LT complains about the capital 'Daher' that should start a
new sentence.

### Simple version
With the entry
```
    EquEnv('align', repl='  Relation')
```
in parms.equation_environments of the Python script, one gets the
following script ouptut.
```
Wir folgern
  Relation
Daher ...
```
Adding a dot '= d.' in the equation will lead to 'Relation.' in the output.

### Full version
With the entry
```
    EquEnv('align')
```
we obtain (gleich means equal):
```
Wir folgern
  D1D  gleich D2D
  D2D  gleich D3D.
Daher ...
```
Now, LT will complain about repetition of D2D. Writing '= b,' in the equation
leads to:
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
In rare cases, manipulation with \LTadd{} or \LTskip{} may be necessary
to avoid false warnings.

See also file Example.md.

## Implementation issues<a name="implementation"></a>
In order to parse with regular expressions, some of them are constructed by
iteration.
At the beginning, we hence check for instance, whether nested {} braces of
the actual input text do overrun the corresponding regular expression.
In that case, an error message is generated, and the variable
parms.max\_depth\_br for maximum brace nesting depth has to be changed.
Setting control variables for instance to 100 does work, but also increases
resource usage.

A severe general problem is order of macro resolution.
While TeX strictly evaluates from left to right, the order of treatment by
regular expressions is completely different.
This calls for hacks like the regular expression in skip_space_macro together
with the placeholder \begin{%};
it aims to avoid that a macro without arguments consumes leading space
inside of an already resolved following environment.

Overall, parsing with regular expressions is fun, but remains a rather coarse
approximation of the "real thing".
Nevertheless, it seems to work quite well in practice, and it inherits high
flexibility from Python.
