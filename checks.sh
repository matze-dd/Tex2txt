#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

#######################################################################
#
#   Bash:
#   perform language checks for LaTeX files
#
#   Actions and usage:
#   - see README.md
#
#
#                                   Matthias Baumann, 2018-2019
#

#   check these, if no argument files given
#
all_tex_files="vorwort.tex */*.tex"

#   LanguageTool for check of native-language text
#
LTprefix=../LT/LanguageTool-4.6
LTcommand="$LTprefix/languagetool-commandline.jar \
    --language de-DE --encoding utf-8 \
    --disable \
WHITESPACE_RULE,\
KOMMA_VOR_UND_ODER"

#   regular expression for filtering of LT's output
#   LT produces: '1.) Line 25, column 13, Rule ID: ...'
#
LT_info_line='^\d+\.\) Line (\d+), column (\d+), Rule ID: '

tooldir=Tools/LT            # Python scripts and private dictionaries
txtdir=$tooldir/Tex2txt     # directory for extraction of raw text 
                            # (subdirectories will be created if necessary)
ext=txt                     # file name extension for raw text
num=lin                     # ... for line number information
chr=chr                     # ... for character position information
foreign=en                  # ... for foreign-language text
ori=ori                     # ... for original dictionary files in LT tree

#   Tex2txt script
#
tex2txt_py=$tooldir/tex2txt.py
tex2txt_repl="--repl $tooldir/repls.txt"
tex2txt_defs="--defs $tooldir/defs.py"

#   sed filter for hunspell (on option --no-lt):
#   '0' --> 'Null'
#
repls_hunspell=' -e s/\<0\>/Null/g'
# repls_hunspell+=' -e s/\$\$/GCHQ/g'

#   list of accepted acronyms during search for single letters;
#   use normal space here (is replaced by nbsp)
#
check_for_single_letters=yes
acronyms='d\. h\.|f\. ü\.|i\. A\.|u\. a\.|v\. g\. V\.|z\. B\.'

utf8_nbsp=$(python3 -c 'print("\N{NO-BREAK SPACE}", end="")')
acronyms=$(echo -n $acronyms | sed -E "s/ /$utf8_nbsp/g")

#   LAB:ADAPT-LT
#   append private hunspell dictionary to LT's spelling.txt
#   ATTENTION: LT does not like empty lines
#
lt_dic_native=$LTprefix/org/languagetool/resource/de/hunspell/spelling.txt
priv_dic_native=$tooldir/hunspell.de

#   prohibit certain words
#   ATTENTION: LT does not like empty lines
#
lt_prohib_native=$LTprefix/org/languagetool/resource/de/hunspell/prohibit.txt
priv_prohib_native=$tooldir/prohibit.de

#   check of foreign-language text
#
foreign_macro=engl          # name of macro for foreign-language text
hunsp_foreign_lang=en_GB    # foreign-language code for hunspell -d ...
priv_dic_foreign=$tooldir/hunspell.en
                            # private hunspell dictionary

#   LAB:RECURSE scan file inclusions
#
#   recognized file inclusion macros
input_macros=input,include

#   do not read these files at all (regular expression)
#   - our files from fig2dev, placed in different sub-directories
input_do_not_read='(.*/)?figure\.tex'

#   scan these files for inclusions, but don't perform language checks on them
#   - our root files containing mainly fancy things, but no "real text"
input_do_not_check='(defs|main)\.tex'


##########################################################
##########################################################

trap exit SIGINT

#   parse command-line
#
declare -A options
while [ "${1:0:1}" == "-" ]
do
    case $1 in
    --recurse|--adapt-lt|--no-lt|--delete|--columns)
        options[$1]=1
        ;;
    --)
        shift
        break
        ;;
    *)
        echo unknown option "'$1'" >&2
        echo usage: bash $0 '[--recurse] [--adapt-lt] [--no-lt] [--delete] [--columns] [files]' >&2
        exit 1
    esac
    shift
