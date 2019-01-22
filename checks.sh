
#
#   Bash:
#   Do for the given LaTeX files:
#
#   . convert to raw text (Python script tex2txt.py)
#   . call LanguageTool (LT) for native-language main text and
#     separately for footnotes
#   . look for single letters (exclude: variable acronyms below)
#     (if check_for_single_letters set to yes)
#   . check foreign-language text using hunspell
#   . at beginning: append private dictionary to LT's spelling.txt,
#     and create entries in LT's prohibit.txt
#
#   - option --nolt:
#     do not call LT, instead only use hunspell
#     (replace before: variable repls_hunspell below)
#   - option --del:
#     remove auxiliary directory $txtdir, and exit
#   - without arguments: check "all" files
#
#
#                                   Matthias Baumann, 2018-2019
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

#   LanguageTool for check of native-language text
#
LTprefix=../LT/LanguageTool-4.4
LTcommand="$LTprefix/languagetool-commandline.jar \
    --language de-DE --encoding utf-8 \
    --disable \
WHITESPACE_RULE,\
KOMMA_VOR_UND_ODER"

tooldir=Tools/LT            # Python scripts and private dictionaries
txtdir=$tooldir/Tex2txt     # directory for extraction of raw text 
                            # (subdirectories will be created if necessary)
ext=txt                     # file name extension for raw text
num=lin                     # ... for line number information
foreign=en                  # ... for foreign-language text
foot=foot                   # ... for footnote text
ori=ori                     # ... for original dictionary files in LT tree

#   Tex2txt script
#
tex2txt_py=$tooldir/tex2txt.py
tex2txt_repl="--repl $tooldir/repls.txt"
tex2txt_defs="--defs $tooldir/defs.py"

#   sed filter for hunspell (on option --nolt):
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


##########################################################
##########################################################

if [ X$1 == X--del ]
then
    read -p "enter YES to remove directory '$txtdir': " repl
    if [ "$repl" == YES ]
    then
        rm -fr $txtdir
    fi
    exit
fi

trap exit SIGINT

#   adjust LT's spelling files
#
if [ -z "$option_nolt" ]
then
    if [ -f $lt_dic_native.$ori ]
    then
        cp $lt_dic_native.$ori $lt_dic_native
    else
        # create backup copy, if not yet present
        cp $lt_dic_native $lt_dic_native.$ori
    fi
    cat $priv_dic_native >> $lt_dic_native
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
        echo "$0: cannot read file '$i'"
        exit 1
    fi
    dir=$(dirname $txtdir/$i)
    if [ ! -d $dir ]
    then
        if ! mkdir -p $dir
        then
            echo "$0: cannot create directory '$dir'"
            exit 1
        fi
    fi

    #####################################################
    # extract raw text, save line numbers
    #####################################################

    python3 $tex2txt_py \
        $tex2txt_repl $tex2txt_defs --nums $txtdir/$i.$num $i \
        > $txtdir/$i.$ext
    python3 $tex2txt_py \
        --extr footnote,footnotetext \
        $tex2txt_repl $tex2txt_defs --nums $txtdir/$i.$foot.$num $i \
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
                | hunspell -l -p $priv_dic_native)
        if (( $foot_text_size > 0 ))
        then
            errs_hunspell_foot=$(sed -E $repls_hunspell $txtdir/$i.$foot.$ext \
                    | hunspell -l -p $priv_dic_native)
        else
            errs_hunspell_foot=
        fi
    fi

    #####################################################
    #   check for single letters
    #####################################################

    if [ "$check_for_single_letters" == yes ]
    then
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

    if [[ ( -n "$single_letters$single_letters_foot" ) \
            || ( -n "$errs_foreign" ) \
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
        echo '=============='
        echo 'Single letters'
        echo '=============='
        echo "$single_letters" \
            | python3 -c "$repl_lines" '^(\d+):' $txtdir/$i.$num
        echo "$single_letters_foot" \
            | python3 -c "$repl_lines" '^(\d+):' $txtdir/$i.$foot.$num
        echo
    fi
    if [ -n "$errs_foreign" ]
    then
        echo '==============================='
        echo 'Errors in foreign-language text'
        echo '==============================='
        echo "$errs_foreign" \
            | python3 -c "$repl_lines" '^(\d+):' $txtdir/$i.$foreign.$num
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
        echo '============'
        echo 'Faulty lines'
        echo '============'
        grep -n '^' $txtdir/$i.$ext \
            | sed -E $repls_hunspell \
            | hunspell -L -p $priv_dic_native \
            | python3 -c "$repl_lines" '^(\d+):' $txtdir/$i.$num
        grep -n '^' $txtdir/$i.$foot.$ext \
            | sed -E $repls_hunspell \
            | hunspell -L -p $priv_dic_native \
            | python3 -c "$repl_lines" '^(\d+):' $txtdir/$i.$foot.$num
        echo
        echo '============='
        echo 'Unknown words'
        echo '============='
        echo "$errs_hunspell$errs_hunspell_foot"
        echo
    fi

done

