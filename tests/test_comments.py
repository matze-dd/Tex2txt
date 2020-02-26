
#
#   tex2txt.py:
#   test of latex comments and removal of blank lines left by macros
#

import tex2txt

options = tex2txt.Options(lang='en', char=True)

#   compare LAB:COMMENTS in tex2txt.py
#
def test_latex_comments():

    # "normal" comment
    latex = 'a %x\nb\n'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == 'a \nb\n'
    assert nums == [1, 2, 5, 6, 7, 8]

    # join lines
    latex = 'a%x\n  b\n'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == 'ab\n'
    assert nums == [1, 7, 8, 9]

    # join lines: protect macro name
    latex = 'a\\aa%x\nb\n'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == 'aåb\n'
    assert nums == [1, -2, 8, 9, 10]

    # do not join lines, if next line empty
    latex = 'a%x\n\nb\n'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == 'a\n\nb\n'
    assert nums == [1, 4, 5, 6, 7, 8]

    # remove pure comment lines
    latex = 'a %x\n %x\nb\n'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == 'a \nb\n'
    assert nums == [1, 2, 5, 10, 11, 12]


def test_remove_blank_lines_left_by_macros():

    # a normal macro: \label
    latex = 'a\n\\label{x}\nb\n'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == 'a\nb\n'
    assert nums == [1, 2, 13, 14, 15]

    # macro plus comment
    latex = 'a\n\\label{x} %x\nb\n'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == 'a\nb\n'
    assert nums == [1, 2, 16, 17, 18]

    # \begin and \end
    latex = 'a\n\\begin{x}\nb\n\\end{x}\nc\n'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == 'a\nb\nc\n'
    assert nums == [1, 2, 13, 14, 23, 24, 25]

    # (actually no blank lines)
    latex = 'a\n\\begin{x}b\n\\end{x}c\n'
    plain, nums = tex2txt.tex2txt(latex, options)
    assert plain == 'a\nb\nc\n'
    assert nums == [1, 2, 12, 13, 21, 22, 23]