done
if (( $# == 0 ))
then
    args=$all_tex_files
else
    args=$*
fi

#   only delete auxiliary directory $txtdir?
#
if [ -n "${options[--delete]}" ]
then
    read -p "enter YES to remove directory '$txtdir': " repl
    if [ "$repl" == YES ]
    then
        rm -fr $txtdir
    fi
    exit
fi

#   adjust LT's spelling files?
#
if [ -n "${options[--adapt-lt]}" ]
then
    echo Updating $lt_dic_native ... >&2
    if [ -f $lt_dic_native.$ori ]
    then
        cp $lt_dic_native.$ori $lt_dic_native
    else
        # create backup copy, if not yet present
        cp $lt_dic_native $lt_dic_native.$ori
    fi
    cat $priv_dic_native >> $lt_dic_native

    echo Updating $lt_prohib_native ... >&2
    if [ -f $lt_prohib_native.$ori ]
    then
        cp $lt_prohib_native.$ori $lt_prohib_native
    else
        # create backup copy, if not yet present
        cp $lt_prohib_native $lt_prohib_native.$ori
    fi
    cat $priv_prohib_native >> $lt_prohib_native
fi

#   Python3:
#   add original line numbers to messages
#   - argv[1]:  RE search pattern;
#               first () group must contain the number;
#               text till second () group is removed
#   - argv[2]: file with original line numbers
#
repl_lines='
import re, sys
expr = sys.argv[1]
numbers = open(sys.argv[2]).readlines()
def repl(m):
    lin = int(m.group(1)) - 1
    if lin >= 0 and lin < len(numbers):
        n = numbers[lin].strip()
        return (m.string[m.start(0):m.end(1)] + " [" + n + "]"
                    + m.string[m.end(2):m.end(0)])
    return m.group(0)
for lin in sys.stdin:
    sys.stdout.write(re.sub(expr, repl, lin))
'

#
#   Python3:
#   replace line and column numbers
#   - argv[1]: regular expression:
#              matching group 1 is line number, group 2 is column number
#   - argv[2]: original LaTeX file
#   - argv[3]: derived file with plain text
#   - argv[4]: file with character offset mapping
#
repl_lines_columns='

import re, sys

expr = sys.argv[1]
tex = open(sys.argv[2]).read()
plain = open(sys.argv[3]).read()
def f(s):
    s = s.strip()
    if s[-1] == "+":
        return -int(s[:-1])
    return int(s)
map = tuple(f(s) for s in open(sys.argv[4]))
starts = list(m.start(0) for m in re.finditer(r"\n", "\n" + plain))

def f(m):
    def ret(s1, s2):
        s = m.group(0)
        return (s[:m.start(1)] + "[" + s1 + "]" + s[m.end(1):m.start(2)]
                    + "[" + s2 + "]" + s[m.end(2):])
    def unkn():
        return ret("?", "?")

    lin = int(m.group(1))
    col = int(m.group(2))
    if lin < 1 or col < 1:
        return unkn()

    # find start of line number lin in plain file
    if lin > len(starts):
        return unkn()
    n = starts[lin - 1]

    # add column number col
    s = plain[n:]
    i = s.find("\n")
    if i >= 0 and col > i or i < 0 and col > len(s):
        return unkn()
    n += col - 1

    # map to character position in tex file
    if n >= len(map):
        return unkn()
    n = map[n]
    mark = ""
    if n < 0:
        mark = "+"
        n = -n

    # get line and column in tex file
    if n > len(tex):
        return unkn()
    s = tex[:n]
    lin = s.count("\n") + 1
    col = len(s) - (s.rfind("\n") + 1)
    return ret(str(lin) + mark, str(col) + mark)

for s in sys.stdin:
    sys.stdout.write(re.sub(expr, f, s))
'

#   Python3:
#   - scan given files for inclusion macros
#   - search recursively
#   - print list of files
#
track_input_macro='
import re, os, sys
todo = sys.argv[1:]
done = []
while todo:
    f = todo.pop(0)
    if re.fullmatch(r"'$input_do_not_read'", f):
        continue
    if f not in done:
        done.append(f)
    p = os.popen(
        "python3 '$tex2txt_py' '"$tex2txt_defs"' --extr '$input_macros' " + f)
    fs = p.read()
    if p.close():
        sys.stderr.write("\n'$0': error while checking file \"" + f + "\"\n")
        exit(1)
    for f in fs.split():
        if not f.endswith(".tex"):
            f += ".tex"
        if f not in done + todo:
            todo.append(f)
iter = (f for f in done if not re.fullmatch(r"'$input_do_not_check'", f))
print(" ".join(iter))
'

#   track file inclusions?
#
if [ -n "${options[--recurse]}" ]
then
    echo Scanning file inclusions starting with $args ... >&2
    args=$(python3 -c "$track_input_macro" $args)
fi


##########################################################
##########################################################

txtdir_path=$(readlink -m $txtdir)/

for i in $args
do
    #   avoid creation of aux files outside of txtdir
    #
    i_path=$(readlink -m $txtdir/$i.$ext)
    if [ "${i_path:0:${#txtdir_path}}" != "$txtdir_path" ]
    then
        echo "$0: ERROR:" >&2
        echo "for input file '$i'," >&2
        echo "auxiliary text file '$txtdir/$i.$ext'" >&2
        echo "would be created outside of directory '$txtdir'" >&2
        echo "--> exit" >&2
        exit 1
    fi   

    if [ ! -r $i ]
    then
        echo "$0: cannot read file '$i'" >&2
        exit 1
    fi
    dir=$(dirname $txtdir/$i)
    if [ ! -d $dir ]
    then
        if ! mkdir -p $dir
        then
            echo "$0: cannot create directory '$dir'" >&2
            exit 1
        fi
    fi

    #####################################################
    # extract raw text, save line numbers / character positions
    #####################################################

    python3 $tex2txt_py \
        $tex2txt_repl $tex2txt_defs --nums $txtdir/$i.$num $i \
        > $txtdir/$i.$ext
    if [ -n "${options[--columns]}" ]
    then
        python3 $tex2txt_py \
            $tex2txt_repl $tex2txt_defs --char --nums $txtdir/$i.$chr $i \
            > /dev/null
    fi

    #####################################################
    # call LT or hunspell
    #####################################################

    if [ -z "${options[--no-lt]}" ]
    then
        if [[ "$OS" =~ Windows ]]
        then
            # under Cygwin: LT with Windows Java produces Latin-1
            LTfilter() { iconv -f latin1 -t utf8; }
        else
            LTfilter() { cat; }
        fi
        LT_output=$(java -jar $LTcommand $txtdir/$i.$ext \
            | LTfilter)
        LT_output_lines=$(echo "$LT_output" | wc -l)
        if (( $LT_output_lines == 1 ))
        then
            echo $LT_output >&2
        fi
    else
        echo Hunspell $txtdir/$i.$ext ... >&2
        errs_hunspell=$(sed -E $repls_hunspell $txtdir/$i.$ext \
                | hunspell -l -p $priv_dic_native)
    fi

    #####################################################
    #   check for single letters
    #####################################################

    if [ "$check_for_single_letters" == yes ]
    then
        single_letters=$(grep -n '^' $txtdir/$i.$ext \
            | sed -E "s/\\<$acronyms//g" \
            | grep -E '\<[[:alpha:]]\>')
    fi

    #####################################################
    #   check foreign-language text with hunspell
    #####################################################

    errs_foreign=$(python3 $tex2txt_py $tex2txt_defs \
        --extr $foreign_macro --nums $txtdir/$i.$foreign.$num $i \
        | grep -n '^' \
        | hunspell -L -d $hunsp_foreign_lang -p $priv_dic_foreign)

    #####################################################
    #   output of results
    #####################################################

    if [[ ( -n "$single_letters" ) \
            || ( -n "$errs_foreign" ) \
            || ( "$LT_output_lines" >  1 ) \
            || ( -n "$errs_hunspell" ) ]]
    then
        echo '=================================================='
        echo $i
        echo '=================================================='
        echo
    fi
    if [ -n "$single_letters" ]
    then
        echo '=============='
        echo 'Single letters'
        echo '=============='
        echo "$single_letters" \
            | python3 -c "$repl_lines" '^(\d+)():' $txtdir/$i.$num
        echo
    fi
    if [ -n "$errs_foreign" ]
    then
        echo '==============================='
        echo 'Errors in foreign-language text'
        echo '==============================='
        echo "$errs_foreign" \
            | python3 -c "$repl_lines" '^(\d+)():' $txtdir/$i.$foreign.$num
        echo
    fi
    if [[ "$LT_output_lines" > 1 ]]
    then
        if [ -z "${options[--columns]}" ]
        then
            echo "$LT_output" \
                | python3 -c "$repl_lines" "$LT_info_line" $txtdir/$i.$num
        else
            echo "$LT_output" \
                | python3 -c "$repl_lines_columns" "$LT_info_line" \
                        $i $txtdir/$i.txt $txtdir/$i.$chr
        fi
        echo
    fi
    if [ -n "$errs_hunspell" ]
    then
        echo '============'
        echo 'Faulty lines'
        echo '============'
        grep -n '^' $txtdir/$i.$ext \
            | sed -E $repls_hunspell \
            | hunspell -L -p $priv_dic_native \
            | python3 -c "$repl_lines" '^(\d+)():' $txtdir/$i.$num
        echo
        echo '============='
        echo 'Unknown words'
        echo '============='
        echo "$errs_hunspell"
        echo
    fi

done

