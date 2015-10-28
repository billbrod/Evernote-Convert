#!/usr/bin/env python

#Inspired by: https://gist.github.com/sebastien/dc18ee5c5a73cac539bb#file-enextractor-py
# and https://github.com/asoplata/evernote-to-markdown/blob/master/convert.py

import os,re,base64,mimetypes,sys,dateutil.parser,datetime
from xml.etree import ElementTree as ET
from html2text import html2text

def main(path):
    tree = ET.parse(path)
    for note in tree.iter('note'):
        write_note(process_note(note))

def process_note(note):
    title = note.find("title").text
    created = note.find("created").text
    updated = note.find("updated").text
    attributes = [{e.tag:e.text} for e in note.find("note-attributes").getchildren()]
    created = created or datetime.datetime.now()
    created = tuple(dateutil.parser.parse(created).timetuple())
    updated = tuple(dateutil.parser.parse(updated).timetuple()) if updated else created
    # The content requires some work
    content = note.find("content").text
    content = re.sub(u'u\xa0','',content)
    content = html2text(content)
    content = re.sub(u'\u2019', '\'', content)
    content = re.sub(u'\u2018', '\'', content)
    content = re.sub(u'\u2014', '----', content)
    content = re.sub(u'\u201c', '\"', content)
    content = re.sub(u'\u201d', '\"', content)
    content = re.sub('\\\\', '', content)
    rsrc = []
    for r in note.findall("resource"):
        data = r.find("data")
        mime = r.find("mime")
	if data is not None and data.get("encoding") is not None:
	    enc  = data.get("encoding")
	    assert enc == "base64", "Unsupported encoding: {0}".format(enc)
	    data = base64.decodestring(data.text)
	    # We take tha last extension (it's the most complete)
	    ext  = mimetypes.guess_all_extensions(mime.text)[-1]
	    rsrc.append(dict(
		data = data,
		mime = mime,
		ext  = ext,
	    ))    
    return dict(
            title      = title,
            created    = created,
            updated    = updated,
            attributes = attributes,
            content    = content,
            resources  = rsrc,
    )

def write_note(note,path="notes"):
    """Now need to decide how to format my Evernote text into something org-modey.
    
    TODO:
    - Deal with regular text (I had a tendency to indent lines
    when I wanted things to be coherent, instead make that part of one
    paragraph, making a new paragraph if there's a newline without
    indent; I also have two newlines sometimes between paragarphs;
    headers tend to be underlined but not all underlines are headers 
    [check if it's by itself or surrounded by newlines]; )
    - Deal with tables (there are some)
    - Deal with images/attachments (save them and link them?)
    - Deal with links
    - Deal with metadata
    - Save as .org (for a given .enex, put it in one .org file, since 
    I can organize them while exporting and then organize again when re-filing)
    - Add header for org file (startup options mainly)
    """
    print 'hi'

if __name__ == "__main__":
    main(*sys.argv[1:])
