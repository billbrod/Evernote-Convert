@echo off
setlocal enabledelayedexpansion
set InputFiles="C:\Users\wfb6\Desktop\Evernotes\*.html"
set OutImages="C:\Users\wfb6\Desktop\Markdowns\Images\"
set tmpFile="C:\Users\wfb6\Desktop\Markdowns\tmp.md"

for %%i in (%InputFiles%) do (
    set infile=%%i
    echo(!infile!
    if not !infile!==C:\Users\wfb6\Desktop\Evernotes\Evernote_index.html (
        set images=!infile:.html=_files!
    	set outfile=!infile:html=md!
	set outfile=!outfile:Evernotes=Markdowns!
	set outfile=!outfile: =-!
	set outfile=!outfile:,=!
    	echo(!outfile!
    	echo(!images!
	xcopy /s /Y "!images!" "!OutImages!"
	pandoc "!infile!" -s -o "!outfile!"
	python str_replace.py "!outfile!"
    	echo(
    )
)
