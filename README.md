# magic-mirror-zero
The purpose of this project is to create some lightweight code that will duplicate some of the functionality of existing magic mirror software, but without as much overhead.
The [most popular magic mirror software](https://github.com/MichMich/MagicMirror) requires a raspberry pi 3 running the full desktop version of Raspberry Pi OS, as well as Electron. That seems like overkill for a project that's displaying a small amount of information on a screen. 
This version will:
- run on a Raspberry Pi Zero
- require only Raspberry Pi OS lite

As a trade off, this will have a largely text based display paradigm, with only crude graphics available.  

## Organization
The central idea of this approach is as follows:
- The Raspberry Pi Zero running the lite version of the OS provides a terminal window
- We can grab the width and height of the terminal window (in columns and lines) using os.get_terminal_size()
- We can then embed all the information we're interested in dispalying into a block of text term_width x term_height characters in size. This block of text will be stored as a text file called term.txt.
- Each plugin we enable will be run as a cron job run on a specified schedule. These will update the relevant section of text in term.txt.
    - For example: we've made a plugin that retrieves the weather and displays the forecast. We've specified that this forecast is to be displayed in the upper left corner of our magic mirror (let's say the first 40 columns and the first 3 rows). When the cron job is executed we would retrieve the forecast, convert it to a block of text no larger than 40x3 characters, and insert it into term.txt
