#
#   tex2txt.py:
#   simple test of equation replacements, from Example.md
#

import tex2txt

latex = r"""
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
"""

plain_t = r"""
We consider
  a set C-C-C, a domain D-D-D, andx
  a function E-E-E.

With a constant F-F-F, we require
  U-U-U  equal V-V-V for all W-W-W, 
  X-X-X  equal Y-Y-Y for all Z-Z-Z 
  Z-Z-Z  equal U-U-U for allV-V-V. 



Thix is a footnote.
"""

options = tex2txt.Options(lang='en', char=True)
plain, nums = tex2txt.tex2txt(latex, options)

def test_text():
    assert plain == plain_t

