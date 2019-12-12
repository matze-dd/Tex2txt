
## Generation of an HTML report

Similarly to the scheme used by 
[TeXtidote](https://github.com/sylvainhalle/textidote),
the command
```
python3 shell2-html.py test.tex > test.html
```
with file test.tex containing
```
This is is the main\footnote{A footnote may be set
in \textcolor{red}{redx colour.}}
text.
```
produces this output test.html:

![test.html](html-report.png)
