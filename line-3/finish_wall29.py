"""Export the generated motif onto ancestor stone without altering other pixels."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

spec = importlib.util.spec_from_file_location('codec28', Path(__file__).with_name('finish_wall28.py'))
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)
ancestor = Path('artifacts/line-3/wall-v8.png')
out = Path('artifacts/line-3/wall-v9.png')
draft_hash = hashlib.sha256(out.read_bytes()).hexdigest()
w, h, c, original = codec.read_png(ancestor)
gw, gh, gc, draft = codec.read_png(out)
assert (w, h, c) == (1254, 1254, 3)
final = original[:]
x0, y0, mw, mh = 860, 590, 170, 85
for y in range(mh):
    for x in range(mw):
        sx, sy = 230 + x * 560 // mw, 350 + y * 280 // mh
        at = (sy * gw + sx) * gc
        r, g, b = draft[at:at+3]
        # Extract only dark strokes, discarding white backdrop and pale shadows.
        darkness = 1 - max(r, g, b) / 255
        red = r > g * 1.4 and r > b * 1.4
        alpha = min(.75, max(0, ((1 - (g+b)/510) if red else darkness) - .35) * 1.5)
        # Deterministic worn pigment gaps; no lines or shapes are added by code.
        if (x * 17 + y * 29) % 11 < 3:
            continue
        pigment = (163, 64, 29) if red else (38, 29, 20)
        target = ((y0+y)*w+x0+x)*3
        for ch in range(3):
            final[target+ch] = round(original[target+ch]*(1-alpha) + pigment[ch]*alpha)
changed = outside = 0
for n in range(w*h):
    if original[n*3:n*3+3] != final[n*3:n*3+3]:
        changed += 1
        outside += not (x0 <= n%w < x0+mw and y0 <= n//w < y0+mh)
assert changed and outside == 0
sha = codec.write_png(out, w, h, final)
continuation = Path('artifacts/line-3/wall.png')
assert not continuation.exists() or continuation.is_symlink()
if continuation.is_symlink():
    continuation.unlink()
continuation.symlink_to(out.name)
rgba = bytearray()
for y in range(512):
    ya, yb = y*h//512, (y+1)*h//512
    for x in range(512):
        xa, xb = x*w//512, (x+1)*w//512
        for ch in range(3):
            rgba.append(round(sum(final[(sy*w+sx)*3+ch] for sy in range(ya,yb) for sx in range(xa,xb))/((yb-ya)*(xb-xa))))
        rgba.append(255)
js = """
const fs = require('fs');
const encode = require('./line-3/tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js');
const data = fs.readFileSync(0);
const result = encode({data,width:512,height:512},77);
fs.writeFileSync('dist/line-3/29.jpg', result.data);
"""
subprocess.run(['node','-e',js],input=rgba,check=True)
report = {'wall':'artifacts/line-3/wall-v9.png','format':'PNG','dimensions':[w,h],
          'mode':'RGB','sha256':sha,'ancestor_sha256':hashlib.sha256(ancestor.read_bytes()).hexdigest(),
          'generated_motif_sha256':draft_hash,'changed_pixels':changed,
          'changed_pixels_outside_rectangle':outside,'new_mark_rectangle':[x0,y0,mw,mh],
          'thumbnail':{'path':'dist/line-3/29.jpg','format':'JPEG','dimensions':[512,512],
                       'bytes':Path('dist/line-3/29.jpg').stat().st_size},
          'unmet_visual_requirements':[], 'visual_review':'pending'}
Path('line-3/IMAGE-29.json').write_text(json.dumps(report,indent=2)+'\n')
record = {'name':'The Joined Stones','image':'https://api.imd.fun/artifacts/'+sha,
          'attributes':[{'trait_type':k,'value':v} for k,v in [
              ('Cave','Crystal'),('Wall','Line 3'),('Number',29),
              ('Left behind','Exact Phrase Finder'),
              ('Meaning','Joined ochre stones mark words found together across a gap.'),
              ('One thing','Offline document search with exact source line citations')]]}
Path('dist/line-3/29.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(report,indent=2))
