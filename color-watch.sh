# !/bin/sh
# author: https://stackoverflow.com/users/3276936/tk009
# source: https://stackoverflow.com/a/69388883/19669305
# accessed: 2022-08-01

trap "tput cnorm" EXIT  # unhide the cursor when the script exits or is interrupted

# simple interval parameter parsing, can be improved
INTERVAL=2
case $1 in
  -n|--interval)
    INTERVAL="$2"
    shift; shift
  ;;
esac

clear           # clear the terminal
tput civis      # invisible cursor, prevents cursor flicker

while true; do
  tput cup 0 0  # move cursor to topleft, without clearing the previous output
  sh -c "$*"    # pass all arguments to sh, like the original watch
  tput ed       # clear all to the end of window, if the new output is shorter
  sleep "$INTERVAL"
done
