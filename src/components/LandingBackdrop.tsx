import React from 'react';
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

interface AsciiArtworkProps {
  artwork: string;
  className: string;
  material: 'leaf' | 'glass' | 'coin';
}

function AsciiArtwork({ artwork, className, material }: AsciiArtworkProps) {
  const rows = artwork.split('\n');

  return (
    <pre className={`landing-art ${className}`}>
      {rows.map((row, rowIndex) => {
        const start = row.search(/\S/);
        const end = row.trimEnd().length;
        const silhouette = start < 0 ? '' : row.slice(start, end);
        const isLiquid = material === 'glass' && rowIndex >= 14 && rowIndex < 30;
        const isSolid = material === 'coin' || (material === 'glass' && rowIndex >= 14);
        const isGlassPane = material === 'glass' && rowIndex >= 6 && rowIndex < 14;

        return (
          <React.Fragment key={rowIndex}>
            {start < 0 ? row : (
              <>
                {row.slice(0, start)}
                {isSolid || isGlassPane ? (
                  <span className={isGlassPane ? 'landing-art-pane' : `landing-art-solid${isLiquid ? ' landing-art-liquid' : ''}`}>
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

export const LandingBackdrop = React.memo(function LandingBackdrop() {
  return (
    <div className="landing-backdrop" aria-hidden="true">
      <div className="landing-still-life">
        <AsciiArtwork className="landing-art-fern-low" artwork={FERN} material="leaf" />
        <AsciiArtwork className="landing-art-fern" artwork={FERN} material="leaf" />
        <AsciiArtwork className="landing-art-wine" artwork={WINE_GLASS} material="glass" />
        <AsciiArtwork className="landing-art-bitcoin" artwork={BITCOIN} material="coin" />
        <div className="landing-art-caption">FIG. 01 / BOTANICAL PROOF<br />CHARACTER STUDY · BITKAUN</div>
      </div>
      <div className="landing-frost" />
      <div className="landing-condensation">
        {DEW_DROPS.map(([left, top, size], index) => (
          <span
            key={index}
            className="landing-dew-drop"
            style={{ left: `${left}%`, top: `${top}%`, width: size, height: size * 1.18 }}
          />
        ))}
      </div>
      <div className="landing-reading-veil" />
    </div>
  );
});
