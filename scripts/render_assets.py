#!/usr/bin/env python3
"""Render the recorded CLI transcript; no output or numerical values are invented."""
from pathlib import Path
import re,textwrap,json
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
NAME='httpeek'
COLORS={'diffblast':'#5DE2B5','diffnote':'#B9A2FF','gitlore':'#FFBC78','httpeek':'#6CD8FF','vetagent':'#8BDFC5'}
TAGS={'diffblast':'Estimate impact. Choose tests.','diffnote':'From diff to reviewable draft.','gitlore':'Read the story in your Git history.','httpeek':'One terminal. Requests and mocks.','vetagent':'Review the permissions behind your agents.'}
ACCENT=COLORS[NAME]
ASSETS=ROOT/'assets';ASSETS.mkdir(exist_ok=True)

def font(size,mono=False):
    choices=(['/System/Library/Fonts/Menlo.ttc','/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'] if mono else ['/System/Library/Fonts/Supplemental/Arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'])
    for f in choices:
        try:return ImageFont.truetype(f,size)
        except OSError:pass
    return ImageFont.load_default(size=size)

def fitted(text,size,width,mono=False):
    f=font(size,mono)
    while f.getlength(text)>width and size>10:size-=1;f=font(size,mono)
    return f

raw=(ROOT/'demo/terminal.txt').read_text()
raw=re.sub(r'\x1b\[[0-9;]*m','',raw)
lines=[]
for line in raw.splitlines():
    lines.extend(textwrap.wrap(line,100,replace_whitespace=False,drop_whitespace=False) or [''])
# Show the opening report; remaining pages in the GIF continue the same transcript.
page_size=25
pages=[lines[i:i+page_size] for i in range(0,len(lines),page_size)] or [[]]
H=790;W=1120

def terminal(rows,count=None,page=0):
    im=Image.new('RGB',(W,H),'#0B1018');d=ImageDraw.Draw(im)
    d.rounded_rectangle((18,18,W-18,H-18),radius=18,fill='#121B28',outline='#2A384A',width=2)
    for i,c in enumerate(['#FF706B','#F7C361','#68D697']):d.ellipse((40+i*22,42,51+i*22,53),fill=c)
    d.text((125,37),NAME+' / real CLI capture',font=font(16),fill='#A3B3C9')
    d.line((38,74,W-38,74),fill='#2A384A')
    y=98
    for line in rows[:count]:
        c=ACCENT if line.lstrip().startswith(('$','GitLore','diffblast','diffnote','vetagent','→')) else '#D7E1EF'
        if 'HIGH (' in line or 'Risk ' in line or 'Score:' in line:c='#FFBC78'
        d.text((42,y),line,font=font(16,True),fill=c);y+=23
    d.text((42,H-60),'SYNTHETIC INPUT  /  ACTUAL PROGRAM OUTPUT',font=font(12,True),fill='#8294AB')
    d.text((W-155,H-60),f'{page+1:02}/{len(pages):02}',font=font(13,True),fill=ACCENT)
    return im

frames=[];durations=[]
for i,page in enumerate(pages):
    for count in range(0,len(page)+1,3):frames.append(terminal(page,count,i));durations.append(160)
    frames.append(terminal(page,len(page),i));durations.append(2600)
frames[0].save(ASSETS/'demo.tmp.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=True)
(ASSETS/'demo.tmp.gif').replace(ASSETS/'demo.gif')
terminal(pages[0],len(pages[0])).save(ASSETS/'demo.png')
# Flat vector logo kept editable in the repository.
icons={
'diffblast':'<path d="M18 32h28M32 18v28M22 22l20 20M42 22L22 42"/><circle cx="32" cy="32" r="8" fill="#121B28"/><circle cx="18" cy="32" r="3"/><circle cx="46" cy="32" r="3"/>',
'diffnote':'<path d="M22 14h15l8 8v28H22zM37 14v10h8M28 32h11M28 39h11"/>',
'gitlore':'<path d="M23 15v34M42 18v12Q42 38 23 38"/><circle cx="23" cy="18" r="4" fill="#121B28"/><circle cx="23" cy="46" r="4" fill="#121B28"/><circle cx="42" cy="18" r="4" fill="#121B28"/>',
'httpeek':'<path d="M23 20L11 32l12 12M41 20l12 12-12 12M36 16l-8 32"/>',
'vetagent':'<path d="M32 12l19 7v15Q49 46 32 54Q15 46 13 34V19zM22 32l7 7 14-15"/>',
}
(ASSETS/'logo.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-label="{NAME} logo"><rect width="64" height="64" rx="16" fill="#121B28"/><g fill="none" stroke="{ACCENT}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">{icons[NAME]}</g></svg>\n')
# A restrained, readable social card; the right panel uses actual captured output.
im=Image.new('RGB',(1280,640),'#0B1018');d=ImageDraw.Draw(im)
d.rectangle((0,0,12,640),fill=ACCENT)
d.text((58,64),'OPEN SOURCE / DEVELOPER TOOLS',font=font(15,True),fill=ACCENT)
d.text((54,136),NAME,font=fitted(NAME,68,555),fill='#F1F5FC')
y=240
for line in textwrap.wrap(TAGS[NAME],28):d.text((58,y),line,font=font(30),fill='#B6C5D8');y+=43
d.text((58,536),'Source install · Reproducible demo',font=font(18),fill='#8294AB')
d.rounded_rectangle((654,68,1234,570),radius=16,fill='#121B28',outline='#2A384A',width=2)
d.text((680,95),'ACTUAL CLI OUTPUT',font=font(13,True),fill=ACCENT)
y=138
for line in lines[:21]:
    f=fitted(line,12,525,True)
    d.text((680,y),line,font=f,fill=ACCENT if line.startswith('$') else '#C6D3E4');y+=18
im.save(ASSETS/'social-preview.png')
print(NAME+': rendered real transcript, GIF, SVG logo and 1280x640 social preview')
