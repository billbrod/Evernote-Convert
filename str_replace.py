#!C:\Users\wfb6\AppData\Local\Continuum\Anaconda\python.exe

from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def main(file_name):
    import os
    import re
    image_path = file_name.split('\\')[-1].split('.')[0]+'_files'
    f = open(file_name)
    text = f.read()
    f.close()
    os.remove(file_name)
    s = MLStripper()
    s.feed(text)
    text = s.get_data()
    text = text.decode('utf8')
    text=text.replace(u'\xa0',' ')
    text = text.replace(u'\x00','')
    text = str(text)
    text = re.sub('---(?s)(.*)\.\.\.','',text)
    oldtext=None
    while text!=oldtext:
        oldtext=text
        text = re.sub('\n\n\n','\n',text)
    text = re.sub('\!\[\]\((.*)\/','![](./'+image_path+'/',text)
    text = text.replace('\\',' ')
    text = re.sub('\n(?=.)',' ',text)
    text = re.sub('[ .](?=\!\[)','\n',text)
    text = re.sub('(?=\n\!\[)','\n',text)
    text = re.sub('==(.*)==','\n\n',text)
    text = '---\ngeometry: margin=2cm\n---\n\n'+text
    f = open(file_name,'w')
    f.write(text)
    f.close()
    
if __name__=="__main__":
    import sys
    main(*sys.argv[1:])