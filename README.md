# Tex2txt
LaTex filter with Python

This is a small Python script for extracting raw text from LaTeX documents.

In some sense, it compares to tools like opendetex and textidote. As in textidote, we make an effort to track line numbers. The file shell.sh shows an example for filtering messages from a language checker.

A speciality is some parsing of LaTeX environments for displayed equations. Therefore, on can check embedded \text{...} macros (LaTeX package amsmath) and interpunction in -- not too complex -- displayed equations.

In the starting section of the script, macros and environments with tailored treatment are listed. This should ease adaptation to own needs. We assume that the LaTeX source does not contain things from the preamble but only a "real" text part.

Some shortcomings result from processing mainly via regular expressions. They are marked in the code.
