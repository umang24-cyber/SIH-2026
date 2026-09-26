import { useEffect, useLayoutEffect, useSyncExternalStore } from 'react';
import { Volume2, VolumeX } from 'lucide-react';
import { publicAudio } from './publicAudio';
import './publicAudio.css';

export function PublicAudioControls({ active }: { active: boolean }) {
  const state = useSyncExternalStore(publicAudio.subscribe, publicAudio.getSnapshot);
  useLayoutEffect(() => { publicAudio.setRoute(active); }, [active]);
  useEffect(() => {
    const visibility = () => publicAudio.setHidden(document.hidden);
    visibility(); document.addEventListener('visibilitychange', visibility);
    return () => document.removeEventListener('visibilitychange', visibility);
  }, []);
  if (!active) return null;
  return <div className="editorial public-audio" aria-label="Public page audio" data-music-state={state.music} data-active-sequences={state.sequences}>
    <button type="button" aria-label={!state.unlocked ? 'Enable sound and music' : state.enabled ? 'Mute sound and music' : 'Unmute sound and music'} aria-pressed={state.enabled && state.unlocked} onClick={() => state.unlocked ? publicAudio.setEnabled(!state.enabled) : publicAudio.setEnabled(true)}>{state.enabled && state.unlocked ? <Volume2 size={14} /> : <VolumeX size={14} />}<span>{!state.unlocked ? 'Sound on' : state.enabled ? 'Sound' : 'Muted'}</span></button>
    <label><span className="sr-only">Public audio volume</span><input aria-label="Public audio volume" type="range" min="0" max="100" value={Math.round(state.volume * 100)} onChange={event => { publicAudio.unlock(); publicAudio.setVolume(Number(event.target.value) / 100); }} /></label>
    {state.music === 'unavailable' && <span className="public-audio-note">Music unavailable</span>}
  </div>;
}
