
#
#   tex2txt.py:
#   - test of \verb and \begin{verbatim}
#

import tex2txt

options = tex2txt.Options(lang='en', char=True)

def test_verb():

    latex = '\\verb?x\\y?\\label{z}?'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == 'x\\y?'

    # extra blank lines: see LAB:VERBATIM in tex2txt.py
    latex = '\\begin{verbatim}\\verb?\\?\n\\end{verbatim}'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == '\n\n\\verb?\\?\n\n'
