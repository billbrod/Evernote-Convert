#!/usr/bin/env python

#Inspired by: https://gist.github.com/sebastien/dc18ee5c5a73cac539bb#file-enextractor-py
# and https://github.com/asoplata/evernote-to-markdown/blob/master/convert.py

import os,re,base64,mimetypes,sys,dateutil.parser,datetime
from xml.etree import ElementTree as ET
from html2text import html2text

def main(path):
    tree = ET.parse(path)
    attach_count = 0
    for note in tree.iter('note'):
        attach_count = write_note(process_note(note),attach_count,os.path.splitext(path)[0]+'.org')

def process_note(note):
    title = note.find("title").text if note.find('title') is not None else None
    created = note.find("created").text if note.find('created') is not None else datetime.datetime.now()
    attributes = [{e.tag:e.text} for e in note.find("note-attributes").getchildren()] if note.find('note-attributes') is not None else []
    created = dateutil.parser.parse(created).strftime("<%Y-%m-%d %a>")
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
	    # We take the last extension (it's the most complete)
	    ext  = mimetypes.guess_all_extensions(mime.text)[-1]
	    rsrc.append(dict(
		data = data,
		mime = mime,
		ext  = ext,
	    ))    
    return dict(
            title      = title,
            created    = created,
            attributes = attributes,
            content    = content,
            resources  = rsrc,
    )

def write_note(note,attach_count,path="notes"):
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
    
    Write now, tables are the biggest issue. Also, not all \n are being removed from the middle of paragraphs, so check why that is
    """
    with open(path,'a') as f:
        f.write("* %s\n"%note['title'])
        f.write("  %s\n\n"%note['created'])
        f.write("%s"%format_content(note['content']))
        if note['resources']:
            attach_path = os.path.dirname(path)+'/attachments/%s-%s%s'%(os.path.basename(path.split('.')[0]),'%s','%s')
            if not os.path.isdir(os.path.dirname(attach_path)):
                os.makedirs(os.path.dirname(attach_path))
            for resource in note['resources']:
                with open(attach_path%(attach_count,resource['ext']),'wb') as g:
                    g.write(resource['data'])
                f.write(" [[file:%s][Attachment %s]]\n"%(attach_path%(attach_count,resource['ext']),attach_count))
                attach_count+=1
        f.write("\n\n")
        
    return attach_count

def format_content(content):
    #Get rid of any mid-line newlines
    content = re.subn(r"([^\n\r])[\n\r]([^\n\r])",r"\1\2",content,re.M)[0]
    #Change link formatting to org mode
    content = re.subn(r"\[(.*?)\]\((.*?)\)",r'[[\1][\2]]',content)[0]
    #Combine paragraphs
    def upper_func(match):
        return ". %s"%match.group(1).upper()
    content = re.subn(r"\n\n  *([^\n\r])",upper_func,content)[0]
    #Indent new lines
    content = re.subn(r"(^|\n)",r"\1  ",content)[0]
    return content

if __name__ == "__main__":
    main(*sys.argv[1:])
