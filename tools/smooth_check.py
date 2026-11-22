import math, random, statistics, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import sim_economy as S
out = open(pathlib.Path(__file__).parent / 'tune_out.txt', encoding='utf-8').read()
def tbl(name):
    m = re.search(name + r' = [\{\[](.*?)[\}\]]', out)
    return [float(x.strip(" '")) for x in m.group(1).split(',')]
def smooth(t, start=0, passes=3):
    l = [math.log(max(x, 1)) for x in t]
    for _ in range(passes):
        l = [l[0]] + [(l[i - 1] + 2 * l[i] + l[i + 1]) / 4 for i in range(1, len(l) - 1)] + [l[-1]]
    r = [math.exp(x) for x in l]
    for i in range(1, len(r)):
        r[i] = max(r[i], r[i - 1] * 1.25)
    return r
def rnd(x):
    if x < 1000: return str(int(round(x, -1 if x >= 100 else 0)))
    e = int(math.floor(math.log10(x))); return f'{round(x / 10 ** e, 1):g}e{e}'
zp = tbl('C.ZONE_PRICE'); bk = tbl('C.BASKET_PRICES'); tr = tbl('C.TRAIN_COST'); lk = tbl('C.LUCK_COST')
bk = [0] + smooth(bk[1:]); tr = smooth(tr); lk = smooth(lk)
for t in (zp, bk, tr, lk):
    t[:] = [float(rnd(x)) if x else 0 for x in t]
S.ZONE_PRICE[:] = zp; S.BASKETS[:] = bk; S.TRAIN_COST = tr; S.LUCK_COST = lk
logs = [S.play(random.Random(500 + s), 75)[0] for s in range(15)]
med = lambda k: statistics.median([l.get(k, math.inf) for l in logs]) / 60
print('ZONE', '{ ' + ', '.join(rnd(x) if x else '0' for x in zp) + ' }')
print('BASK', [rnd(x) if x else '0' for x in bk])
print('TRAIN', '{ ' + ', '.join(rnd(x) for x in tr) + ' }')
print('LUCK', '{ ' + ', '.join(rnd(x) for x in lk) + ' }')
for k in [f'zone {z}' for z in (2,3,4,5,6,7,8,9,10,12,14,16,18,20)] + [f'basket {j}' for j in (1,3,6,10,15,19)] + [f'train {j}' for j in (1,5,10,20,40,60)] + [f'luck {j}' for j in (1,5,10,15,20)] + ['rebirth 1 possible']:
    print(f'{k:20s} {med(k):8.1f} min')
