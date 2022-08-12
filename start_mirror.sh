# !/bin/bash

# This command displays the contents of the term.txt file.
# The "+0" just means "display everything from the first byte of the file",
# and the "-f" means "wait, and if the file changes, display the changed
# file contents"

# Variables
PROJECT_DIR=$(dirname $0)
MIRROR_DIR=$PROJECT_DIR/magicmirror/mirror

python $MIRROR_DIR/make_term_file.py
python $MIRROR_DIR/cron_launcher.py
$PROJECT_DIR/color-watch.sh cat $MIRROR_DIR/term.txt
