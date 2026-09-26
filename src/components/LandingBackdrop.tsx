import React from 'react';
import { useLandingMotion } from './useLandingMotion';
import type { ArtworkId } from './useLandingMotion';
import { useLandingEntrance } from './useLandingEntrance';
import './LandingBackdrop.css';

// Keep the rim, bowl, stem, and foot on one axis regardless of row width.
function centerAsciiRows(artwork: string): string {
  const rows = artwork.trim().split('\n').map(row => row.trim());
  const width = Math.max(...rows.map(row => row.length));
  return rows.map(row => ' '.repeat(Math.floor((width - row.length) / 2)) + row).join('\n');
}

const WINE_GLASS = centerAsciiRows(String.raw`
                .-----------------------.
           .--''    . . . . . . . . .    ''--.
        .-'    .--''''---------------''''--.    '-.
       /    .-'                             '-.    \
      ;    /     .---------------------.      \    ;
      |    '----'-----------------------'----'    |
      |  :                                     :  |
      |  :  .                               .  :  |
      |  :  :                               :  :  |
      |  :  :                               :  :  |
      |  :  :                               :  :  |
      |  :  :                               :  :  |
      |  :  :                               :  :  |
      |  :  :       . . . . . . . .         :  :  |
      |  :  .   .-~~~~~~~~~~~~~~~~~~~-.     .  :  |
      |  .   .-'  . . . . . . . . . .  '-.    .  |
      |   .-' .:::::::::::::::::::::::::. '-.   |
      |  ( .:::::::-----------------:::::::. )  |
      |   '-.:::::...................:::::.-'   |
      |  :   '---:::::::::::::::::::::---'   :  |
      |  :.  .::::::;;;;;;;;;;;;;::::::.    .:  |
      |  ::  .::::;;;;;;;;;;;;;;;;;::::.   ::  |
       \  :.  .:::;;;;;;;;;;;;;;;;;:::.   .:  /
        \  :.  .:::;;;;;;;;;;;;;;;:::.   .:  /
         \  :.  .:::;;;;;;;;;;;;;:::.   .:  /
          \  :.  .:::;;;;;;;;;;;:::.  .:  /
           \  '.  .:::;;;;;;;;;:::. .'  /
            '.  '.  .:::;;;:::.  .'  .'
              '.  '-.  .:.  .-'  .'
                '-.  '-----'  .-'
                   '--.   .--'
                       |: |
                       |: |
                       |: |
                       |: |
                       |: |
                       |: |
                       |: |
                       |: |
                       |: |
                       |: |
                       |: |
                       |: |
                      /:  \
                 _.-'':    ''-._
            _.-''   .::    ::.   ''-._
         .-'    ..:::        :::..    '-.
        (  ...:::::..........:::::...   )
         '-._______________________.-'
             '-----------------'
`);

const BITCOIN = String.raw`
                  _..------------.._
             _.-'' .:============:. ''-._
          .-' .:=='   . . . . . .  '==:. '-.
        .' .:=='  .-'------------'-.  '==:. '.
       / .:==' .-'                  '-. '==:. \
      / :==' .'       ||   ||          '. '==: \
     ; :==: /         ||   ||            \ :==: ;
     | :==: |     +===++===++====+.      | :==: |
     | :==: |     |###############\      | :==: |
     | :==: |     +===###====+######\     | :==: |
     | :==: |         ###    \######|    | :==: |
     | :==: |         ###    /######/    | :==: |
     | :==: |         ############+'     | :==: |
     | :==: |         ############+.     | :==: |
     | :==: |         ###    \#######\    | :==: |
     | :==: |         ###     |######|   | :==: |
     | :==: |         ###    /#######/    | :==: |
     | :==: |     +===###====+######/     | :==: |
     | :==: |     |###############'      | :==: |
     | :==: |     +===++===++====+'      | :==: |
     ; :==: \         ||   ||            / :==: ;
      \ :==: '.       ||   ||          .' :==: /
       \ ':==: '-.                  .-' :==:' /
        '. ':==:. '----------------' .:==:' .'
          '-. ':===.  . . . . . . .===:' .-'
             '-._ '':============:'' _.-'
                 ''--............--''
`.replace(/^\n/, '').trimEnd();

