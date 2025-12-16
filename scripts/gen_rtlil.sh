s=$1
s=${s##*/}
BASENAME="${s%.*}"


/home/dhk/tools/tabby/bin/yosys -p "read_verilog -sv $1; write_rtlil ../rtlil/verific/${BASENAME}.il"
/usr/local/bin/yosys -m slang -p "read_slang --no-proc $1; write_rtlil ../rtlil/slang/${BASENAME}.il"
