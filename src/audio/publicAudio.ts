import { sound } from './soundEngine';

export type PublicCue = 'depart' | 'pour' | 'glass' | 'flip' | 'ding' | 'leaf' | 'book' | 'delivery' | 'unroll' | 'chart' | 'reveal';
export type AudioCue = { at: number; type: PublicCue; duration?: number };
type Snapshot = { enabled: boolean; volume: number; unlocked: boolean; music: 'locked' | 'paused' | 'playing' | 'unavailable'; sequences: number; publicRoute: boolean };
const storedVolume = () => { try { const raw = localStorage.getItem('bitkaun-public-volume'); return raw === null ? .35 : Math.max(0, Math.min(1, Number(raw) || 0)); } catch { return .35; } };
const storedEnabled = () => { try { return localStorage.getItem('bitkaun-public-sound') !== 'off'; } catch { return true; } };

/** One public-page mixer. Sequence leases prevent overlapping reveals from resuming music early. */
class PublicAudio {
  private snapshot: Snapshot = { enabled: storedEnabled(), volume: storedVolume(), unlocked: false, music: 'locked', sequences: 0, publicRoute: false };
  private listeners = new Set<() => void>();
  private ctx: AudioContext | null = null;
  private effects: GainNode | null = null;
  private musicGain: GainNode | null = null;
  private music: HTMLAudioElement | null = null;
  private leases = new Set<symbol>();
  private stops = new Set<() => void>();
  private fadeTimer = 0;
  private revision = 0;
  private hidden = false;
  private lastChart = -Infinity;
  subscribe = (listener: () => void) => { this.listeners.add(listener); return () => { this.listeners.delete(listener); }; };
  getSnapshot = () => this.snapshot;
  private update(values: Partial<Snapshot>) { this.snapshot = { ...this.snapshot, ...values }; this.listeners.forEach(listener => listener()); }

  unlock = () => {
    try {
      if (!this.ctx) {
        this.ctx = sound.initCtx();
        if (!this.ctx) return;
        this.effects = this.ctx.createGain(); this.effects.connect(this.ctx.destination);
        this.musicGain = this.ctx.createGain(); this.musicGain.gain.value = 0; this.musicGain.connect(this.ctx.destination);
        this.music = new Audio('/audio/lounge.mp3');
        this.music.loop = true; this.music.preload = 'none';
        this.ctx.createMediaElementSource(this.music).connect(this.musicGain);
        this.music.addEventListener('error', () => this.update({ music: 'unavailable' }));
      }
      void this.ctx.resume().then(() => this.syncMusic()).catch(() => {});
      this.update({ unlocked: true }); this.syncEffects(); this.syncMusic();
    } catch { this.update({ music: 'unavailable' }); }
  };
  setRoute(active: boolean) {
    if (active === this.snapshot.publicRoute) return;
    this.update({ publicRoute: active });
    if (!active) this.stopEffects();
    this.syncMusic(!active); this.syncEffects();
  }
  setHidden(hidden: boolean) {
    this.hidden = hidden;
    if (hidden) this.stopEffects();
    this.syncMusic(hidden); this.syncEffects();
  }
  setEnabled = (enabled: boolean) => {
    this.update({ enabled });
    try { localStorage.setItem('bitkaun-public-sound', enabled ? 'on' : 'off'); } catch { /* Private browsing. */ }
    if (enabled) this.unlock(); else this.stopEffects();
    this.syncEffects(); this.syncMusic(!enabled);
  };
  setVolume = (volume: number) => {
    const value = Math.max(0, Math.min(1, volume));
    this.update({ volume: value });
    try { localStorage.setItem('bitkaun-public-volume', String(value)); } catch { /* Private browsing. */ }
    this.syncEffects(); this.syncMusic();
  };
  private syncEffects() {
    if (!this.effects || !this.ctx) return;
    this.effects.gain.setTargetAtTime(this.snapshot.enabled && this.snapshot.publicRoute && !this.hidden ? this.snapshot.volume : 0, this.ctx.currentTime, .025);
  }
  private wanted() { return this.snapshot.enabled && this.snapshot.unlocked && this.snapshot.publicRoute && !this.hidden && !this.leases.size && this.snapshot.volume > 0; }
  private syncMusic(immediate = false) {
    if (!this.music || !this.musicGain || !this.ctx) return;
    const generation = ++this.revision;
    clearTimeout(this.fadeTimer);
    const gain = this.musicGain.gain, now = this.ctx.currentTime;
    gain.cancelScheduledValues(now); gain.setValueAtTime(gain.value, now);
    if (!this.wanted()) {
      gain.linearRampToValueAtTime(0, now + (immediate ? .025 : .16));
      const pause = () => { if (generation !== this.revision) return; this.music?.pause(); if (this.snapshot.music !== 'unavailable') this.update({ music: 'paused' }); };
      if (immediate) pause(); else this.fadeTimer = window.setTimeout(pause, 175);
      return;
    }
    void this.music.play().then(() => {
      if (generation !== this.revision || !this.wanted()) return;
      gain.cancelScheduledValues(this.ctx!.currentTime);
      gain.setValueAtTime(gain.value, this.ctx!.currentTime);
      gain.linearRampToValueAtTime(this.snapshot.volume * .42, this.ctx!.currentTime + .8);
      this.update({ music: 'playing' });
    }).catch(() => { if (generation === this.revision) this.update({ music: this.music?.error ? 'unavailable' : 'paused' }); });
  }
  hold(name: string) {
    const token = Symbol(name); this.leases.add(token);
    this.update({ sequences: this.leases.size }); this.syncMusic();
    let released = false;
    return () => { if (released) return; released = true; this.leases.delete(token); this.update({ sequences: this.leases.size }); this.syncMusic(); };
  }
  private stopEffects() { [...this.stops].forEach(stop => stop()); }

