# Tex2txt
This is a Python script for extracting raw text from LaTeX documents.

In some sense, it compares to tools like OpenDetex and TeXtidote. As in TeXtidote, we make an effort to track line numbers. The file shell.sh shows an example for filtering messages from a language checker.

A speciality is some parsing of LaTeX environments for displayed equations. Therefore, one can check embedded \text{...} macros (LaTeX package amsmath) and interpunction in -- not too complex -- displayed equations. An example is shown in file 'Example', operation is summarized in the script at label LAB:EQUATIONS.

In the starting section of the script, macros and environments with tailored treatment are listed. This should ease adaptation to own needs. We assume that the LaTeX source does not contain things from the preamble but only a "real" text part.

In order to parse with regular expressions, some of them are constructed by iteration. At the beginning, we check for instance, whether nested {} braces of the actual text do overrun the corresponding regular expression. In that case, an error message is generated and the controlling variable has to be changed.

A more complete shell script for checking a whole document tree is checks.sh.
