"""One-shot extraction of image-generated pigment onto unused ancestral rock."""
import hashlib
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('png_codec27', Path(__file__).with_name('finish_wall22.py'))
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)
ancestor = Path('artifacts/line-4/wall.png')
output = Path('artifacts/line-4/wall-v9.png')
assert ancestor.read_bytes() == Path('artifacts/line-4/wall-v8.png').read_bytes()
old_sha = hashlib.sha256(ancestor.read_bytes()).hexdigest()
w, h, original = codec.read_png(ancestor)
dw, dh, draft = codec.read_png(output)
assert (w, h) == (1254, 1254)
assert (dw, dh) == (w, h)
# The image tool's pigment has already been scaled into this patch. Remove the
# residual generated ochre background between the three individual pebbles.
final = original[:]
x0, y0, x1, y1 = 320, 815, 550, 1035
for y in range(y0, y1):
    for x in range(x0, x1):
        if y >= 968 and not any(((x-cx)/rx)**2 + ((y-cy)/ry)**2 < 1
                for cx,cy,rx,ry in [(347,995,17,18),(435,1008,18,19),(520,995,17,18)]):
            continue
        at = (y*w+x)*3
        final[at:at+3] = draft[at:at+3]
points = [(i % w, i // w) for i in range(w*h)
          if final[3*i:3*i+3] != original[3*i:3*i+3]]
assert points and all(x0 <= x < x1 and y0 <= y < y1 for x,y in points)
sha = codec.write_png(output, w, h, final)
assert codec.read_png(output)[2] == final

preview_spec = importlib.util.spec_from_file_location('preview27', Path(__file__).with_name('preview_jpeg27.py'))
preview = importlib.util.module_from_spec(preview_spec)
preview_spec.loader.exec_module(preview)
small = preview.resize(final, w, h)
jpeg = preview.encode(small, 512, 512, quality=40)
assert len(jpeg) < 100000
Path('dist/line-4/27.jpg').write_bytes(jpeg)
ancestor.write_bytes(output.read_bytes())
evidence = {'ancestor_sha256': old_sha, 'wall_sha256': sha,
            'dimensions': [w,h], 'format': 'PNG', 'mode': 'RGB',
            'outputs': ['artifacts/line-4/wall-v9.png', 'artifacts/line-4/wall.png'],
            'new_mark_rectangle_xyxy': [x0,y0,x1,y1], 'changed_pixels': len(points),
            'changed_pixels_outside_rectangle': 0,
            'method': 'Built-in image tool generated three ochre choices and converging charcoal paths. Extracted pigment was shrunk onto unused lower-left rock. Every pixel outside the patch is identical to the ancestor.',
            'preview': {'path':'dist/line-4/27.jpg', 'format':'JPEG', 'dimensions':[512,512], 'bytes':len(jpeg)},
            'unmet_visual_requirements': []}
Path('line-4/IMAGE-27.json').write_text(json.dumps(evidence, indent=2)+'\n')
record = {'name': 'Paths That Still Reach', 'image': 'https://api.imd.fun/artifacts/'+sha,
          'attributes': [{'trait_type':'Cave','value':'Crystal'},
                         {'trait_type':'Wall','value':'Line 4'},
                         {'trait_type':'Number','value':27},
                         {'trait_type':'Left behind','value':'Release Map'},
                         {'trait_type':'Meaning','value':'Three ochre choices follow charcoal paths to a shared chalk stone, showing which choices can still work together.'},
                         {'trait_type':'One thing','value':'Finite offline dependency resolution'}]}
Path('dist/line-4/27.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(evidence, indent=2))
