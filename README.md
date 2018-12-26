# Tex2txt
## Problem
Unfortunately, there is a naming conflict with the related Haskell package.
We ask for apology.

## Description
This is a Python script for extracting raw text from LaTeX documents.

In some sense, it compares to tools like OpenDetex, TeXtidote and the above-mentioned Haskell program.
As in TeXtidote, we make an effort to track line numbers.
Therefore, unnecessary creation of empty new lines can be avoided,
paragraphs and sentences remain intact.
The file shell.sh shows an example for filtering messages from a language checker.

An optional speciality is some parsing of LaTeX environments for displayed equations.
Therefore, one can check embedded \text{...} parts (LaTeX package amsmath) and interpunction in—not too complex—displayed equations.
An example is shown in file Example, operation is summarized in the script at label LAB:EQUATIONS.

The starting section of the script lists macros and environments with tailored treatment.
This should ease adaptation to own needs.

A more complete shell script for language checking of a whole document tree is checks.sh.

## Usage
python3 tex2txt.py [--nums file] [--repl file] [--extr list] [--lang xy] [file]

<ul>
    <li> without argument file: read standard input
    </li>
    <li> option --nums file<br>
        file for storing original line numbers;
        can be used later to correct line numbers in messages
    </li>
    <li> option --repl file<br>
        file with phrase replacements performed at the end, namely after
        changing inline maths to text, and German hyphen "= to - ;
        see LAB:SPELLING in script for line syntax
    </li>
    <li> option --extr ma[,mb,...] (list of macro names)<br>
        extract only arguments of these macros;
        useful, e.g., for check of foreign-language text and footnotes
    </li>
    <li> option --lang xy<br>
        language de or en, default: de;
        used for adaptation of equation replacements, math operator names,
        proof titles, and replacement of foreign-language text;
        see LAB:LANGUAGE in script
    </li>
</ul>

## Selected actions
<ul>
    <li> frames \begin{...} and \end{...} of environments are deleted;
       tailored behaviour for environment types listed in script
    </li>
    <li> flexible treatment of own macros with arbitrary arguments
    </li>
    <li> text in heading macros as \section{...} is extracted with
        added interpunction
    </li>
    <li> suitable placeholders for \ref, \eqref, \pageref, and \cite
    </li>
    <li> "undeclared" macros are silently ignored (keeping arguments)
    </li>
    <li> inline math $...$ is replaced with text from rotating collection
        in variable parms.inline_math
    </li>
    <li> equation environments are resolved in a way suitable for check of
        interpunction, argument of \text{...} is included into output text;
        \[ ... \] is same as environment equation*; <br>
        see file Example and LAB:EQUATIONS in the script for example and
        detailed description
    </li>
    <li> some treatment for \item[...] labels, see LAB:ITEMS in script
    </li>
    <li> rare warnings can be suppressed using \LTadd{}, \LTskip{},
        \LTalter{}{} in the LaTeX text with suitable macro definition
        there;
        e.g., adding something that only the language checker should see:<br>
        \newcommand{\LTadd}[1]{}
    </li>
</ul>

## Implementation
With around 580 lines of "real code" for version 1.1.0, including 130 lines in the "declaration section", the script is not very large.

In order to parse with regular expressions, some of them are constructed by iteration.
At the beginning, we hence check for instance, whether nested {} braces of the actual input text do overrun the corresponding regular expression.
In that case, an error message is generated and the variable for maximum nesting depth has to be changed.

