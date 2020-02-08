Assume the following input text.
```
We consider\footnote{Thix is a footnote.}
\begin{itemize}
\item a set $M$, a domain $\Omega\subset M$, andx
\item a function $f:M \to [0,1]$.
\end{itemize}

With a constant $\epsilon > 0$, we require
\begin{align}
U_\epsilon(x)
    &\subset M \quad\text{for all } x \in \Omega, \notag \\
f(x)    % LINE 11
    &> 0 \quad\text{for all}\ x \in \Omega \label{l1} \\
f(x)
    &= 0 \quad\text{for all} x \in M \setminus \Omega. \label{l2}
\end{align}
```
Using option --lang en, one gets the following output from Python script
[tex2txt.py](tex2txt.py).
```
Thix is a footnote.
We consider
  a set C-C-C, a domain D-D-D, andx
  a function E-E-E.

With a constant F-F-F, we require
  U-U-U  equal V-V-V for all W-W-W, 
  X-X-X  equal Y-Y-Y for all Z-Z-Z 
  Z-Z-Z  equal U-U-U for allV-V-V. 



Thix is a footnote.
```
With the filter from Bash script [shell.sh](shell.sh), the typo 'andx'
will be related to input line 3.
The problems in the equation (missing comma leads to word repetition,
missing space leads to spelling error) will be related to line 11+ and 13+,
respectively; line 11 is marked with a comment.
Extra text flows like footnotes are separately appended at the end,
the typo 'Thix' is related to input line 1.

Here is the output of the command `bash shell.sh z.tex`, if the above input
text is stored in file z.tex.
Line numbers in \[\] brackets have been added by the filter in variable
\$repl\_lines of the Bash script.
```
1.) Line 2 [3], Rule ID: MORFOLOGIK_RULE_EN_GB
Message: Possible spelling mistake found
Suggestion: and; Andy; and x
We consider   a set C-C-C, a domain D-D-D, andx   a function E-E-E.  With a constant F-F-F, ...
                                           ^^^^                                             

2.) Line 7 [11+], Rule ID: ENGLISH_WORD_REPEAT_RULE
Message: Possible typo: you repeated a word
Suggestion: Z-Z-Z
...for all W-W-W,    X-X-X  equal Y-Y-Y for all Z-Z-Z    Z-Z-Z  equal U-U-U for allV-V-V.     Thix is a foo...
                                                ^^^^^^^^^^^^^^                                             

3.) Line 8 [13+], Rule ID: MORFOLOGIK_RULE_EN_GB
Message: Possible spelling mistake found
...-Y-Y for all Z-Z-Z    Z-Z-Z  equal U-U-U for allV-V-V.     Thix is a footnote. 
                                                ^^^^^^^^                          

4.) Line 12 [1], Rule ID: MORFOLOGIK_RULE_EN_GB
Message: Possible spelling mistake found
Suggestion: This; Thin; Hix; Th ix
...-Z-Z    Z-Z-Z  equal U-U-U for allV-V-V.     Thix is a footnote. 
                                                ^^^^                
```
