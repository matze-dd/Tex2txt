import tex2txt

latex = r"""
Only few people\footnote{We use
\textcolor{red}{redx colour.}}
is lazy.
"""

res = r"""
Only few people
is lazy.



We use
redx colour.
"""

opts = tex2txt.Options(lang='en')
plain, nums = tex2txt.tex2txt(latex, opts)

def test_plain():
    assert plain == res

