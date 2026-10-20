"""Synthesize the 15s soundtrack: a 130 BPM trot-EDM track with SFX synced to scene.html.

Sections (seconds):  groove 0-6.45 | tape-stop crash 6.45-8 | rebound 8-9 | build 9-11.15
                     | Bali-win bridge 11.15-12 | "아모르 파티" drop 12-FIN | ring-out FIN-15
"""
import wave, os
import numpy as np

SR, DUR, BPM = 44100, 15.0, 130
BEAT = 60 / BPM
DROP = 12.0
FIN = DROP + 5 * BEAT              # final unison hit, same as scene.html
GRID0 = DROP - 28 * BEAT           # beat grid placed so the drop lands on a bar downbeat
N = int(SR * DUR)
rng = np.random.default_rng(7)

def bus(): return np.zeros((N, 2))
music, half, sfx, verb_send = bus(), bus(), bus(), bus()

def add(b, sig, t, gain=1.0, pan=0.0):
    i = int(round(t * SR))
    if i >= N or t < 0: return
    sig = sig[: N - i] * gain
    b[i:i + len(sig), 0] += sig * (1 - max(0, pan))
    b[i:i + len(sig), 1] += sig * (1 + min(0, pan))

def env(n, a=0.003, d=None):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a)
    return e * (np.exp(-t / d) if d else 1)

def osc(f, dur, kind='sine', d=None, a=0.003, phase=0.0):
    n = int(dur * SR)
    f = np.asarray(f, float)
    f = np.full(n, float(f)) if f.ndim == 0 else f[:n]
    ph = 2 * np.pi * np.cumsum(f) / SR + phase
    if kind == 'sine': s = np.sin(ph)
    elif kind == 'saw': s = 2 * ((ph / (2 * np.pi)) % 1) - 1
    elif kind == 'square': s = np.sign(np.sin(ph))
    else: s = 2 * np.abs(2 * ((ph / (2 * np.pi)) % 1) - 1) - 1
    return s * env(n, a, d)

def noise(dur, d=0.05, a=0.001): n = int(dur * SR); return rng.standard_normal(n) * env(n, a, d)

def fft_filter(x, lo=None, hi=None):
    """Brick-ish band filter with soft edges, done in the frequency domain."""
    X = np.fft.rfft(x, axis=0); f = np.fft.rfftfreq(len(x), 1 / SR)
    m = np.ones_like(f)
    if hi: m *= 1 / (1 + (f / hi) ** 4)
    if lo: m *= 1 / (1 + (lo / np.maximum(f, 1)) ** 4)
    return np.fft.irfft(X * (m[:, None] if x.ndim == 2 else m), n=len(x), axis=0)

def note(m): return 440 * 2 ** ((m - 69) / 12)

# ---------- instruments ----------
def kick(hard=False):
    n = int(0.45 * SR); t = np.arange(n) / SR
    f = 45 + 160 * np.exp(-t / 0.035)
    s = osc(f, 0.45, d=0.22 if hard else 0.16) + noise(0.45, 0.004) * 0.25
    return np.tanh(s * (3.2 if hard else 1.8)) * 0.9

def clap():
    s = np.zeros(int(0.3 * SR))
    for k in range(3):
        b = fft_filter(noise(0.3, 0.012 if k < 2 else 0.09), lo=900, hi=6000)
        j = int(k * 0.011 * SR); s[j:] += b[: len(s) - j]
    return s * 0.7

def snare(): return fft_filter(noise(0.25, 0.07), lo=400) * 0.6 + osc(185, 0.25, d=0.05) * 0.5
def hat(open_=False): return fft_filter(noise(0.25 if open_ else 0.06, 0.07 if open_ else 0.014), lo=7000) * 0.5

def supersaw(m, dur, voices=7, spread=0.012, d=None):
    s = sum(osc(note(m) * (1 + spread * (v / (voices - 1) - 0.5)), dur, 'saw', d=d, a=0.01, phase=rng.uniform(0, 6))
            for v in range(voices))
    return s / voices

