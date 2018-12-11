
#
#   Bash:
#   Do for the given LaTex files:
#
#   . convert to raw text (our Python script tex2txt.py)
#   . call LanguageTool (LT)
#   . look for single letters (exclude: variable acronyms below)
#   . check arguments of \engl{...} using hunspell (english)
#   . at beginning: append our private dictionary to LT's spelling.txt,
#     and create entries in LT's prohibit.txt
#
#   - option --nolt:
#     do not call LT, instead only use hunspell
#     (replace before: variable repls_hunspell below)
#   - without arguments: check "all" files
#
#
#                                   Matthias Baumann, November 2018
#

if [ X$1 == X--nolt ]
then
    option_nolt=1
    shift
fi

if (( $# == 0 ))
then
    args="vorwort.tex */*.tex"
else
    args=$*
fi

LTprefix=../LT/LanguageTool-4.3
LTprefix=../LT/LanguageTool-4.4-SNAPSHOT
LTcommand="$LTprefix/languagetool-commandline.jar \
    --language de-DE --encoding utf-8 \
    --disable \
WHITESPACE_RULE,\
KOMMA_VOR_UND_ODER"

tooldir=Tools/LT            # Python scripts and private dictionaries
txtdir=$tooldir/Tex2txt     # place for extraction of raw text 
                            # assumption: necessary subdirectories exist
ext=txt                     # file name extension for raw text
num=lin                     # ... for line number information
engl=en                     # ... for Englisch text
foot=foot                   # ... for footnote text
ori=ori                     # ... for original files in LT tree

#   sed filter for hunspell:
#   '0' --> 'Null'
#
repls_hunspell=' -e s/\<0\>/Null/g'
# repls_hunspell+=' -e s/\$\$/GCHQ/g'

#   list of accepted acronyms during search for single letters;
#   use normal space here (is replaced by nbsp)
#
acronyms='d\. h\.|f\. ü\.|i\. A\.|u\. a\.|v\. g\. V\.|z\. B\.'

utf8_nbsp=$(python3 -c 'print("\N{NO-BREAK SPACE}", end="")')
acronyms=$(echo -n $acronyms | sed -E "s/ /$utf8_nbsp/g")


#   append private hunspell dictionary to LT's spelling.txt
#   XXX: or better ignore.txt?
#
lt_dic_de=$LTprefix/org/languagetool/resource/de/hunspell/spelling.txt
priv_dic_de=$tooldir/hunspell.de
priv_dic_en=$tooldir/hunspell.en

#   prohibit certain words
#
lt_prohib=$LTprefix/org/languagetool/resource/de/hunspell/prohibit.txt
priv_prohib=$tooldir/prohibit.de

##########################################################
##########################################################

# find $txtdir -type f -exec rm {} \;
# exit

trap exit SIGINT

#   adjust LT's spelling files
#
if [ -z "$option_nolt" ]
then
    if [ -f $lt_dic_de.$ori ]
    then
        cp $lt_dic_de.$ori $lt_dic_de
    else    # create backup copy, if not yet present
        cp $lt_dic_de $lt_dic_de.$ori
    fi
    cat $priv_dic_de >> $lt_dic_de
    if [ -f $lt_prohib.$ori ]
    then
        cp $lt_prohib.$ori $lt_prohib
    else
        cp $lt_prohib $lt_prohib.$ori
    fi
    cat $priv_prohib >> $lt_prohib
fi

#   Python3:
#   add original line numbers to messages
#   - argv[1]: RE search pattern; first () group must contain the number
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
                    + m.string[m.end(1):m.end(0)])
    return m.group(0)
for lin in sys.stdin:
    sys.stdout.write(re.sub(expr, repl, lin))
'

##########################################################
##########################################################

for i in $args
do
    if [ ! -r $i ]
    then
        echo "$0: kann '$i' nicht lesen"
        exit
    fi

    #####################################################
    # extract raw text, save line numbers
    #####################################################

    python3 $tooldir/tex2txt.py \
        --repl $tooldir/repls.txt --nums $txtdir/$i.$num $i \
        > $txtdir/$i.$ext
    python3 $tooldir/tex2txt.py \
        --extr footnote,footnotetext \
        --repl $tooldir/repls.txt --nums $txtdir/$i.$foot.$num $i \
        > $txtdir/$i.$foot.$ext
    foot_text_size=$(wc -c < $txtdir/$i.$foot.$ext)

    #####################################################
    # call LT or hunspell
    #####################################################

    if [ -z "$option_nolt" ]
    then
        if [[ "$OS" =~ Windows ]]
        then
            # under Cygwin: LT with Windows Java produces Latin-1
            LTfilter() { iconv -f latin1 -t utf8; }
        else
            LTfilter() { cat; }
        fi
        LT_output=$(java -jar $LTcommand $txtdir/$i.$ext \
            | LTfilter \
            | python3 -c "$repl_lines" \
                    '^\d+\.\) Line (\d+), column \d+,' $txtdir/$i.$num)
        LT_output_lines=$(echo "$LT_output" | wc -l)
        if (( $LT_output_lines == 1 ))
        then
            echo $LT_output > /dev/tty
        fi
        if (( $foot_text_size > 0 ))
        then        # save energy: only if file not empty
            LT_foot_output=$(java -jar $LTcommand $txtdir/$i.$foot.$ext \
                | LTfilter \
                | python3 -c "$repl_lines" \
                    '^\d+\.\) Line (\d+), column \d+,' $txtdir/$i.$foot.$num)
            LT_foot_output_lines=$(echo "$LT_foot_output" | wc -l)
            if (( $LT_foot_output_lines == 1 ))
            then
                echo $LT_foot_output > /dev/tty
            fi
        else
            LT_foot_output=
            LT_foot_output_lines=
        fi
    else
        errs_hunspell=$(sed -E $repls_hunspell $txtdir/$i.$ext \
                | hunspell -l -p $priv_dic_de)
        if (( $foot_text_size > 0 ))
        then
            errs_hunspell_foot=$(sed -E $repls_hunspell $txtdir/$i.$foot.$ext \
                    | hunspell -l -p $priv_dic_de)
        else
            errs_hunspell_foot=
        fi
    fi

    #####################################################
    #   check for single letters
    #####################################################

    single_letters=$(grep -n '^' $txtdir/$i.$ext \
        | sed -E "s/\\<$acronyms//g" \
        | grep -E '\<[[:alpha:]]\>')
    if (( $foot_text_size > 0 ))
    then
        single_letters_foot=$(grep -n '^' $txtdir/$i.$foot.$ext \
            | sed -E "s/\\<$acronyms//g" \
            | grep -E '\<[[:alpha:]]\>')
    else
        single_letters_foot=
    fi

    #####################################################
    #   check English text with hunspell
    #####################################################

    errs_engl=$(python3 $tooldir/tex2txt.py \
        --extr engl --nums $txtdir/$i.$engl.$num $i \
        | grep -n '^' \
        | hunspell -L -d en_GB -p $priv_dic_en)

    #####################################################
    #   output of results
    #####################################################

    if [[ ( -n "$single_letters$single_letters_foot" ) \
            || ( -n "$errs_engl" ) \
            || ( "$LT_output_lines" >  1 ) \
            || ( "$LT_foot_output_lines" >  1 ) \
            || ( -n "$errs_hunspell$errs_hunspell_foot" ) ]]
    then
        echo '=================================================='
        echo $i
        echo '=================================================='
        echo
    fi
    if [ -n "$single_letters$single_letters_foot" ]
    then
        echo '==================='
        echo 'einzelne Buchstaben'
        echo '==================='
        echo "$single_letters" \
            | python3 -c "$repl_lines" '^(\d+):' $txtdir/$i.$num
        echo "$single_letters_foot" \
            | python3 -c "$repl_lines" '^(\d+):' $txtdir/$i.$foot.$num
        echo
    fi
    if [ -n "$errs_engl" ]
    then
        echo '========================='
        echo 'Fehler im englischen Text'
        echo '========================='
        echo "$errs_engl" \
            | python3 -c "$repl_lines" '^(\d+):' $txtdir/$i.$engl.$num
        echo
    fi
    if [[ ( "$LT_output_lines" > 1 ) \
            || ( "$LT_foot_output_lines" > 1 ) ]]
    then
        echo "$LT_output$LT_foot_output"
        echo
    fi
    if [ -n "$errs_hunspell$errs_hunspell_foot" ]
    then
        echo '=================='
        echo 'fehlerhafte Zeilen'
        echo '=================='
        grep -n '^' $txtdir/$i.$ext \
            | sed -E $repls_hunspell \
            | hunspell -L -p $priv_dic_de \
            | python3 -c "$repl_lines" '^(\d+):' $txtdir/$i.$num
        grep -n '^' $txtdir/$i.$foot.$ext \
            | sed -E $repls_hunspell \
            | hunspell -L -p $priv_dic_de \
            | python3 -c "$repl_lines" '^(\d+):' $txtdir/$i.$foot.$num
        echo
        echo '=================='
        echo 'unbekannte Woerter'
        echo '=================='
        echo "$errs_hunspell$errs_hunspell_foot"
        echo
    fi

done