// A deterministic Barnsley fern: thousands of plotted points become actual
// ASCII cells, preserving the fine, self-similar leaflets without an image.
function createFern(): string {
  const width = 112;
  const height = 100;
  const cells = new Uint16Array(width * height);
  let seed = 146;
  let x = 0;
  let y = 0;

  for (let point = 0; point < 60000; point++) {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    const chance = seed / 4294967296;
    const previousX = x;

    if (chance < 0.01) {
      x = 0;
      y = 0.16 * y;
    } else if (chance < 0.86) {
      x = 0.85 * x + 0.04 * y;
      y = -0.04 * previousX + 0.85 * y + 1.6;
    } else if (chance < 0.93) {
      x = 0.2 * x - 0.26 * y;
      y = 0.23 * previousX + 0.22 * y + 1.6;
    } else {
      x = -0.15 * x + 0.28 * y;
      y = 0.26 * previousX + 0.24 * y + 0.44;
    }

    if (point < 30) continue;
    const column = Math.round((x + 2.2) / 4.9 * (width - 1));
    const row = Math.round((1 - y / 10.1) * (height - 1));
    if (column >= 0 && column < width && row >= 0 && row < height) {
      cells[row * width + column]++;
    }
  }

  const shades = ' .,:;=+*#@';
  return Array.from({ length: height }, (_, row) =>
    Array.from({ length: width }, (_, column) => {
      const density = cells[row * width + column];
      return shades[Math.min(shades.length - 1, Math.ceil(Math.sqrt(density)))];
    }).join('')
  ).join('\n');
}

const FERN = createFern();

const GLASS_ROWS = WINE_GLASS.split('\n');
// The bowl interior narrows with the outline. Wine is only ever drawn inside it.
const LIQUID_MASK = GLASS_ROWS.map((row, index) => {
  if (index < 6 || index > 28) return { start: 0, end: 0 };
  return { start: row.search(/\S/) + 5, end: row.trimEnd().length - 5 };
});
const EMPTY_GLASS = GLASS_ROWS.map((row, index) => {
  const { start, end } = LIQUID_MASK[index];
  return end > start ? row.slice(0, start) + ' '.repeat(end - start) + row.slice(end) : row;
}).join('\n');
const FERN_BANDS = Array.from({ length: 20 }, (_, index) => FERN.split('\n').slice(index * 5, index * 5 + 5).join('\n'));

interface AsciiArtworkProps {
  artwork: string;
  className: string;
  material: 'leaf' | 'glass' | 'coin';
}

function AsciiArtwork({ artwork, className, material }: AsciiArtworkProps) {
  const rows = artwork.split('\n');

  return (
    <pre className={`landing-art-text ${className}`} aria-hidden="true">
      {rows.map((row, rowIndex) => {
        const start = row.search(/\S/);
        const end = row.trimEnd().length;
        const silhouette = start < 0 ? '' : row.slice(start, end);
        const isSolid = material === 'coin' || (material === 'glass' && rowIndex >= 14);
        const isGlassPane = material === 'glass' && rowIndex >= 6 && rowIndex < 14;

        return (
          <React.Fragment key={rowIndex}>
            {start < 0 ? row : (
              <>
                {row.slice(0, start)}
                {isSolid || isGlassPane ? (
                  <span className={isGlassPane ? 'landing-art-pane' : 'landing-art-solid'}>
                    {silhouette}
                  </span>
                ) : (
                  // Only the actual leaf/rim cells are opaque; gaps between
                  // leaflets and the empty glass remain see-through.
                  silhouette.split(/(\s+)/).map((run, runIndex) => (
                    /\S/.test(run) ? <span className="landing-art-solid" key={runIndex}>{run}</span> : run
                  ))
                )}
                {row.slice(end)}
              </>
            )}
            {rowIndex < rows.length - 1 ? '\n' : null}
          </React.Fragment>
        );
      })}
    </pre>
  );
}

// Fixed positions avoid re-randomizing the condensation during logo typing.
const DEW_DROPS = [
  [63, 12, 11], [71, 19, 6], [87, 10, 17], [94, 28, 8],
  [77, 33, 22], [83, 38, 5], [67, 43, 9], [92, 49, 15],
  [73, 57, 7], [86, 63, 24], [96, 70, 6], [64, 73, 13],
  [79, 81, 10], [89, 88, 7], [57, 91, 18], [48, 16, 5],
  [54, 61, 6], [98, 16, 4], [81, 24, 4], [90, 65, 5],
];

const BOTTLE = String.raw`       .------.
       |======|
       |======|
       |      |
       |      |
       |      |
      /        \
     /          \
    /            \
   /              \
  |   .--------.   |
  |  /          \  |
  | |     B?     | |
  | |            | |
  | |  RÉSERVE   | |
  | |            | |
  | |    2026    | |
  |  \          /  |
  |   '--------'   |
  |                |
  |                |
  |                |
  |                |
  |                |
  |                |
  |________________|
  '----------------'`;
const noop = () => {};

