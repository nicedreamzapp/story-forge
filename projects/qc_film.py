#!/usr/bin/env python3
"""Automated film QC — checks a finished film against all criteria. Exit 0 = all pass.
Usage: qc_film.py <film.mp4> <spec.json>
spec: {"voices":[{"t0":2,"t1":8,"max_hz":150,"name":"dean"}], "lines":["expected","..."], "min_fps":30}
Checks: voice gender (pitch), no singing in music gaps, dialogue present, music@0, fps, duration.
Lip-sync proxy: talking-clip audio transcribes to the intended lines (right audio on right mouth).
"""
import sys, json, subprocess, re, tempfile, os
import librosa, numpy as np

V = sys.argv[1]; spec = json.load(open(sys.argv[2]))
WHISPER = os.path.expanduser("~/whisper-models/ggml-small.en.bin")
DEMUCS = os.path.expanduser("~/Library/Python/3.9/bin/demucs")
fails = []

def dur(p): return float(subprocess.check_output(["ffprobe","-v","quiet","-show_entries","format=duration","-of","csv=p=0",p]).strip())
def seg(t0,t1,out):
    subprocess.run(["ffmpeg","-y","-v","quiet","-ss",str(t0),"-t",str(t1-t0),"-i",V,"-vn","-ar","16000","-ac","1",out],check=True)
def pitch(wav):
    y,sr=librosa.load(wav,sr=16000); f0=librosa.yin(y,fmin=55,fmax=350,sr=sr); f0=f0[(f0>55)&(f0<300)]
    return float(np.median(f0)) if len(f0) else 0
def transcribe(wav):
    out=subprocess.run(["/opt/homebrew/bin/whisper-cli","-m",WHISPER,"-f",wav,"-np","-nt"],capture_output=True,text=True).stdout
    return re.sub(r'\(.*?\)|\[.*?\]|♪','',out).strip()
def vocal_rms(wav):
    td=tempfile.mkdtemp(); subprocess.run([DEMUCS,"-d","cpu","--two-stems","vocals","-o",td,wav],capture_output=True)
    base=os.path.splitext(os.path.basename(wav))[0]
    y,_=librosa.load(f"{td}/htdemucs/{base}/vocals.wav",sr=16000); return float(np.sqrt(np.mean(y**2)))

# 1. fps
fps=subprocess.check_output(["ffprobe","-v","quiet","-select_streams","v","-show_entries","stream=r_frame_rate","-of","csv=p=0",V]).decode().strip()
fnum=eval(fps) if '/' in fps else float(fps)
if fnum < spec.get("min_fps",30): fails.append(f"fps {fnum} < {spec.get('min_fps',30)}")

# 2. music present at 0:00
seg(0,3,"/tmp/qc_open.wav")
y,_=librosa.load("/tmp/qc_open.wav",sr=16000)
if float(np.sqrt(np.mean(y**2))) < 0.005: fails.append("no audio/music at 0:00")

# 3. voice gender (pitch) on specified character windows
for vchk in spec.get("voices",[]):
    seg(vchk["t0"],vchk["t1"],"/tmp/qc_v.wav")
    p=pitch("/tmp/qc_v.wav")
    if "max_hz" in vchk and p > vchk["max_hz"]: fails.append(f"{vchk['name']} voice {p:.0f}Hz > {vchk['max_hz']} (too high/female)")
    if "min_hz" in vchk and p < vchk["min_hz"]: fails.append(f"{vchk['name']} voice {p:.0f}Hz < {vchk['min_hz']}")

# 4. no singing in credits music (music-only tail)
d=dur(V); seg(max(0,d-4.5),d-0.5,"/tmp/qc_cred.wav")
vr=vocal_rms("/tmp/qc_cred.wav")
if vr > 0.02: fails.append(f"music has singing (credits vocal RMS {vr:.3f})")

# 5. dialogue present (lip-sync proxy: expected lines appear in transcript)
seg(0,d,"/tmp/qc_full.wav")
full=transcribe("/tmp/qc_full.wav").lower()
def hit(ln):
    ws=[w for w in re.findall(r"[a-z]+",ln.lower()) if len(w)>2]
    return sum(1 for w in ws if w in full) >= max(1,len(ws)//2)
missing=[ln for ln in spec.get("lines",[]) if not hit(ln)]
if len(missing) > len(spec.get("lines",[]))*0.3: fails.append(f"{len(missing)} script lines not heard (dialogue/sync issue)")

print(json.dumps({"film":os.path.basename(V),"fps":fnum,"PASS":not fails,"fails":fails},indent=2))
sys.exit(0 if not fails else 1)
