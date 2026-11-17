/** How the tap sounds: a short, soft tick that falls in pitch. */
const TICK = {
  startHz: 1300,
  endHz: 650,
  seconds: 0.045,
  volume: 0.05,
} as const;

type AudioSessionNavigator = Navigator & { audioSession?: { type: string } };

let context: AudioContext | null = null;

function audio(): AudioContext | null {
  if (typeof AudioContext === "undefined") return null;
  if (!context) {
    // Safari: an "ambient" session stays quiet when the phone is on silent and does not stop
    // the person's music.
    const session = (navigator as AudioSessionNavigator).audioSession;
    if (session) session.type = "ambient";
    context = new AudioContext();
  }
  return context;
}

/** Plays the tap sound. Browsers only allow it after a tap or a key press, which is when it runs. */
export function playClick() {
  const ctx = audio();
  if (!ctx) return;
  if (ctx.state === "suspended") void ctx.resume();
  const now = ctx.currentTime;
  const tone = ctx.createOscillator();
  const level = ctx.createGain();
  tone.type = "triangle";
  tone.frequency.setValueAtTime(TICK.startHz, now);
  tone.frequency.exponentialRampToValueAtTime(TICK.endHz, now + TICK.seconds);
  level.gain.setValueAtTime(0.0001, now);
  level.gain.exponentialRampToValueAtTime(TICK.volume, now + 0.004);
  level.gain.exponentialRampToValueAtTime(0.0001, now + TICK.seconds);
  tone.connect(level).connect(ctx.destination);
  tone.start(now);
  tone.stop(now + TICK.seconds + 0.01);
}