export const LandingBackdrop = React.memo(function LandingBackdrop({ isExiting = false, introActive = false, introRunning = false, onReveal = noop, onIntroComplete = noop }: { isExiting?: boolean; introActive?: boolean; introRunning?: boolean; onReveal?: () => void; onIntroComplete?: () => void }) {
  const motion = useLandingMotion(isExiting, LIQUID_MASK, introActive);
  const entrance = useLandingEntrance(introRunning, motion.sceneRef, motion.setIntroFrame, onReveal, onIntroComplete);
  const control = (id: ArtworkId, label: string, hint: string) => (
    <>
      <button
        type="button"
        className={`landing-art-handle landing-art-handle-${id}`}
        aria-label={label}
        aria-describedby="landing-art-instructions"
        disabled={isExiting || introActive}
        {...motion.bind(id)}
      />
      <span className="landing-art-hint" aria-hidden="true">{hint}</span>
    </>
  );

  return (
    <>
      {introRunning && <><pre ref={entrance.bottleRef} className="landing-intro-bottle" aria-hidden="true">{BOTTLE}</pre><svg ref={entrance.streamRef} className="landing-pour-stream" aria-hidden="true"><path fill="none" stroke="#722f42" strokeWidth="4" strokeLinecap="round" /><ellipse rx="10" ry="3" fill="none" stroke="#722f42" strokeWidth="1" /></svg></>}
      <div className="landing-backdrop" ref={motion.sceneRef}>
        <span className="landing-visually-hidden" id="landing-art-instructions">
          Drag left or right to move this artwork. Use arrow keys to adjust, Enter or Space to nudge, and Escape to reset.
        </span>
        <div className="landing-still-life">
          {(['fern-low', 'fern'] as const).map(id => (
            <div className={`landing-art landing-art-${id}`} key={id}>
              <div className="landing-art-pose" data-motion-pose={id} aria-hidden="true">
                {FERN_BANDS.map((band, index) => (
                  <AsciiArtwork className="landing-fern-band" artwork={band} material="leaf" key={index} />
                ))}
              </div>
              {control(id, id === 'fern' ? 'Bend the tall fern' : 'Bend the lower fern', 'BRUSH / PULL TO BEND')}
            </div>
          ))}
          <div className="landing-art landing-art-wine">
            <div className="landing-art-pose landing-glass-pose" data-motion-pose="wine" aria-hidden="true">
              <AsciiArtwork className="landing-glass-outline" artwork={EMPTY_GLASS} material="glass" />
              <pre className="landing-art-text landing-liquid-grid">
                {GLASS_ROWS.map((_, row) => (
                  <span className="landing-liquid-row" data-liquid-row key={row}>
                    <span /><span className="landing-art-liquid" />
                  </span>
                ))}
              </pre>
            </div>
            {control('wine', 'Tilt the wine glass and swirl the wine', 'DRAG TO SWIRL')}
          </div>
          <div className="landing-art landing-art-bitcoin">
            <div className="landing-coin-perspective" aria-hidden="true">
              <div className="landing-art-pose landing-coin-pose" data-motion-pose="coin">
                <AsciiArtwork className="landing-coin-front" artwork={BITCOIN} material="coin" />
                <AsciiArtwork className="landing-coin-back" artwork={BITCOIN} material="coin" />
                <pre className="landing-art-text landing-coin-edge">{Array.from({ length: 27 }, () => '|||').join('\n')}</pre>
              </div>
            </div>
            {control('coin', 'Rotate or flick the Bitcoin', 'DRAG / FLICK TO SPIN')}
          </div>
          <div className="landing-art-caption" aria-hidden="true">FIG. 01 / BOTANICAL PROOF<br />CHARACTER STUDY · BITKAUN</div>
        </div>
        <div className="landing-frost" aria-hidden="true" />
        <div className="landing-condensation" aria-hidden="true">
          {DEW_DROPS.map(([left, top, size], index) => (
            <span
              key={index}
              className="landing-dew-drop"
              style={{ left: `${left}%`, top: `${top}%`, width: size, height: size * 1.18 }}
            />
          ))}
        </div>
        <div className="landing-reading-veil" aria-hidden="true" />
      </div>
      <div className="landing-motion-controls">
        <span aria-hidden="true">{motion.reducedMotion ? 'MANUAL MOTION' : 'ASCII / ALIVE'}</span>
        <button
          type="button"
          aria-pressed={motion.paused}
          disabled={isExiting || introActive || motion.reducedMotion}
          onClick={() => motion.setPaused(value => !value)}
        >
          {motion.reducedMotion ? 'REDUCED MOTION' : motion.paused ? 'RESUME MOTION' : 'PAUSE MOTION'}
        </button>
      </div>
    </>
  );
});
