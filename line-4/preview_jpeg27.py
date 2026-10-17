"""Small standard-library baseline JPEG encoder for the wall's color preview.

Uses 4:2:0 sampling, separable DCT and deliberately simple valid Huffman tables.
Build helper only; the dependency tool does not import this module.
"""
import math
import struct

LUMA = [16,11,10,16,24,40,51,61,12,12,14,19,26,58,60,55,
        14,13,16,24,40,57,69,56,14,17,22,29,51,87,80,62,
        18,22,37,56,68,109,103,77,24,35,55,64,81,104,113,92,
        49,64,78,87,103,121,120,101,72,92,95,98,112,100,103,99]
CHROMA = [17,18,24,47,99,99,99,99,18,21,26,66,99,99,99,99,
          24,26,56,99,99,99,99,99,47,66,99,99,99,99,99,99] + [99]*32
ZIG = []
for diagonal in range(15):
    coords = [(y, diagonal-y) for y in range(8) if 0 <= diagonal-y < 8]
    if diagonal % 2 == 0:
        coords.reverse()
    ZIG.extend(y*8+x for y,x in coords)
T = [[.5 * (1/math.sqrt(2) if u == 0 else 1) *
      math.cos((2*x+1)*u*math.pi/16) for x in range(8)] for u in range(8)]


def encode(pixels, width, height, quality=40):
    assert width % 16 == height % 16 == 0
    assert len(pixels) == width*height*3 and 1 <= quality <= 100
    scale = 5000/quality if quality < 50 else 200-2*quality
    quant = [[max(1, min(255, int((n*scale+50)/100))) for n in table]
             for table in (LUMA, CHROMA)]
    planes = [[0.0]*(width*height), [0.0]*(width*height//4), [0.0]*(width*height//4)]
    for y in range(height):
        for x in range(width):
            r,g,b = pixels[(y*width+x)*3:(y*width+x)*3+3]
            planes[0][y*width+x] = .299*r+.587*g+.114*b-128
            sub = (y//2)*(width//2)+x//2
            planes[1][sub] += (-.168736*r-.331264*g+.5*b)/4
            planes[2][sub] += (.5*r-.418688*g-.081312*b)/4
    out = bytearray(b'\xff\xd8')

    def marker(kind, payload):
        out.extend(bytes([255,kind])+struct.pack('>H',len(payload)+2)+payload)

    marker(0xe0, b'JFIF\0\x01\x01\0\0\x01\0\x01\0\0')
    marker(0xdb, b''.join(bytes([i])+bytes(q[j] for j in ZIG) for i,q in enumerate(quant)))
    marker(0xc0, bytes([8])+struct.pack('>HH',height,width)+bytes([3,1,0x22,0,2,0x11,1,3,0x11,1]))
    # Avoid an all-ones code; JPEG reserves it for scan padding.
    ac_symbols = [0, 0xf0]+[(run << 4)|size for run in range(16) for size in range(1,11)]
    dc_counts, ac_counts = [0]*16, [0]*16
    dc_counts[3], ac_counts[7] = 12, len(ac_symbols)
    marker(0xc4, bytes([0])+bytes(dc_counts)+bytes(range(12))+
           bytes([0x10])+bytes(ac_counts)+bytes(ac_symbols))
    marker(0xda, bytes([3,1,0,2,0,3,0,0,63,0]))
    ac_codes = {symbol: i for i,symbol in enumerate(ac_symbols)}
    pending, bits = 0, 0

    def emit(value, count):
        nonlocal pending, bits
        pending = (pending << count)|value
        bits += count
        while bits >= 8:
            bits -= 8
            byte = (pending >> bits)&255
            out.append(byte)
            if byte == 255:
                out.append(0)
        pending &= (1 << bits)-1

    def amplitude(value):
        size = abs(value).bit_length()
        return size, value if value >= 0 else value+(1 << size)-1

    def coefficients(plane, stride, bx, by, table):
        rows = [[sum(plane[(by+y)*stride+bx+x]*T[u][x] for x in range(8))
                 for u in range(8)] for y in range(8)]
        result = [round(sum(rows[y][u]*T[v][y] for y in range(8))/table[v*8+u])
                  for v in range(8) for u in range(8)]
        return [result[j] for j in ZIG]

    previous = [0,0,0]

    def block(component, bx, by):
        values = coefficients(planes[component], width if component == 0 else width//2,
                              bx, by, quant[0 if component == 0 else 1])
        delta = values[0]-previous[component]
        previous[component] = values[0]
        size, value = amplitude(delta)
        assert size <= 11
        emit(size,4)
        emit(value,size)
        run = 0
        for n in values[1:]:
            if n == 0:
                run += 1
                continue
            while run >= 16:
                emit(ac_codes[0xf0],8)
                run -= 16
            size, value = amplitude(n)
            assert size <= 10
            emit(ac_codes[(run << 4)|size],8)
            emit(value,size)
            run = 0
        if run:
            emit(ac_codes[0],8)

    for my in range(0,height,16):
        for mx in range(0,width,16):
            for dy,dx in ((0,0),(0,8),(8,0),(8,8)):
                block(0,mx+dx,my+dy)
            block(1,mx//2,my//2)
            block(2,mx//2,my//2)
    if bits:
        emit((1 << (8-bits))-1,8-bits)
    out.extend(b'\xff\xd9')
    return bytes(out)


def resize(pixels, width, height, target=512):
    """Bilinear RGB preview; no intermediate image files."""
    result = bytearray(target*target*3)
    for y in range(target):
        sy = (y+.5)*height/target-.5
        iy = max(0,min(height-2,int(sy)))
        fy = sy-iy
        for x in range(target):
            sx = (x+.5)*width/target-.5
            ix = max(0,min(width-2,int(sx)))
            fx = sx-ix
            for c in range(3):
                a = pixels[(iy*width+ix)*3+c]*(1-fx)+pixels[(iy*width+ix+1)*3+c]*fx
                b = pixels[((iy+1)*width+ix)*3+c]*(1-fx)+pixels[((iy+1)*width+ix+1)*3+c]*fx
                result[(y*target+x)*3+c] = max(0,min(255,round(a*(1-fy)+b*fy)))
    return result
