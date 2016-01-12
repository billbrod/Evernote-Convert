#!/usr/bin/env python

#Inspired by: https://gist.github.com/sebastien/dc18ee5c5a73cac539bb#file-enextractor-py
# and https://github.com/asoplata/evernote-to-markdown/blob/master/convert.py

import os,re,base64,mimetypes,sys,dateutil.parser,datetime,hashlib,glob,getpass
from xml.etree import ElementTree as ET
from html2text import html2text
from unidecode import unidecode

def main(glob_path="~/Dropbox/Docs/Evernote/*.enex"):
    glob_path = os.path.expanduser(glob_path)
    credentials = {}
    credentials['username'] = raw_input("Input username: ")
    credentials['password'] = getpass.getpass("Input password: ")
    #We want to assign a unique id to each note, so we can link them
    note_dict = dict((note.find('title').text,hashlib.md5(note.find('title').text).hexdigest()) for path in glob.glob(glob_path) for note in ET.parse(path).iter('note'))
    for path in glob.glob(glob_path):
        if path=='/home/billbrod/Dropbox/Docs/Evernote/test.enex':
            continue
        print("Parsing %s"%path)
        tree = ET.parse(path)
        attach_count = 0
        for note in tree.iter('note'):
            attach_count = write_note(process_note(note),attach_count,note_dict,credentials,os.path.splitext(path)[0]+'.org')

def process_note(note):
    title = note.find("title").text if note.find('title') is not None else None
    created = note.find("created").text if note.find('created') is not None else datetime.datetime.now()
    attributes = [{e.tag:e.text} for e in note.find("note-attributes").getchildren()] if note.find('note-attributes') is not None else []
    created = dateutil.parser.parse(created).strftime("<%Y-%m-%d %a>")
    # The content requires some work
    content = note.find("content").text
    content = html2text(content)
    content = re.sub('\\\\', '', content)
    #This replaces unicode characters with the "best guess" in
    #ascii. Since we don't have any accented or non-English
    #characters, I'm pretty sure all the unicode is just punctuation,
    #which this should take care of without any issues.
    content = unidecode(content)
    rsrc = []
    for r in note.findall("resource"):
        data = r.find("data")
        mime = r.find("mime")
	if data is not None and data.get("encoding") is not None:
	    enc  = data.get("encoding")
	    assert enc == "base64", "Unsupported encoding: {0}".format(enc)
	    data = base64.decodestring(data.text)
            # To get the extension, we grab the end of the the filename from the resource attributes            
            try:
                ext = os.path.splitext(r.find('resource-attributes').find('file-name').text)[-1]
            #If it doesn't have resource-attributes, we hope mimetypes does the job
            except AttributeError:
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

def write_note(note,attach_count,note_dict,credentials,path="notes"):
    """Now need to decide how to format my Evernote text into something org-modey.
    
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
    
    Right now, tables are the biggest issue. Also, not all \n are
    being removed from the middle of paragraphs, so check why that is
    -- fixed the \n's, but I think tables may be too difficult. Since
    they're infrequent, probably best to go through and fix them by
    hand, they're not too far off. The real issue is that it's not
    really clear where I would want a table to start (i.e., what
    should be the first column of a table header and what's the text
    beforehand), which makes it impossible to parse them. When they
    get converted, they're missing the | that starts the table (and
    the one at the end of each row) and I can't come up with a good
    way to determine where to put it.

    """
    with open(path,'a') as f:
        print("Writing headline %s in note %s"%(note['title'],path))
        f.write("* %s\n"%note['title'])
        f.write("  %s\n"%note['created'])
        f.write("  :PROPERTIES:\n  :ID: %s\n  :END:\n\n"%note_dict[note['title']])
        f.write("%s\n"%format_content(note['content'],note_dict,credentials))
        if note['resources']:
            attach_path = os.path.dirname(path)+'.Attachments/%s-%s%s'%(os.path.basename(os.path.splitext(path)[0]),'%s','%s')
            if not os.path.isdir(os.path.dirname(attach_path)):
                os.makedirs(os.path.dirname(attach_path))
            for resource in note['resources']:
                with open(attach_path%(attach_count,resource['ext']),'wb') as g:
                    g.write(resource['data'])
                f.write("  [[file:%s][Attachment %s]]\n"%(attach_path%(attach_count,resource['ext']),attach_count))
                attach_count+=1
        f.write("\n\n")
        
    return attach_count

def format_content(content,note_dict,credentials):
    #Get rid of any mid-line newlines
    content = re.subn(r"([^\n\r])[\n\r]([^\n\r])",r"\1\2",content,re.M)[0]
    content = re.subn(r"(.)[\n\r](.)",r"\1\2",content)[0]
    #Change link formatting to org mode
    content = re.subn(r"\[(.*?)\]\((.*?)\)",r'[[\2][\1]]',content)[0]
    #Combine paragraphs
    def upper_func(match):
        return ". %s"%match.group(1).upper()
    content = re.subn(r"\n\n  *([^\n\r])",upper_func,content)[0]
    #Indent new lines
    content = re.subn(r"(^|\n)",r"\1  ",content)[0]
    #If we have links to other notes, they will be linked via a unique id.
    #First we find all urls that have evernote in them
    for url in re.findall("(?P<url>https?://www.evernote[^\s\]]+)", content):
        #Then we use evernote_get_title to find the title of the note and find its unique id in note_dict
        try:
            content = re.subn(url,"id:%s"%note_dict[evernote_get_title(url,credentials)],content)[0]
        except:
            content = re.subn(url,"dead link",content)[0]
    return content

def evernote_get_title(url,credentials):
    import mechanize,cookielib
    browser = mechanize.Browser()
    # Cookie Jar
    cj = cookielib.LWPCookieJar()
    browser.set_cookiejar(cj)
    # Browser options
    browser.set_handle_equiv(True)
    browser.set_handle_gzip(True)
    browser.set_handle_redirect(True)
    browser.set_handle_referer(True)
    browser.set_handle_robots(False)
    # Follows refresh 0 but not hangs on refresh > 0
    browser.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    browser.open(url)
    browser.select_form(nr = 0)
    browser.form['username'] = credentials["username"]
    browser.form['password'] = credentials["password"]
    browser.submit()
    title = browser.title()
    browser.close()
    return title

if __name__ == "__main__":
    main(*sys.argv[1:])
