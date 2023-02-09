#!/usr/bin/env python
import requests
import re
from bs4 import BeautifulSoup as bs

roud_pat = re.compile(r'Roud (V?[1-9][0-9]*)')
end_pat = re.compile(r'Music behind DJ|Liraz|Afro Yaqui') # Marathon shows
base = 'https://www.wfmu.org'
rouds = {}

rep = requests.get(base + '/playlists/CW')
lines = rep.text.splitlines()
lines.reverse()

done = False
for line in lines:
    if done:
        break
    if 'See the playlist' in line:
        url = line.split('href="',1)[1]
        url = url.split('"',1)[0]
        show_num = int(url.rsplit('/',1)[1])
        if show_num < 86529: # Segment has not yet started
            continue
        rep = requests.get(base + url)
        s = bs(rep.content, 'html.parser')
        tab = s.find_all(id='drop_table')[0]
        rows = tab.find_all('tr')
        roud_block = False
        n_block = 0
        n_single = 0
        for row in rows:
            if done:
                break
            text = row.text.strip()
            if not text or text[0] == '→' or end_pat.search(text):
                roud_block = False
            cells = row.find_all('td')
            single = False
            for i, cell in enumerate(cells):
                if match := roud_pat.search(cell.text):
                    n = match.group(1)
                    #if n.isdigit() and int(n) > 10:
                    #    done = True
                    #    break
                    print("Roud", n)
                    if n not in rouds:
                        rouds[n] = []
                    if i == 0:
                        roud_block = True
                        n_block = n
                    else:
                        single = True
                        n_single = n
            if single:
                rouds[n_single].append(row)
            elif roud_block:
                rouds[n_block].append(row)

def sort_key(x):
    if x.startswith('V'):
        return 1000*int(x[1:])
    else:
        return int(x)
keys = sorted(rouds.keys(), key=sort_key)
print(keys)

f = open('roud.html','w')
f.write('<table border=1>')
for key in keys:
    rows = rouds[key]
    for row in rows:
        f.write('<tr>\n')
        for c in row.find_all('td'):
            if any(x in c.attrs['class']
                   for x in ('col_media',
                             'col_record_label',
                             'col_image_favable',
                             'col_new_or_special_flag')):
                continue
            out = []
            wrote = False
            for a in c.find_all('a'):
                href = a.attrs.get('href')
                if href and href.startswith('/flashplayer'):
                    if wrote:
                        out.append('|') # delim

                    out.append('<a href="%s%s">Play</a>' % (base, href))
                    wrote = True
            if not wrote:
                text = c.text.split('→')[0].strip()
                if text:
                    if roud_pat.match(text):
                        if 'Roud 209: Poor Paddy' in text: # Oops!
                            text = text.replace('Roud 209', 'Roud 208')
                        text = '<i>'+text+'</i>'

                    out.append(text)
            if out:
                attrs = ''
                if 'colspan' in c.attrs and c['colspan']=='11':
                    attrs = ' align="center" colspan=6'
                    out.insert(0, '<font size=+1></br>')
                    out.append('</font>')
                f.write('<td%s>'%attrs + '\n'.join(out) + '</td>\n')
            else: # Empty cell
                f.write('<td></td>\n')
        f.write('</tr>\n')
f.write('</table>\n')
f.close()
