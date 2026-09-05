import React, { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  speed: number;
  char: '0' | '1';
  opacity: number;
  fontSize: number;
  flipCooldown: number;
  driftX: number;
}

export const AmbientBinaryRain: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);

    // Number of scattered subtle particles (few and scattered for pure ambience)
    const particleCount = Math.max(18, Math.floor(width / 65));
    const particles: Particle[] = [];

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        speed: 0.30 + Math.random() * 0.45, // Slow gentle drift
        char: Math.random() > 0.5 ? '0' : '1',
        opacity: 0.20 + Math.random() * 0.15, // More opaque and visible (0.20 - 0.35)
        fontSize: Math.random() > 0.5 ? 18 : 15, // Bigger, clearly visible digits
        flipCooldown: Math.floor(50 + Math.random() * 120), // Periodic flip timer
        driftX: (Math.random() - 0.5) * 0.1 // Tiny horizontal jitter
      });
    }

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      ctx.textBaseline = 'top';

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        // Slowly fall down
        p.y += p.speed;
        p.x += p.driftX;

        // Reset to top when passing bottom
        if (p.y > height + 15) {
          p.y = -15;
          p.x = Math.random() * width;
          p.char = Math.random() > 0.5 ? '0' : '1';
          p.opacity = 0.20 + Math.random() * 0.15;
        }

        // Periodically scramble back and forth between 0 and 1
        p.flipCooldown--;
        if (p.flipCooldown <= 0) {
          p.char = p.char === '0' ? '1' : '0';
          p.flipCooldown = Math.floor(60 + Math.random() * 160); // 1 to 3 seconds
        }

        // Draw the visible phosphor green digit
        ctx.font = `bold ${p.fontSize}px 'Share Tech Mono', 'VT323', monospace`;
        ctx.fillStyle = `rgba(0, 204, 85, ${p.opacity})`;
        ctx.fillText(p.char, p.x, p.y);
      }

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="ambient-binary-canvas"
      aria-hidden="true"
    />
  );
};
