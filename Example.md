Assume the following input text.
```
We consider
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
Using option --lang en, one gets the following Python script output.
```
We consider
  a set C, a domain D, andx
  a function E.

With a constant F, we require
  U  equal V for all W, 
  X  equal Y for all Z 
  Z  equal U for allV. 
```
With the filter from Bash script [shell.sh](shell.sh), the typo 'andx'
will be related to input line 3.
The problems in the equation (missing comma leads to word repetition,
missing space leads to spelling error) will be related to line 11+ and 13+,
respectively; line 11 is marked with a comment.

Here is the output of Bash script [shell.sh](shell.sh), if the above input
text is stored in a file named z.tex.
Line numbers in \[\] brackets have been added by the filter in variable
\$repl\_lines of the Bash script.
```
Expected text language: English (GB)
Working on z.tex.txt...
1.) Line 2 [3], Rule ID: MORFOLOGIK_RULE_EN_GB
Message: Possible spelling mistake found
Suggestion: and; Andy; and x
We consider   a set C, a domain D, andx   a function E.  With a constant F, we requi...
                                   ^^^^                                             

2.) Line 7 [11+], Rule ID: ENGLISH_WORD_REPEAT_RULE
Message: Possible typo: you repeated a word
Suggestion: Z
... U  equal V for all W,    X  equal Y for all Z    Z  equal U for allV.  
                                                ^^^^^^                     

3.) Line 8 [13+], Rule ID: MORFOLOGIK_RULE_EN_GB
Message: Possible spelling mistake found
Suggestion: all; ally; alls; All; all V
...W,    X  equal Y for all Z    Z  equal U for allV.  
                                                ^^^^   
Time: 3058ms for 3 sentences (1.0 sentences/sec)
```