def lead(m, dur, vib=True):
    """Trot-flavoured lead: a little scoop up into the note (꺾기) and vibrato on long notes."""
    n = int(dur * SR); t = np.arange(n) / SR
    semis = -0.8 * np.exp(-t / 0.035)
    if vib and dur > 0.35: semis += 0.28 * np.sin(2 * np.pi * 6 * t) * np.minimum(1, t / 0.2)
    f = note(m) * 2 ** (semis / 12)
    s = osc(f, dur, 'square', a=0.006) * 0.45 + osc(f * 1.003, dur, 'saw', a=0.006) * 0.55
    return s * np.minimum(1, (dur - t) / 0.03).clip(0, 1)

# ---------- song data (A minor: Am - F - C - G) ----------
CH = [[57, 60, 64], [53, 57, 60], [55, 60, 64], [55, 59, 62]]
BASS = [33, 29, 36, 31]
HOOK = [  # (beat in bar, midi, length in beats) for 4 bars
    [(0, 69, .5), (.5, 72, .5), (1, 76, 1), (2, 74, .5), (2.5, 72, .5), (3, 74, 1)],
    [(0, 72, .5), (.5, 69, .5), (1, 72, 1), (2, 77, 1), (3, 76, 1)],
    [(0, 76, .5), (.5, 79, .5), (1, 76, 1), (2, 74, .5), (2.5, 72, .5), (3, 72, 1)],
    [(0, 71, 1), (1, 74, 1), (2, 79, 1.5), (3.5, 76, .5)],
]

def section(t):
    if t < 6.45: return 'groove'
    if t < 8.0: return 'crash'
    if t < 9.0: return 'rebound'
    if t < 11.15: return 'build'
    if t < DROP: return 'bridge'
    if t < FIN - 1e-6: return 'drop'
    return 'end'

