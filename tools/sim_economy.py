r"""Raining Eggs - economy simulator: how long a normal player needs for each zone, rebirth, upgrades.

  py tools/sim_economy.py              -> table of times with the numbers in game/Config.lua
  py tools/sim_economy.py --runs 40    -> more players averaged (default 20)

Reads ZONE_PRICE, the zone pet incomes / speed requirements, RARITY, TIER, BASKETS, PEN_MAX, STORAGE_MAX,
REBIRTH_BONUS and INDEX_BONUS from Config.lua; the formulas (upgrade costs, train power, walk speed, luck...)
are copied from Config.lua below - keep them in step when they change there.

The player model is simple on purpose (one trip = catch until the basket is full, walk home, deposit, a little
treadmill time, buy what you can afford). Real players are a bit slower (AFK, menus, rotten eggs) and a bit faster
(storms, BIG EGG, daily rewards, game passes are left out), so read the result as "about".
"""
import math
import pathlib
import random
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CFG = (ROOT / 'game' / 'Config.lua').read_text(encoding='utf-8')


def num(name):
    return float(re.search(r'^C\.%s\s*=\s*([0-9.e+-]+)' % name, CFG, re.M).group(1))


def arr(name):
    body = re.search(r'^C\.%s\s*=\s*\{([^}]*)\}' % name, CFG, re.M).group(1)
    return [float(v) for v in re.findall(r'[0-9.]+(?:e[0-9]+)?', body)]


ZONE_PRICE = arr('ZONE_PRICE')
# world 1 zones are "\tzone(...)" lines; world 2 zones are "C.ZONES[C.NZ + k] = zone(...)" (no speed number: HUGE)
ZONES = [(math.inf if r == 'HUGE' else float(r), float(inc))
         for r, inc in re.findall(r'^(?:\t|C\.ZONES\[C\.NZ \+ \d+\] = )zone\("[^"]+",\s*([0-9.e+]+|HUGE),\s*([0-9.e+]+)', CFG, re.M)]
NZ = len(re.findall(r'^\tzone\(', CFG, re.M))   # the 10 normal zones (index, rebirth)
NT = len(ZONES)                                 # every zone a player can open (world 2 included)
RAR = [(float(o), float(m)) for o, m in re.findall(r'odds = ([0-9.]+), mult = ([0-9.]+)', CFG)]
TIER = [float(m) for m in re.findall(r'\{ name = "[A-Za-z ]*", mult = ([0-9.]+) \}', CFG)]
BASKETS = [float(p) for p in re.findall(r'\{ name = "[^"]+", price = ([0-9.e+]+) \}', CFG)]
PEN_MAX, STORAGE_MAX = int(num('PEN_MAX')), int(num('STORAGE_MAX'))
REBIRTH_BONUS, INDEX_BONUS, FUSE = num('REBIRTH_BONUS'), num('INDEX_BONUS'), int(num('FUSE'))
GOLDEN_CHANCE, GOLDEN_LUCK = 1 / 30, num('GOLDEN_LUCK')
MAX_LV = dict(train=60, basket=len(BASKETS) - 1, luck=20)
_t = re.search(r'normal = \{ ([0-9.]+), ([0-9.]+), ([0-9.]+) \}', CFG)
TIER_ODDS = [float(x) for x in _t.groups()] if _t else [1, 0, 0]
AUTO_FUSE = bool(re.search(r'^C\.AUTO_FUSE\s*=\s*true', CFG, re.M))
TRAIN_COST = arr('TRAIN_COST') if re.search(r'^C\.TRAIN_COST', CFG, re.M) else None   # v148: price tables
LUCK_COST = arr('LUCK_COST') if re.search(r'^C\.LUCK_COST', CFG, re.M) else None


# ---------------------------------------------------------------- formulas (copied from Config.lua)
def cost(kind, lv):
    if kind == 'train' and TRAIN_COST:
        return TRAIN_COST[lv] if lv < len(TRAIN_COST) else math.inf
    if kind == 'luck' and LUCK_COST:
        return LUCK_COST[lv] if lv < len(LUCK_COST) else math.inf
    if kind == 'train':
        return math.floor(40 * 3 ** lv)
    if kind == 'basket':
        return BASKETS[lv + 1] if lv + 1 < len(BASKETS) else math.inf
    return math.floor(250 * 5 ** lv)


def train_power(lv):
    return math.floor(2 * 2.2 ** lv + 0.5)


def walk_speed(speed):
    return min(16 + 7 * math.log10(1 + speed), 100)


def rebirth_mult(n):
    return 1 + REBIRTH_BONUS * n


REBIRTH_SCALE = num('REBIRTH_SPEED_SCALE') if re.search(r'^C\.REBIRTH_SPEED_SCALE', CFG, re.M) else 1.0


def rebirth_need(n):
    zi = min(3 + n, NZ)
    return ZONES[zi - 1][0] * 10 ** max(0, 3 + n - NZ) * REBIRTH_SCALE


def roll(luck, rng):
    for i in range(len(RAR) - 1, 0, -1):
        if rng.random() < min(luck / RAR[i][0], 0.9):
            return i
    return 0


