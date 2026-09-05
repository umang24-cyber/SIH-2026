// Web Audio API procedural sound synthesizer for authentic VT100 / mechanical clicks & retro arcade beeps

class SoundEngine {
  private ctx: AudioContext | null = null;
  private enabled: boolean = true;
  private currentThemeStop: (() => void) | null = null;

  constructor() {
    // AudioContext initialized on user interaction
  }

  public initCtx() {
    if (!this.ctx && typeof window !== 'undefined') {
      const AudioCtxClass = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioCtxClass) {
        this.ctx = new AudioCtxClass();
      }
    }
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume().catch(() => {});
    }
    return this.ctx;
  }

  public isEnabled(): boolean {
    return this.enabled;
  }

  public setEnabled(value: boolean) {
    this.enabled = value;
  }

  public playKeyClick() {
    if (!this.enabled) return;
    try {
      this.initCtx();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'triangle';
      osc.frequency.setValueAtTime(1400 + Math.random() * 400, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(300, this.ctx.currentTime + 0.02);

      gain.gain.setValueAtTime(0.04, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.02);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + 0.025);
    } catch {}
  }

  public playEnterSuccess() {
    if (!this.enabled) return;
    try {
      this.initCtx();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'square';
      osc.frequency.setValueAtTime(880, this.ctx.currentTime);
      osc.frequency.setValueAtTime(1320, this.ctx.currentTime + 0.04);

      gain.gain.setValueAtTime(0.05, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.1);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + 0.1);
    } catch {}
  }

  public playErrorChirp() {
    if (!this.enabled) return;
    try {
      this.initCtx();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(220, this.ctx.currentTime);
      osc.frequency.setValueAtTime(160, this.ctx.currentTime + 0.06);

      gain.gain.setValueAtTime(0.06, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + 0.15);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + 0.15);
    } catch {}
  }

  // Iconic Pac-Man Waka-Waka eating sound
  public playPacmanChomp(step: number = 0) {
    if (!this.enabled) return;
    try {
      this.initCtx();
      if (!this.ctx) return;

      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'triangle';
      const isUp = step % 2 === 0;
      const startFreq = isUp ? 280 : 540;
      const endFreq = isUp ? 540 : 280;

      osc.frequency.setValueAtTime(startFreq, this.ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(endFreq, this.ctx.currentTime + 0.07);

      gain.gain.setValueAtTime(0.22, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.005, this.ctx.currentTime + 0.075);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start();
      osc.stop(this.ctx.currentTime + 0.08);
    } catch {}
  }

  // Authentic 1980 Pac-Man Startup Intro Theme
  public playPacmanIntro(): () => void {
    if (!this.enabled) return () => {};
    try {
      this.initCtx();
      if (!this.ctx) return () => {};

      this.stopPacmanIntro();

      const notes: { f: number; d: number }[] = [
        { f: 493.88, d: 0.12 }, // B4
        { f: 987.77, d: 0.12 }, // B5
        { f: 739.99, d: 0.12 }, // F#5
        { f: 622.25, d: 0.12 }, // D#5
        { f: 987.77, d: 0.12 }, // B5
        { f: 739.99, d: 0.12 }, // F#5
        { f: 622.25, d: 0.22 }, // D#5

        { f: 523.25, d: 0.12 }, // C5
        { f: 1046.50, d: 0.12 }, // C6
        { f: 783.99, d: 0.12 }, // G5
        { f: 659.25, d: 0.12 }, // E5
        { f: 1046.50, d: 0.12 }, // C6
        { f: 783.99, d: 0.12 }, // G5
        { f: 659.25, d: 0.22 }, // E5

        { f: 493.88, d: 0.12 }, // B4
        { f: 987.77, d: 0.12 }, // B5
        { f: 739.99, d: 0.12 }, // F#5
        { f: 622.25, d: 0.12 }, // D#5
        { f: 987.77, d: 0.12 }, // B5
        { f: 739.99, d: 0.12 }, // F#5
        { f: 622.25, d: 0.22 }, // D#5

        { f: 622.25, d: 0.08 }, // D#5
        { f: 659.25, d: 0.08 }, // E5
        { f: 698.46, d: 0.08 }, // F5
        { f: 698.46, d: 0.08 }, // F5
        { f: 739.99, d: 0.08 }, // F#5
        { f: 783.99, d: 0.08 }, // G5
        { f: 830.61, d: 0.08 }, // G#5
        { f: 880.00, d: 0.08 }, // A5
        { f: 987.77, d: 0.35 }  // B5 (finale)
      ];

      const startTime = this.ctx.currentTime + 0.05;
      let currTime = startTime;
      const oscillators: OscillatorNode[] = [];

      notes.forEach(n => {
        if (!this.ctx) return;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        // Authentic vintage Namco pulse tone
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(n.f, currTime);

        gain.gain.setValueAtTime(0.24, currTime);
        gain.gain.exponentialRampToValueAtTime(0.005, currTime + n.d - 0.008);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(currTime);
        osc.stop(currTime + n.d);
        oscillators.push(osc);

        currTime += n.d;
      });

      const stopFn = () => {
        oscillators.forEach(o => {
          try {
            o.stop();
            o.disconnect();
          } catch {}
        });
      };

      this.currentThemeStop = stopFn;
      return stopFn;
    } catch {
      return () => {};
    }
  }

  public stopPacmanIntro() {
    if (this.currentThemeStop) {
      this.currentThemeStop();
      this.currentThemeStop = null;
    }
  }
}

export const sound = new SoundEngine();
