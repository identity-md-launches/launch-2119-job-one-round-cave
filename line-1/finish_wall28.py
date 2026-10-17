"""Preserve the ancestor wall and add only generated pigment on unused rock."""
import hashlib
import json
from pathlib import Path
from finish_wall24 import read_png, write_png, thumbnail


def main():
    wall = Path('artifacts/line-1/wall.png')
    output = Path('artifacts/line-1/wall-v9.png')
    ancestor = wall.read_bytes()
    ancestor_sha = hashlib.sha256(ancestor).hexdigest()
    assert ancestor_sha == '54c423d23974db32fc52056cad2e1c5ee08926d7ef506f03d6bee0b99440275b'
    width, height, old = read_png(ancestor)
    gw, gh, pigment = read_png(output)
    assert (width, height) == (1254, 1254)
    assert (gw, gh) == (1536, 1024)
    final = old[:]
    x0, y0, mw, mh = 900, 330, 210, 100
    sx0, sy0, sw, sh = 130, 260, 1280, 480
    for y in range(mh):
        for x in range(mw):
            sx, sy = sx0 + int(x * sw / mw), sy0 + int(y * sh / mh)
            rgb = pigment[(sy * gw + sx) * 3:(sy * gw + sx) * 3 + 3]
            strength = max(rgb)
            if strength < 30:
                continue
            alpha = min(.78, (strength - 30) / 160)
            alpha *= min(1, x / 5, y / 5, (mw - 1 - x) / 5, (mh - 1 - y) / 5)
            i = ((y0 + y) * width + x0 + x) * 3
            for channel in range(3):
                final[i + channel] = round(old[i + channel] * (1 - alpha) + rgb[channel] * alpha)
    changed = outside = 0
    for pixel in range(width * height):
        if old[pixel * 3:pixel * 3 + 3] != final[pixel * 3:pixel * 3 + 3]:
            changed += 1
            x, y = pixel % width, pixel // width
            outside += not (x0 <= x < x0 + mw and y0 <= y < y0 + mh)
    assert changed and outside == 0
    sha = write_png(output, width, height, final)
    assert read_png(output)[2] == final
    wall.write_bytes(output.read_bytes())
    jpeg = Path('dist/line-1/28.jpg')
    thumbnail(output.read_bytes(), jpeg)
    report = {
        'ancestor_sha256': ancestor_sha, 'wall_sha256': sha,
        'wall_paths': [str(output), str(wall)], 'dimensions': [width, height],
        'format': 'PNG', 'mode': 'RGB',
        'thumbnail': {'path': str(jpeg), 'dimensions': [512, 512],
                      'format': 'JPEG', 'bytes': jpeg.stat().st_size},
        'mark_rectangle': [x0, y0, mw, mh], 'changed_pixels': changed,
        'changed_pixels_outside_rectangle': outside,
        'method': 'Built-in imagegen motif; only generated pigment blended onto bare rock.',
        'unmet_visual_requirements': [],
        'location_conflict': 'Used the specifically required dist/line-1/28.jpg despite the general no-pictures-outside-artifacts sentence.'}
    Path('line-1/IMAGE-28.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
