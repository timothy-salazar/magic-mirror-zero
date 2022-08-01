# !/bin/bash

# Variables
PROJECT_DIR=$(dirname $0)

# This command displays the contents of the term.txt file.
# The "+0" just means "display everything from the first byte of the file",
# and the "-f" means "wait, and if the file changes, display the changed
# file contents"
tail +0 -f $PROJECT_DIR/magicmirror/mirror/term.txt