pumpbus, chordbus = bus(), bus()
nbeats = int((DUR - GRID0) / BEAT) + 1
for b in range(nbeats):
    t = GRID0 + b * BEAT
    if t < -0.05 or t >= DUR: continue
    sec = section(t)
    bar, beat_in_bar = (b // 4) % 4, b % 4
    drop = sec == 'drop'
    if sec in ('groove', 'rebound', 'drop') or (sec == 'build' and t < 10.6):
        add(music, kick(hard=drop), t, 1.0 if drop else 0.8)
        add(music, hat(True), t + BEAT / 2, 0.5 if drop else 0.35, 0.25)
        if drop or sec == 'groove':
            add(music, hat(), t + BEAT / 4, 0.25, -0.3); add(music, hat(), t + 3 * BEAT / 4, 0.25, -0.3)
        if beat_in_bar in (1, 3):
            add(music, clap(), t, 0.8 if drop else 0.55, 0.05); add(verb_send, clap(), t, 0.3)
        # off-beat pumping bass (8ths) + sub on the drop
        for k in (0.5,) if not drop else (0.25, 0.5, 0.75):
            add(pumpbus, osc(note(BASS[bar] + 12), BEAT * 0.24, 'saw', d=0.09), t + k * BEAT, 0.5)
        if drop: add(pumpbus, osc(note(BASS[bar]), BEAT, 'sine', d=0.5), t, 0.9)
        # chord stabs / pads
        if drop:
            for m in CH[bar]: add(chordbus, supersaw(m + 12, BEAT * 0.9, d=0.35), t, 0.55)
        else:
            for m in CH[bar]: add(chordbus, supersaw(m + 12, BEAT * 0.3, voices=3, d=0.08), t + BEAT / 2, 0.35)
        # hook
        if sec in ('groove', 'drop', 'rebound'):
            for (bo, m, ln) in HOOK[bar]:
                if beat_in_bar <= bo < beat_in_bar + 1:
                    tt = t + (bo - beat_in_bar) * BEAT
                    add(music, lead(m + (12 if drop else 0), ln * BEAT * 0.95), tt, 0.16 if drop else 0.13, -0.1)
                    add(verb_send, lead(m, ln * BEAT * 0.95), tt, 0.08)
                    if drop: add(music, lead(m, ln * BEAT * 0.95), tt, 0.12, 0.15)
    if sec == 'build':
        # snare roll that speeds up: 8ths -> 16ths -> 32nds
        div = 2 if t < 9.9 else 4 if t < 10.6 else 8
        for k in range(div):
            tt = t + k * BEAT / div
            if tt < 11.15: add(music, snare(), tt, 0.25 + 0.5 * (tt - 9) / 2.15)
        add(chordbus, supersaw(CH[bar][0] + 12, BEAT * 0.4, voices=5, d=0.2), t, 0.3)

# sidechain pump: duck bass + chords right after every grid beat
tt = np.arange(N) / SR
phase = ((tt - GRID0) % BEAT)
pump = 1 - 0.85 * np.exp(-phase / 0.07)
pumpbus *= pump[:, None]; chordbus *= pump[:, None]
music += fft_filter(pumpbus, hi=1800) + fft_filter(chordbus, hi=7000)
verb_send += chordbus * 0.25

# tape-stop on the market crash (6.45s): the whole groove grinds to a halt
t0, td = 6.45, 0.45
i0, nd = int(t0 * SR), int(td * SR)
r = 1 - np.arange(nd) / nd
pos = i0 + np.cumsum(r)
for c in range(2):
    music[i0:i0 + nd, c] = np.interp(pos, np.arange(N), music[:, c]) * np.linspace(1, 0.2, nd)
music[i0 + nd:int(8.0 * SR)] = 0

# half-time sad groove 6.9-8.0 + womp womp
for k, t in enumerate(np.arange(6.95, 8.0, BEAT * 2)):
    add(half, kick(), t, 0.7)
    if k % 2: add(half, snare(), t, 0.3)
for t, m, d in [(6.95, 55, .35), (7.35, 54, .35), (7.75, 52, .6)]:
    n = int(d * SR); bend = note(m) * 2 ** (-np.linspace(0, 1, n) * 0.6 / 12)
    add(half, osc(bend, d, 'saw', d=0.4) * 0.5 + osc(bend * 0.5, d, 'square', d=0.4) * 0.3, t, 0.35)
music += half

# ---------- SFX ----------
def pop(f=900): n = int(0.1 * SR); return osc(f + 1100 * np.linspace(0, 1, n), 0.1, d=0.035)
def whoosh(dur=0.35, lo=300, hi=5000):
    s = fft_filter(noise(dur, 10), lo=lo, hi=hi); w = np.sin(np.linspace(0, np.pi, len(s))) ** 2
    return s * w * 0.8
def chime(fs, gap=0.08, d=0.4):
    out = np.zeros(int((gap * len(fs) + 1.2) * SR))
    for i, f in enumerate(fs):
        s = osc(f, 1.2, d=d) + osc(f * 2, 1.2, d=d / 2) * 0.3 + osc(f * 3.01, 1.2, d=d / 4) * 0.15
        j = int(i * gap * SR); out[j:j + len(s)] += s
    return out
def riser(t0, t1, f0, f1, gain):
    n = int((t1 - t0) * SR); k = np.linspace(0, 1, n)
    s = supersaw(0, t1 - t0, voices=5, spread=0.02) if False else sum(
        osc(f0 * (f1 / f0) ** k * (1 + 0.01 * v), t1 - t0, 'saw') for v in (-1, 0, 1)) / 3
    add(sfx, s * k ** 2, t0, gain)

for t in [0.15, 1.65, 3.15, 4.5, 6.6, 7.6, 9.4, 10.4]: add(sfx, pop(), t, 0.3); add(verb_send, pop(), t, 0.1)
for t in [0.7, 1.1]: add(sfx, osc(1320, 0.08, d=0.03), t, 0.2)
add(sfx, whoosh(0.4), 1.2, 0.6, 0.5)
add(sfx, chime([note(m) for m in [72, 76, 79, 84]], 0.05), 2.1, 0.2)
for i in range(3): add(sfx, whoosh(0.18, 800), 3.1 + i * 0.25, 0.45, -0.5)
add(sfx, chime([note(m) for m in [67, 71, 74]], 0.07), 4.45, 0.18)
for t in [2.82, 5.82, 8.82]: add(sfx, whoosh(0.36), t, 0.7)
add(sfx, osc(1800, 0.04, 'square', d=0.01), 6.25, 0.3)                      # buy click
add(sfx, kick(hard=True), 6.45, 0.6)                                         # crash impact
riser(8.0, 8.45, 180, 1400, 0.22)                                            # rebound sweep
add(sfx, chime([note(m) for m in [72, 76, 79, 84, 88]], 0.04), 8.45, 0.22)
add(sfx, fft_filter(noise(0.8, 0.3), lo=500, hi=6000), 8.45, 0.25)           # cheer burst
add(sfx, whoosh(0.3, 1000), 9.15, 0.6)                                       # card flip
add(sfx, kick(), 10.6, 0.5); add(sfx, fft_filter(noise(0.1, 0.03), lo=200), 10.6, 0.4)
riser(9.0, 11.15, 110, 1760, 0.18)                                           # build riser
add(sfx, whoosh(2.1, 2000, 12000) * np.linspace(0, 1, int(2.1 * SR)), 9.05, 0.6)
add(sfx, chime([note(88), note(84)], 0.22, d=0.5), 11.15, 0.45)              # ding-dong (Bali!)
add(verb_send, chime([note(88), note(84)], 0.22, d=0.5), 11.15, 0.3)
# bridge: reverse-cymbal swell + rising riser straight into the drop
n = int(0.5 * SR); add(sfx, fft_filter(noise(0.5, 10), lo=3000) * np.linspace(0, 1, n) ** 3, 11.45, 0.9)
riser(11.45, 11.95, 220, 2600, 0.25)
add(sfx, osc(note(33) * np.exp(-np.linspace(0, 1.5, int(1.2 * SR))), 1.2, d=0.6), DROP, 1.0)  # sub drop
add(sfx, fft_filter(noise(1.5, 0.6), lo=2500), DROP, 0.5)                    # crash cymbal
add(verb_send, fft_filter(noise(1.5, 0.6), lo=2500), DROP, 0.3)
# final unison hit
add(sfx, kick(hard=True), FIN, 1.0); add(sfx, fft_filter(noise(1.6, 0.7), lo=2500), FIN, 0.55)
for m in [57, 60, 64, 69, 72, 76]: add(sfx, supersaw(m, 0.69, d=0.25), FIN, 0.32)
for m in [57, 64, 69, 76]: add(verb_send, supersaw(m, 0.6, d=0.3), FIN, 0.3)
add(sfx, chime([note(m) for m in [81, 84, 88, 93]], 0.05, d=0.5), FIN + 0.05, 0.25)

# ---------- reverb (convolution with a decaying noise tail) ----------
ir_n = int(1.6 * SR)
ir = rng.standard_normal((ir_n, 2)) * np.exp(-np.arange(ir_n) / SR / 0.45)[:, None]
ir = fft_filter(ir, lo=200, hi=6000); ir /= np.sqrt((ir ** 2).sum(axis=0))
L = 1 << int(np.ceil(np.log2(N + ir_n)))
verb = np.fft.irfft(np.fft.rfft(verb_send, L, axis=0) * np.fft.rfft(ir, L, axis=0), L, axis=0)[:N]

mix = music * 0.9 + sfx * 0.8 + verb * 0.5
fade = int(0.35 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
mix /= np.percentile(np.abs(mix), 99.9)
mix = np.tanh(mix * 1.3) * 0.93                                              # soft limiter
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'audio.wav')
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(mix, -1, 1) * 32767).astype('<i2').tobytes())
print(out)
