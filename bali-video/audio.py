"""Synthesize the 15s soundtrack (120 BPM beat + SFX synced to scene.html events)."""
import wave, os
import numpy as np

SR, DUR, BPM = 44100, 15.0, 120
BEAT = 60 / BPM
N = int(SR * DUR)
mix = np.zeros((N, 2))
rng = np.random.default_rng(7)

def add(sig, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= N: return
    sig = sig[: N - i] * gain
    mix[i:i + len(sig), 0] += sig * (1 - max(0, pan))
    mix[i:i + len(sig), 1] += sig * (1 + min(0, pan))

def env(n, a=0.005, d=None):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a)
    return e * (np.exp(-t / d) if d else 1)

def tone(f, dur, wave_='sine', d=None, a=0.005):
    n = int(dur * SR); t = np.arange(n) / SR
    f = np.broadcast_to(f, n) if np.ndim(f) else np.full(n, f)
    ph = 2 * np.pi * np.cumsum(f) / SR
    if wave_ == 'sine': s = np.sin(ph)
    elif wave_ == 'saw': s = 2 * ((ph / (2 * np.pi)) % 1) - 1
    elif wave_ == 'square': s = np.sign(np.sin(ph))
    else: s = np.abs(2 * ((ph / (2 * np.pi)) % 1) - 1) * 2 - 1
    return s * env(n, a, d)

def noise(dur, d=0.05, hp=True):
    n = int(dur * SR); s = rng.standard_normal(n)
    if hp: s = np.diff(s, prepend=0)
    return s * env(n, 0.001, d)

def kick(): n = int(0.3 * SR); f = 50 + 110 * np.exp(-np.arange(n) / SR / 0.04); return tone(f, 0.3, d=0.12)
def snare(): return noise(0.2, 0.06, hp=False) * 0.5 + tone(190, 0.2, d=0.05) * 0.4
def hat(): return noise(0.05, 0.015) * 0.4
def clap(): return sum(noise(0.15, 0.04, hp=False) * 0.4 for _ in range(1))
def note(m): return 440 * 2 ** ((m - 69) / 12)

def pluck(m, dur=0.4, g=0.25):
    return (tone(note(m), dur, 'saw', d=0.12) * 0.5 + tone(note(m) * 2, dur, 'tri', d=0.08) * 0.3) * g

# --- music ---
prog = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]  # C Am F G
bass = [36, 33, 29, 31]
for b in range(int(DUR / BEAT)):
    t = b * BEAT
    if t >= 14.25: break
    dance = t >= 12
    bar = (b // 4) % 4
    add(kick(), t, 0.9 if dance else 0.55)
    add(hat(), t + BEAT / 2, 0.5 if dance else 0.3, pan=0.3)
    if dance:
        add(hat(), t + BEAT / 4, 0.25, -0.3); add(hat(), t + 3 * BEAT / 4, 0.25, -0.3)
    if b % 2 == 1: add(clap() if dance else snare(), t, 0.6 if dance else 0.35)
    add(tone(note(bass[bar]), BEAT * 0.9, 'tri', d=0.25), t, 0.35 if dance else 0.25)
    add(tone(note(bass[bar] + 12), BEAT * 0.4, 'tri', d=0.08), t + BEAT / 2, 0.15 if dance else 0.08)
    # chord stabs on off-beats
    for m in prog[bar]:
        add(pluck(m + (12 if dance else 0), 0.3, 0.12 if dance else 0.08), t + BEAT / 2, pan=0.2)
    # melody hook in dance section
    if dance:
        mel = [72, 76, 79, 76, 74, 77, 81, 79][b % 8]
        add(tone(note(mel), BEAT * 0.45, 'square', d=0.15) * 0.08, t)

# --- sfx ---
def pop(f=900): n = int(0.12 * SR); return tone(f + 900 * np.linspace(0, 1, n), 0.12, d=0.04)
def whoosh(dur=0.35):
    s = noise(dur, 1, hp=False); n = len(s); w = np.sin(np.linspace(0, np.pi, n)) ** 2
    k = np.ones(30) / 30
    return np.convolve(s * w, k, 'same') * 0.6
def chime(fs, gap=0.08, d=0.4):
    out = np.zeros(int((gap * len(fs) + 1.0) * SR))
    for i, f in enumerate(fs):
        s = tone(f, 1.0, d=d) + tone(f * 2, 1.0, d=d / 2) * 0.3
        j = int(i * gap * SR); out[j:j + len(s)] += s
    return out

for t in [0.15, 1.65, 3.15, 4.5, 6.6, 7.6, 9.4, 10.4]: add(pop(), t, 0.25)
for t in [0.7, 1.1]: add(tone(1320, 0.08, d=0.03), t, 0.15)
for t, p in [(0.3, -0.4), (0.55, 0.4), (0.8, -0.4), (1.05, 0.4), (1.3, -0.4), (1.55, 0.4)]: add(kick() * 0.5, t, 0.25, p)  # foot stomps
add(whoosh(0.4), 1.2, 0.5, 0.5)
add(chime([note(m) for m in [72, 76, 79, 84]], 0.06), 2.1, 0.18)
for i in range(3): add(whoosh(0.2), 3.1 + i * 0.25, 0.35, -0.5)
add(chime([note(m) for m in [67, 71, 74]], 0.08), 4.45, 0.15)
for t in [2.82, 5.82, 8.82]: add(whoosh(0.36), t, 0.6)
add(tone(1800, 0.05, 'square', d=0.01), 6.25, 0.25)  # click
n = int(0.6 * SR); add(tone(880 * np.exp(-np.linspace(0, 2.2, n)), 0.6, 'saw', d=0.5), 6.45, 0.18)  # crash slide
add(kick(), 7.0, 0.7)
add(tone(np.full(int(0.25 * SR), note(55)), 0.25, 'square', d=0.1), 6.6, 0.08)
add(tone(np.full(int(0.4 * SR), note(52)), 0.4, 'square', d=0.2), 6.85, 0.08)  # womp womp
n = int(0.6 * SR); add(tone(220 * np.exp(np.linspace(0, 1.6, n)), 0.6, 'tri', d=0.6), 8.0, 0.18)  # rise
add(chime([note(m) for m in [72, 76, 79, 84, 88]], 0.05), 8.45, 0.2)
add(noise(0.6, 0.25, hp=False) * 0.3, 8.45, 0.25)  # cheer burst
add(whoosh(0.3), 9.15, 0.5)
add(kick(), 10.6, 0.5); add(noise(0.1, 0.03, hp=False) * 0.4, 10.6, 0.5)  # stamp
add(chime([note(88), note(84)], 0.22, d=0.5), 11.15, 0.35)  # ding-dong
add(chime([note(88), note(84)], 0.22, d=0.5), 11.6, 0.2)
add(chime([note(m) for m in range(72, 97, 2)], 0.025, d=0.3), 11.85, 0.18)  # sparkle glissando
add(whoosh(0.5), 11.8, 0.4)
# final unison hit
add(kick(), 14.25, 1.0); add(noise(1.2, 0.5) * 0.5, 14.25, 0.5)
for m in [60, 64, 67, 72, 76]: add(tone(note(m), 0.75, 'saw', d=0.3) * 0.2, 14.25, 0.6)
add(chime([note(m) for m in [84, 88, 91, 96]], 0.05, d=0.5), 14.3, 0.2)

# fade, normalize, write
fade = int(0.25 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.4) * 0.89
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out', 'audio.wav')
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
print(out)
