#
#   tex2txt.py:
#   test of introductory example from README.md
#

import tex2txt

latex = r"""
Only few people\footnote{We use
\textcolor{red}{redx colour.}}
is lazy.
"""

plain_t = r"""
Only few people
is lazy.



We use
redx colour.
"""

nums_t = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 27, 27, 27, 27, 28, 29, 30, 31, 32, 33, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 63, 74]


options = tex2txt.Options(lang='en', char=True)
plain, nums = tex2txt.tex2txt(latex, options)

def test_text():
    assert plain == plain_t

def test_nums():
    assert nums == nums_t