  sequence(name: string, cues: AudioCue[], duration: number): () => void {
    const release = this.hold(name);
    const sources: AudioScheduledSourceNode[] = [];
    const nodes: AudioNode[] = [];
    let stopped = false;
    const ctx = this.ctx;
    const audible = ctx && this.effects && this.snapshot.unlocked && this.snapshot.enabled && this.snapshot.publicRoute && !this.hidden;
    const chart = name === 'chart';
    const allowCues = !chart || performance.now() - this.lastChart > 220;
    if (chart && allowCues) this.lastChart = performance.now();
    if (audible && allowCues) {
      const origin = ctx.currentTime + .035;
      const tone = (at: number, frequency: number, length: number, volume: number, end = frequency, type: OscillatorType = 'sine') => {
        const oscillator = ctx.createOscillator(), gain = ctx.createGain();
        oscillator.type = type; oscillator.frequency.setValueAtTime(frequency, at); oscillator.frequency.exponentialRampToValueAtTime(Math.max(30, end), at + length);
        gain.gain.setValueAtTime(0, at); gain.gain.linearRampToValueAtTime(volume, at + .006); gain.gain.exponentialRampToValueAtTime(.0001, at + length);
        oscillator.connect(gain); gain.connect(this.effects!); oscillator.start(at); oscillator.stop(at + length + .01);
        sources.push(oscillator); nodes.push(oscillator, gain);
      };
      const noise = (at: number, length: number, frequency: number, volume: number, end = frequency, q = .8) => {
        const buffer = ctx.createBuffer(1, Math.ceil(ctx.sampleRate * length), ctx.sampleRate);
        const data = buffer.getChannelData(0);
        let brown = 0;
        for (let i = 0; i < data.length; i++) { brown = (brown + (Math.random() * 2 - 1) * .04) / 1.04; data[i] = brown * 3 + (Math.random() * 2 - 1) * .18; }
        const source = ctx.createBufferSource(), filter = ctx.createBiquadFilter(), gain = ctx.createGain();
        source.buffer = buffer; filter.type = 'bandpass'; filter.Q.value = q;
        filter.frequency.setValueAtTime(frequency, at); filter.frequency.exponentialRampToValueAtTime(end, at + length);
        gain.gain.setValueAtTime(0, at); gain.gain.linearRampToValueAtTime(volume, at + Math.min(.08, length / 4)); gain.gain.exponentialRampToValueAtTime(.0001, at + length);
        source.connect(filter); filter.connect(gain); gain.connect(this.effects!); source.start(at); source.stop(at + length);
        sources.push(source); nodes.push(source, filter, gain);
      };
      cues.forEach(cue => {
        const at = origin + cue.at / 1000;
        switch (cue.type) {
          case 'pour': {
            const length = (cue.duration || 1700) / 1000;
            noise(at, length, 850, .7, 1800, 1.2);
            for (let i = 0; i < length * 13; i++) tone(at + i / 13, 330 + (i % 7) * 63, .055, .025, 160);
            break;
          }
          case 'glass': tone(at, 1450, .65, .13); tone(at, 2260, .4, .035); break;
          case 'flip': noise(at, .13, 3400, .3, 1200); [0, .12, .29, .52].forEach((offset, i) => tone(at + offset, 2400 - i * 160, .09, .10 / (i + 1), 1800)); break;
          case 'ding': tone(at, 1760, .7, .16); tone(at, 2640, .5, .045); tone(at, 3520, .25, .015); break;
          case 'leaf': noise(at, .24, 1600, .3, 4800); tone(at, 320, .075, .07, 120); break;
          case 'book': noise(at, .72, 1100, .65, 3500); noise(at + .38, .4, 2800, .25, 700); break;
          case 'delivery': noise(at, .55, 420, .45, 2400); tone(at + .52, 110, .18, .2, 45); noise(at + .54, .24, 650, .55, 240); break;
          case 'unroll': noise(at, 1.08, 800, .45, 3200); noise(at + .7, .35, 2100, .22, 450); break;
          case 'chart': noise(at, .36, 1800, .09, 3600); break;
          case 'reveal': tone(at, 660, .38, .07); tone(at + .06, 990, .4, .035); break;
          case 'depart': noise(at, .45, 450, .3, 1600); break;
        }
      });
    }
    const stop = () => {
      if (stopped) return; stopped = true; clearTimeout(timer);
      sources.forEach(source => { try { source.stop(); } catch { /* Already ended. */ } });
      nodes.forEach(node => node.disconnect()); this.stops.delete(stop); release();
    };
    const timer = window.setTimeout(stop, duration + 80);
    this.stops.add(stop);
    return stop;
  }
}

export const publicAudio = new PublicAudio();
