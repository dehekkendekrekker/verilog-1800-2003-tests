s=$1
s=${s##*/}
BASENAME="${s%.*}"

cat << EOF
[gold]
read_rtlil ../rtlil/verific/${BASENAME}.il
hierarchy -auto-top
proc

[gate]
read_rtlil ../rtlil/slang/${BASENAME}.il
hierarchy -auto-top

[strategy sby]
use sby
depth 2
engine smtbmc bitwuzla
EOF

