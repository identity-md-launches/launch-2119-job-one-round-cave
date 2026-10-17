"""Composite image-tool pigment onto bare inherited rock; retain all other pixels."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

spec = importlib.util.spec_from_file_location('png29', 'gathering/finish_wall.py')
png = importlib.util.module_from_spec(spec)
spec.loader.exec_module(png)
OLD = Path('artifacts/line-2/wall-v8.png')
NEW = Path('artifacts/line-2/wall-v9.png')
RECT = (730, 220, 95, 135)


def main():
    ancestor = hashlib.sha256(OLD.read_bytes()).hexdigest()
    assert ancestor == '8f0c7e9860f0ed0c3dc639d1f0e8cf9a5d81155fc3b1b9e20e08a441d0b5124f'
    generated = hashlib.sha256(NEW.read_bytes()).hexdigest()
    assert generated == 'ace335b56170d93c0a53e614321000dbbe830c0ca34827e71006e0a9caa44fea', 'expected original generated motif; do not run twice'
    width, height, original = png.read_png(OLD)
    dw, dh, draft = png.read_png(NEW)
    assert (width, height) == (1254, 1254)
    final = original[:]
    dx, dy, pw, ph = RECT
    # Source crop holds the three generated twigs, ochre tie and chalk pebble.
    sx, sy, sw, sh = round(dw*.40), round(dh*.245), round(dw*.19), round(dh*.455)
    for y in range(ph):
        for x in range(pw):
            source = ((sy+y*sh//ph)*dw + sx+x*sw//pw)*3
            target = ((dy+y)*width+dx+x)*3
            r, g, b = draft[source:source+3]
            dark = r < 97 and g < 79 and b < 65
            tie = ph*.51 < y < ph*.72 and r > 1.8*g and r > 2.7*b
            chalk = y > ph*.85 and pw*.27 < x < pw*.74 and r > 158 and g > 125 and b > 95
            if dark or tie or chalk:
                fade = max(0, min(1, x/3, y/3, (pw-1-x)/3, (ph-1-y)/3))
                alpha = .82 * fade
                for c in range(3):
                    final[target+c] = round(original[target+c]*(1-alpha)+draft[source+c]*alpha)
    changed = outside = 0
    for i in range(width*height):
        if final[3*i:3*i+3] != original[3*i:3*i+3]:
            changed += 1
            x, y = i % width, i // width
            outside += not (dx <= x < dx+pw and dy <= y < dy+ph)
    assert outside == 0 and changed > 1000
    digest = png.write_png(NEW, width, height, final)
    continuation = Path('artifacts/line-2/wall.png')
    if continuation.is_symlink():
        continuation.unlink()
    continuation.symlink_to('wall-v9.png')
    rgba = bytearray()
    for y in range(512):
        ya, yb = y*height//512, (y+1)*height//512
        for x in range(512):
            xa, xb = x*width//512, (x+1)*width//512
            count = (yb-ya)*(xb-xa)
            for c in range(3):
                rgba.append(round(sum(final[(sy*width+sx)*3+c] for sy in range(ya,yb) for sx in range(xa,xb))/count))
            rgba.append(255)
    # The inherited ordinary-file JPEG encoder is used only for media conversion.
    js = """
const fs = require('fs');
const encode = require('./line-3/tools/corpus-change-receipt/vendor/jpeg-js/lib/encoder.js');
const data = fs.readFileSync(0);
const result = encode({data,width:512,height:512},78);
if(result.data.length>100000)throw Error('JPEG too large');
fs.writeFileSync('dist/line-2/29.jpg',result.data);
"""
    subprocess.run(['node','-e',js],input=rgba,check=True)
    report = {'round':29,'ancestorSha256':ancestor,'generatedMotifSha256':generated,
              'wallSha256':digest,'dimensions':[width,height],'format':'PNG','channels':'RGB',
              'newMarkRectangle':list(RECT),'changedPixels':changed,
              'changedPixelsOutsideRectangle':outside,
              'method':'Image-tool-generated twig bundle; selected pigment composited onto bare inherited rock.',
              'visualReview':'Pending final inspection','unmetVisualRequirements':[], 'images':[]}
    for path, kind, size in ((NEW,'PNG',[1254,1254]),(continuation,'PNG',[1254,1254]),
                             (Path('dist/line-2/29.jpg'),'JPEG',[512,512])):
        data = path.read_bytes()
        report['images'].append({'path':str(path),'format':kind,'dimensions':size,
                                 'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    Path('line-2/REVIEW-29.json').write_text(json.dumps(report,indent=2)+'\n')
    traits = [('Cave','Crystal'),('Wall','Line 2'),('Number',29),('Left behind','Proof Pack'),
              ('Meaning','Separate branches share one bundle without losing their paths.'),
              ('One thing','Verify Ethereum account and storage proofs against trusted state roots')]
    record = {'name':'The Bound Twigs','image':'https://api.imd.fun/artifacts/'+digest,
              'attributes':[{'trait_type':key,'value':value} for key,value in traits]}
    Path('dist/line-2/29.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
