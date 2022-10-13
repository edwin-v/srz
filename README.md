# srz

Srz is a simple tool to keep download and update custom songs for Synth Riders from synthriderz.com.
This tool is primarily aimed used at Linux users because the main program [NoodleManagerX](https://github.com/tommaier123/NoodleManager)
does not seem to run properly at this time.

## Installation

The program only consists of a single Python script, so it can be placed anywhere:
- Copy it somewhere in the search path (e.g. `$HOME/.local/bin`)
- Make it executable
- Verify the python executable on the first line of `srz.py`
- Change the **SYNTHRIDERS_DIR** variable to the FULL PATH of your Synth Riders installation in `srz.py` line 4

(Optional) Enable the one-click installer
- Copy the `srz.desktop` file to `$HOME/.local/share/applications`
- Type: `xdg-mime default srz.desktop x-scheme-handler/synthriderz`

## Usage

Important to note is that the game assumes that all custom songs follow
the new naming scheme for songs: `(id)[-(version)]-(artist)-(title)-(mapper).synth`.
However, it can detect older files from their meta file and rename them.
Some (even older) files don't have meta files and those can't be detected.
It is recommended to delete and redownload those.

Use the update command to make sure that all songs are (re)named to the
current naming scheme.

Commands are:

`srz.py c`

Check installed files. This command lists the status of all installed custom
songs. Songs can be ok, ok with old naming style, out of date or not found (on
synthriderz.com). No changes are made.

`srz.py u`

Check if installed songs are up-to-date and download the replacement if it's not.
Songs that are up-to-date but do not follow the current naming scheme are renamed.

`srz.py d id`

Download a song with **id** to the CustomSongs directory.

`srz.py d url`

Download using a synthriderz:// url to the CustomSongs directory. This option
is used for the one-click downloads.

`srz.py a`

Download all songs that are not currently installed or up-to-date. This may take
some time.

`srz.py i id`

Display some information for the song identified by **id**.

`srz.py s keyword`

Search the song database on synthriderz.com for "keyword". Multiple words are
allowed, but used as a single search word.

## Disclaimer

This is just a quick little project to make it easier to deal with custom songs.
It is not a replacement for the synthriderz.com site or NoodleManagerX. It may
not be perfect, so **use at your own risk**. Some functions (like checking) make A 
LOT of connections to the synthriderz.com site if you have a large list, so
don't overuse them. I have some ideas to improve that in the future.
