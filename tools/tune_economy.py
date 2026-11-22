r"""Raining Eggs - fits every price (zones, baskets, treadmill, luck) to a target play-time curve with sim_economy.py.

  py tools/tune_economy.py   -> prints the new tables (paste into game/Config.lua) and the final times

Curve (v148, user): very fast at the start (hook), then each next step takes longer. Targets are minutes of play.
"""
import math
import random
import statistics
import sys

sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import sim_economy as S

HOURS = 75


def geo(n, first, last):
    r = (last / first) ** (1 / (n - 1))
    return [first * r ** k for k in range(n)]


# targets in minutes
ZONE_T = {2: 1, 3: 3, 4: 7, 5: 15, 6: 30, 7: 55, 8: 95, 9: 160, 10: 260,
          12: 400, 13: 560, 14: 760, 15: 1000, 16: 1300, 17: 1650, 18: 2050, 19: 2550, 20: 3150}
BASKET_T = geo(19, 0.7, 1100)   # basket 2 after 15 s ... basket 20 after ~18 h
TRAIN_T = geo(60, 0.7, 3600)     # treadmill level 1 after 12 s ... level 60 after ~60 h
LUCK_T = geo(20, 1.0, 2400)      # luck 1 after 30 s ... luck 20 after ~40 h

# start from the current prices
zp = list(S.ZONE_PRICE)
bk = list(S.BASKETS)
tr = [S.cost('train', k) for k in range(60)]
lk = [S.cost('luck', k) for k in range(20)]


def apply():
    S.ZONE_PRICE[:] = zp
    S.BASKETS[:] = bk
    S.TRAIN_COST = tr
    S.LUCK_COST = lk


def times(runs=7):
    logs = [S.play(random.Random(100 + s), HOURS)[0] for s in range(runs)]
    def med(key):
        ts = [l.get(key, math.inf) for l in logs]
        return statistics.median(ts) / 60
    return med


def fix(table, idx, actual, target, k=0.8):
    if actual == math.inf:
        f = 0.4
    else:
        f = max(0.25, min(4.0, (target / max(actual, 0.05)) ** k))
    table[idx] *= f


def monotone(t, start=0, step=1.15):
    for i in range(max(1, start), len(t)):
        if t[i - 1] and t[i] < t[i - 1] * step:
            t[i] = t[i - 1] * step


for it in range(int(sys.argv[1]) if len(sys.argv) > 1 else 28):
    apply()
    med = times()
    err = []
    for z, tt in ZONE_T.items():
        a = med(f'zone {z}')
        err.append(abs(math.log((a + 0.05) / tt)) if a < math.inf else 3)
        fix(zp, z - 1, a, tt)
    for j, tt in enumerate(BASKET_T):
        a = med(f'basket {j + 1}')
        err.append(abs(math.log((a + 0.05) / tt)) if a < math.inf else 3)
        fix(bk, j + 1, a, tt)
    for j, tt in enumerate(TRAIN_T):
        a = med(f'train {j + 1}')
        fix(tr, j, a, tt, 0.6)
    for j, tt in enumerate(LUCK_T):
        a = med(f'luck {j + 1}')
        fix(lk, j, a, tt, 0.6)
    zp[10] = 0
    bk[1], tr[0], lk[0] = max(bk[1], 25), max(tr[0], 10), max(lk[0], 60)   # floors: nothing is free
    for t in (bk, tr, lk):
        monotone(t, step=1.3)
    for i in range(1, len(zp)):
        if i != 10 and zp[i - 1] and zp[i] < zp[i - 1] * 2:
            zp[i] = zp[i - 1] * 2
    print(f'iter {it}: mean log error {statistics.mean(err):.2f}', flush=True)


def r(x):
    if x == 0:
        return '0'
    e = int(math.floor(math.log10(x)))
    m = round(x / 10 ** e, 1)
    if e < 4:
        return str(int(round(x, -max(0, e - 1))))
    return f'{m:g}e{e}'


apply()
med = times(15)
print('\nC.ZONE_PRICE = {', ', '.join(r(x) for x in zp), '}')
print('C.BASKET_PRICES =', [r(x) for x in bk])
print('C.TRAIN_COST = {', ', '.join(r(x) for x in tr), '}')
print('C.LUCK_COST = {', ', '.join(r(x) for x in lk), '}')
print('\nminutes: target / sim')
for z, tt in ZONE_T.items():
    print(f'  zone {z:2d}  {tt:6.0f} / {med(f"zone {z}"):7.1f}')
for j in (0, 2, 5, 9, 14, 18):
    print(f'  basket {j + 2:2d}  {BASKET_T[j]:6.1f} / {med(f"basket {j + 1}"):7.1f}')
for j in (0, 4, 9, 19, 39, 59):
    print(f'  train {j + 1:2d}  {TRAIN_T[j]:6.1f} / {med(f"train {j + 1}"):7.1f}')
for j in (0, 4, 9, 14, 19):
    print(f'  luck {j + 1:2d}  {LUCK_T[j]:6.1f} / {med(f"luck {j + 1}"):7.1f}')
