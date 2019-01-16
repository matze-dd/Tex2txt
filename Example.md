Assume the following input text.
```
%
We see
%
\begin{itemize}
\item
    that all is acceptable andx
\item
    that it can be improved.
\end{itemize}
%
Thus, with a constant $C$ and a domain $\Omega$,
%
\begin{align}
\mu &= f(x) \quad\text{for all } \mu\in\Omega, \notag \\
x   &= \begin{cases}
        0 & \text{ for} \ y>0 \\
        1 & \text{ in case} y\le 0.
            \end{cases}     \label{lab}
\end{align}

OK.
```
Using option --lang en, one gets the following Python script output.
```
We see
  that all is acceptable andx
  that it can be improved.
Thus, with a constant B and a domain C,
  U  equal V for all W, 
  X  equal Y  for Z 
  Z  in caseU. 

OK.
```
With the filter from the Bash script shell.sh, the typo 'andx' will be
related to line 6. The problems in the equation (missing comma leads to
word repetition, missing space to spelling error) will be related
to line 13+, which is \begin{align}.

