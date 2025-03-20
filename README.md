# BC95XLTprog
Cross-platform programming for the Uniden BC95XLT "NASCAR" Scanner

## The Story
I've been frustrated for years that Uniden didn't support programming my BC95XLT scanner via macOS. 

When I moved to an Apple Silicon Mac and Parallels for Windows emulation, my last Windows program for editing channels stopped working, due to some connectivity problem with Parallels (I think). I'd had it, and decided to write my own. By design, I wrote it to work on Mac, Windows and Linux.

Given that it took a couple days sitting in a camper at Sebring International Raceway to create, I was pretty surprised nobody at Uniden ever bothered. Likewise the guys at BUTEL, who provided the commercial software I'd used for years.

## The Program
This program is designed explicitly for the BC95XLT scanner, a pretty old model, and is likely not to work with any other scanner, Uniden or others. I've tested the program with a scanner to DB-9 serial cable, and serial adapters using Prolific and FTDI converter chips. Other cables, including scanner-to-USB cables probably will work, but no promises here.

The program works on macOS, Windows and Linux (tested Ubuntu so far), with 64-bit ARM and AMD 64 architectures.

BC95XLTprog takes what will necessarily be a correctly-formatted CSV file, and uses it to program channels into the scanner. Likewise, it can read and create such a file from channels already in the scanner.

Your best choice for managing channels is probably a spreadsheet program, like Excel, Libre Office's Calc spreadsheet, Google Docs' Sheet, or perhaps macOS' Numbers (though I've never tried that one). You'll need to save your spreadsheet as a CSV (Comma-Separated Value) file.

In general, spreadsheets offer a lot more flexibility in handling tabular data than any scanner channel management program I've tried. Masochists can queue for Notepad or vi.

## Making your CSV file
Your CSV file will need to have 5 columns minimum:

- Channel: ###
- Frequency: ###.####
- Lockout: Y|N
- Priority: Y|N
- Delay: Y|N

Optionally you can add a 6th column for Comments, but this is completely ignored by the program, as is any column after 5, and as is any line beginning with non-numeric text vs. an integer.

Your CSV file should probably not use quotes for text specifiers (though this is untested at this writing). A trailing quote before the end-of-line specifier is fine.

Note that the program is not terribly picky about your CSV file (it'll take channel 5, as well as channel 005, and 451.05 as well as 451.0500 frequencies), but neither is there any attempt to ensure you're giving it a valid CSV file.

Formatting the CSV file is on you, the user, and the program will attempt to program your radio with just about anything you throw at it.

Remember: If you try stupid things, expect stupid things to happen.

## The provided goods
There are Mac, Windows and Linux executables provided, in ARM64 and AMD 64 builds. **If these don't work for you, you can install Python 3.12 (and above) and pyserial and run the BC95XLTprog.py python file directly.**

These executables are not signed, and on macOS you'll need to control-click (or right-click) and open the program from the context menu the first time, as macOS will complain about it.

Example CSV files are provided:

- IMSA_Jan_2025.csv - the channels I desparately wanted programmed into my scanner in the first place
- ClearAllChannels.csv - will zero your BC95XLT back to factory channels (all zeroes)
- JustAFewChannels.csv - demonstrates how to program a few channels, if you don't wanna change all 200
- Crazy_Stuff_in_there.csv - shows tolerance for mixed text (which you might use to comment a section)
