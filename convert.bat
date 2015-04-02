@echo off
setlocal enabledelayedexpansion
set InputFiles="C:\Users\wfb6\Desktop\Evernotes\*.html"

for %%i in (%InputFiles%) do (
    set infile=%%i
    echo(!infile!
    if not !infile!==C:\Users\wfb6\Desktop\Evernotes\Evernote_index.html (
        set images=!infile:.html=_files!
    	set outfile=!infile:html=md!
	set outfile=!outfile:Evernotes=Markdowns!
	set outfile=!outfile: =-!
	set outfile=!outfile:,=!
	set outimages=!outfile:.md=_files!
	if not exist "!outimages!" mkdir !outimages!
	xcopy /s "!images!" "!outimages!"
	pandoc "!infile!" -s -o "!outfile!"
	python str_replace.py "!outfile!"
    	echo(
    )
)
