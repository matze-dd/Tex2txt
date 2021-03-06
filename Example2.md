This is the version of [Example.md](Example.md) with tracking
of character offsets.
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
Here is the output of the command `bash shell2.sh z.tex`, if the above input
text is stored in file z.tex.
In order to indicate action of the output filter in [shell2.sh](shell2.sh),
line and column numbers are placed in \[\] brackets.
```
1.) Line [3], column [46], Rule ID: MORFOLOGIK_RULE_EN_GB
Message: Possible spelling mistake found
Suggestion: and; Andy; and x
We consider   a set C-C-C, a domain D-D-D, andx   a function E-E-E.  With a constant F-F-F, ...
                                           ^^^^                                             

2.) Line [12+], column [6+], Rule ID: ENGLISH_WORD_REPEAT_RULE
Message: Possible typo: you repeated a word
Suggestion: Z-Z-Z
...for all W-W-W,    X-X-X  equal Y-Y-Y for all Z-Z-Z    Z-Z-Z  equal U-U-U for allV-V-V.     Thix is a foo...
                                                ^^^^^^^^^^^^^^                                             

3.) Line [14+], column [6+], Rule ID: MORFOLOGIK_RULE_EN_GB
Message: Possible spelling mistake found
...-Y-Y for all Z-Z-Z    Z-Z-Z  equal U-U-U for allV-V-V.     Thix is a footnote. 
                                                ^^^^^^^^                          

4.) Line [1], column [22], Rule ID: MORFOLOGIK_RULE_EN_GB
Message: Possible spelling mistake found
Suggestion: This; Thin; Hix; Th ix
...-Z-Z    Z-Z-Z  equal U-U-U for allV-V-V.     Thix is a footnote. 
                                                ^^^^                
```
