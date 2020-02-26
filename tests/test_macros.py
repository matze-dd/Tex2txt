
#
#   tex2txt.py:
#   - test of detection of macro arguments
#   - test of optional parameters for \cite, \begin{proof}
#

import tex2txt

options = tex2txt.Options(lang='en', char=True)

def test_macro_arguments():

    # normal expansion
    latex = '\\textcolor\n{red}\n{blue}'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == 'blue'
    assert nums == [19, 20, 21, 22, 24]

    # no expansion: argument in next paragraph
    latex = '\\textcolor\n{red}\n \n{blue}'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == 'red\n \nblue'

    # no expansion: argument in next paragraph
    latex = '\\textcolor\n\n{red}\n{blue}'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == '\nred\nblue'

    # expansion: comment line
    latex = '\\textcolor\n %x\n{red}\n{blue}'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == 'blue'


def test_cite_proof():

    latex = '\\cite{x}'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == '[1]'

    latex = '\\cite[y]{x}'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == '[1, y]'

    latex = '\\begin{proof}'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == 'Proof.'

    latex = 'A \\begin{proof}[Test] B'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == 'A Test. B'
    assert nums == [1, 2, 17, 18, 19, 20, 21, 22, 23, 24]