# ---------------------------------------------------------------- one player
TREAD_SHARE = 0.15          # part of every trip spent on the treadmill
EGG_RATE = 0.5 * (1.2 + 0.7)  # eggs a second in a zone with one player (server: egg rain)
HOP = 30.0                  # studs between two eggs you chase


def play(rng, hours=30.0, verbose=False):
    t, cash, speed = 0.0, 0.0, 0.0
    lv = dict(train=0, basket=0, luck=0)
    reb, unlocked = 0, 1
    pets, index = [], set()          # pets: list of (zone, rarity, tier)
    log = {}

    def mark(k):
        log.setdefault(k, t)

    def inc_of(p):
        return ZONES[p[0] - 1][1] * RAR[p[1]][1] * TIER[p[2]]

    def zones_done():
        return sum(1 for z in range(1, NZ + 1) if all((z, i) in index for i in range(len(RAR))))

    def income():
        best = sorted(pets, key=inc_of, reverse=True)[:PEN_MAX]
        return sum(map(inc_of, best)) * rebirth_mult(reb) * (1 + INDEX_BONUS * zones_done())

    def fuse():
        again = True
        while again:
            again = False
            seen = {}
            for k, p in enumerate(pets):
                if p[2] < len(TIER) - 1:
                    seen.setdefault(p, []).append(k)
                    if len(seen[p]) == FUSE:
                        for k2 in sorted(seen[p], reverse=True):
                            pets.pop(k2)
                        pets.append((p[0], p[1], p[2] + 1))
                        again = True
                        break

    while t < hours * 3600:
        z = unlocked
        ws = walk_speed(speed)
        n = 3 + lv['basket']
        rate = min(EGG_RATE * 0.65, ws / HOP) * 0.9                 # rotten eggs (10 %) are not worth catching
        dist = 160 + 140 * (z - 1) - 70                             # pen -> middle of the zone
        dt = n / rate + 2 * dist / ws
        dt_tread = dt * TREAD_SHARE
        cash += income() * (dt + dt_tread)
        t += dt + dt_tread
        speed += train_power(lv['train']) * rebirth_mult(reb) * 4 * dt_tread
        for k in range(n):
            combo = 1 + min(k, 20) * 0.05
            luck = (1 + 0.25 * lv['luck']) * combo * (GOLDEN_LUCK if rng.random() < GOLDEN_CHANCE else 1)
            i = roll(luck, rng)
            r = rng.random()                                   # v152 coat roll: C.TIER_ODDS (golden eggs ignored here)
            pets.append((z, i, 2 if r < TIER_ODDS[2] else 1 if r < TIER_ODDS[2] + TIER_ODDS[1] else 0))
            index.add((z, i))
        if AUTO_FUSE:
            fuse()
        pets.sort(key=inc_of, reverse=True)
        while len(pets) > PEN_MAX + STORAGE_MAX:
            cash += inc_of(pets.pop()) * 30
        # spend: next zone first, then the cheapest upgrade you can pay
        while True:
            if unlocked < NT and cash >= ZONE_PRICE[unlocked]:   # zone 11 = price 0 (the Golden Portal)
                cash -= ZONE_PRICE[unlocked]
                unlocked += 1
                mark(f'zone {unlocked}')
                continue
            opts = [(cost(k, lv[k]), k) for k in lv if lv[k] < MAX_LV[k]]
            opts = [o for o in opts if o[0] <= cash * 0.6]          # keep some cash for the next zone
            if not opts:
                break
            c, k = min(opts)
            cash -= c
            lv[k] += 1
            mark(f'{k} {lv[k]}')
        if speed >= rebirth_need(reb):
            mark(f'rebirth {reb + 1} possible')
        for zd in range(1, zones_done() + 1):
            mark(f'index {zd} zones')
    return log, dict(lv=lv, income=income(), speed=speed, pets=len(pets))


def fmt(s):
    if s is None:
        return '   -   '
    m = s / 60
    return f'{m:5.0f} min' if m < 90 else f'{m / 60:5.1f} h  '


if __name__ == '__main__':
    runs = int(sys.argv[sys.argv.index('--runs') + 1]) if '--runs' in sys.argv else 20
    hours = float(sys.argv[sys.argv.index('--hours') + 1]) if '--hours' in sys.argv else 30
    logs = [play(random.Random(s), hours)[0] for s in range(runs)]
    keys = [f'zone {z}' for z in range(2, NT + 1)] + ['rebirth 1 possible', 'rebirth 2 possible']
    print(f'{runs} players, {hours:.0f} h each; median time of play to reach:')
    for k in keys:
        ts = sorted(l[k] for l in logs if k in l)
        med = ts[len(ts) // 2] if len(ts) * 2 > runs else None
        price = ZONE_PRICE[int(k.split()[1]) - 1] if k.startswith('zone') else None
        print(f'  {k:20s} {fmt(med)}' + (f'   (price {price:,.0f})' if price else '') + ('' if med is not None else '   (most players not within the time)'))
