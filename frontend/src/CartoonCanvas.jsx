import React, { useRef, useEffect, useState } from 'react';
import { Play, Pause, RotateCcw, Volume2, VolumeX, Sparkles, Footprints, MessageSquare } from 'lucide-react';

export default function CartoonCanvas({ currentScene = 1, isPlaying = true, lyrics = "Twinkle, twinkle, little star", voiceUrl = "" }) {
  const canvasRef = useRef(null);
  const [internalPlaying, setInternalPlaying] = useState(isPlaying);
  const [characterAction, setCharacterAction] = useState('walk'); // 'walk', 'talk', 'dance', 'wave'
  const [isTalking, setIsTalking] = useState(true);
  const [isWalking, setIsWalking] = useState(true);
  const [foxWalkProgress, setFoxWalkProgress] = useState(0.2);
  const audioRef = useRef(null);
  const animFrameRef = useRef(null);

  // Sync internal playing with prop
  useEffect(() => {
    setInternalPlaying(isPlaying);
  }, [isPlaying]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let startTime = performance.now();
    let blinkTimer = 0;
    let isBlinking = false;

    const render = (now) => {
      const elapsed = (now - startTime) / 1000;
      const w = canvas.width;
      const h = canvas.height;

      // Clear
      ctx.clearRect(0, 0, w, h);

      // --- 1. PARALLAX BACKGROUND ACCORDING TO SCENE ---
      drawBackground(ctx, w, h, currentScene, elapsed);

      // --- 2. FLOATING STAR (TWINKLE) ---
      drawTwinkle(ctx, w, h, elapsed, isTalking);

      // --- 3. CHARACTER ANIMATION (PIP OR FOX BASED ON SCENE) ---
      // Eye blink controller: blinks every 3.5 seconds for 0.15s
      blinkTimer += 0.016;
      if (blinkTimer > 3.5) {
        isBlinking = true;
        if (blinkTimer > 3.65) {
          isBlinking = false;
          blinkTimer = 0;
        }
      }

      // Mouth talk oscillation (simulated lip-sync visemes)
      const mouthOpen = isTalking ? (Math.sin(elapsed * 12) > 0 ? (0.5 + 0.5 * Math.sin(elapsed * 18)) : 0.1) : 0;

      if (currentScene === 5 || currentScene === 6 || currentScene === 9) {
        // Fox scenes
        drawFox(ctx, w, h, elapsed, isWalking, mouthOpen, isBlinking);
      } else {
        // Pip (Bunny) scenes
        drawPip(ctx, w, h, elapsed, isWalking, characterAction, mouthOpen, isBlinking);
      }

      // --- 4. FLOATING PARTICLES & FIREFLIES ---
      drawParticles(ctx, w, h, elapsed);

      if (internalPlaying) {
        animFrameRef.current = requestAnimationFrame(render);
      }
    };

    animFrameRef.current = requestAnimationFrame(render);
    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [currentScene, internalPlaying, isTalking, isWalking, characterAction]);

  // --- BACKGROUND DRAWING ---
  const drawBackground = (ctx, w, h, scene, t) => {
    // Sky gradient
    let grad = ctx.createLinearGradient(0, 0, 0, h);
    if (scene === 3) { // Sunset
      grad.addColorStop(0, '#f97316');
      grad.addColorStop(0.5, '#ec4899');
      grad.addColorStop(1, '#3b0764');
    } else if (scene === 8) { // Sunrise
      grad.addColorStop(0, '#f472b6');
      grad.addColorStop(0.6, '#fef08a');
      grad.addColorStop(1, '#60a5fa');
    } else { // Twilight / Night
      grad.addColorStop(0, '#0f172a');
      grad.addColorStop(0.7, '#1e1b4b');
      grad.addColorStop(1, '#2e1065');
    }
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    // Crescent Moon
    if (scene !== 3 && scene !== 8) {
      ctx.save();
      ctx.fillStyle = '#fef08a';
      ctx.beginPath();
      ctx.arc(w * 0.18, h * 0.22, 28, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#1e1b4b';
      ctx.beginPath();
      ctx.arc(w * 0.18 + 12, h * 0.22 - 6, 26, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    // Smiling Sun for scene 3
    if (scene === 3) {
      const sunY = h * 0.45 + Math.sin(t * 0.5) * 15;
      ctx.save();
      ctx.fillStyle = '#fbbf24';
      ctx.beginPath();
      ctx.arc(w * 0.25, sunY, 55, 0, Math.PI * 2);
      ctx.fill();
      // Sun face
      ctx.fillStyle = '#78350f';
      ctx.beginPath();
      ctx.arc(w * 0.25 - 16, sunY - 10, 5, 0, Math.PI * 2);
      ctx.arc(w * 0.25 + 16, sunY - 10, 5, 0, Math.PI * 2);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(w * 0.25, sunY + 8, 14, 0, Math.PI);
      ctx.stroke();
      ctx.restore();
    }

    // Rolling Green Hills in background
    ctx.fillStyle = '#064e3b';
    ctx.beginPath();
    ctx.arc(w * 0.25, h * 1.3, w * 0.65, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#047857';
    ctx.beginPath();
    ctx.arc(w * 0.8, h * 1.25, w * 0.6, 0, Math.PI * 2);
    ctx.fill();

    // Foreground grassy path
    ctx.fillStyle = '#059669';
    ctx.beginPath();
    ctx.ellipse(w * 0.5, h * 0.98, w * 0.7, h * 0.25, 0, 0, Math.PI * 2);
    ctx.fill();
  };

  // --- DRAW TWINKLE (SMILING STAR) ---
  const drawTwinkle = (ctx, w, h, t, talking) => {
    const starX = w * 0.72 + Math.sin(t * 1.2) * 20;
    const starY = h * 0.22 + Math.cos(t * 1.5) * 12;
    const pulse = 1.0 + 0.15 * Math.sin(t * 4);

    ctx.save();
    ctx.translate(starX, starY);
    ctx.scale(pulse, pulse);

    // Glowing aura
    let glow = ctx.createRadialGradient(0, 0, 10, 0, 0, 70);
    glow.addColorStop(0, 'rgba(254, 240, 138, 0.9)');
    glow.addColorStop(0.5, 'rgba(251, 191, 36, 0.4)');
    glow.addColorStop(1, 'rgba(251, 191, 36, 0)');
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(0, 0, 70, 0, Math.PI * 2);
    ctx.fill();

    // 5-Point Rounded Star Body
    ctx.fillStyle = '#fef08a';
    ctx.strokeStyle = '#f59e0b';
    ctx.lineWidth = 3;
    drawStarShape(ctx, 0, 0, 5, 34, 18);
    ctx.fill();
    ctx.stroke();

    // Rosy Cheeks
    ctx.fillStyle = 'rgba(244, 114, 182, 0.7)';
    ctx.beginPath();
    ctx.arc(-14, 4, 6, 0, Math.PI * 2);
    ctx.arc(14, 4, 6, 0, Math.PI * 2);
    ctx.fill();

    // Cute Eyes (Winking one eye occasionally)
    ctx.fillStyle = '#1e1b4b';
    const isWink = Math.sin(t * 2) > 0.85;
    ctx.beginPath();
    ctx.arc(-10, -4, 4, 0, Math.PI * 2);
    ctx.fill();

    if (isWink) {
      ctx.beginPath();
      ctx.arc(10, -4, 5, 0, Math.PI);
      ctx.lineWidth = 2.5;
      ctx.stroke();
    } else {
      ctx.beginPath();
      ctx.arc(10, -4, 4, 0, Math.PI * 2);
      ctx.fill();
    }

    // Talking / Smiling Mouth
    ctx.fillStyle = '#be123c';
    ctx.beginPath();
    if (talking) {
      const mouthH = 4 + 6 * Math.abs(Math.sin(t * 10));
      ctx.ellipse(0, 8, 7, mouthH, 0, 0, Math.PI * 2);
    } else {
      ctx.arc(0, 6, 8, 0, Math.PI);
    }
    ctx.fill();

    ctx.restore();
  };

  // --- DRAW FOX CUB (WALKING WITH LANTERN) ---
  const drawFox = (ctx, w, h, t, walking, mouthVal, blinking) => {
    const walkSpeed = walking ? 0.08 : 0;
    const charX = w * (0.25 + ((t * walkSpeed) % 0.55));
    const stepFreq = 8;
    const bob = walking ? Math.abs(Math.sin(t * stepFreq)) * 10 : 0;
    const charY = h * 0.74 - bob;

    ctx.save();
    ctx.translate(charX, charY);

    // --- LEGS (WALKING ANIMATION) ---
    const legSwing = walking ? Math.sin(t * stepFreq) * 18 : 0;
    ctx.fillStyle = '#c2410c';
    // Back leg
    ctx.save();
    ctx.translate(-14, 25);
    ctx.rotate((-legSwing * Math.PI) / 180);
    ctx.fillRect(-6, 0, 12, 28);
    ctx.restore();

    // Fluffy tail with white tip swaying
    const tailAngle = Math.sin(t * 4) * 0.25;
    ctx.save();
    ctx.translate(-30, 8);
    ctx.rotate(tailAngle);
    ctx.fillStyle = '#ea580c';
    ctx.beginPath();
    ctx.ellipse(-25, -12, 35, 18, -0.3, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#ffffff';
    ctx.beginPath();
    ctx.ellipse(-52, -22, 14, 10, -0.3, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // Body
    ctx.fillStyle = '#ea580c';
    ctx.beginPath();
    ctx.ellipse(0, 0, 32, 38, 0, 0, Math.PI * 2);
    ctx.fill();

    // White Chest
    ctx.fillStyle = '#fff7ed';
    ctx.beginPath();
    ctx.ellipse(10, 4, 18, 24, 0, 0, Math.PI * 2);
    ctx.fill();

    // Front leg
    ctx.fillStyle = '#c2410c';
    ctx.save();
    ctx.translate(14, 25);
    ctx.rotate((legSwing * Math.PI) / 180);
    ctx.fillRect(-6, 0, 12, 28);
    ctx.restore();

    // Head
    ctx.fillStyle = '#ea580c';
    ctx.beginPath();
    ctx.arc(14, -42, 30, 0, Math.PI * 2);
    ctx.fill();

    // Ears
    ctx.fillStyle = '#c2410c';
    ctx.beginPath();
    ctx.moveTo(-4, -65);
    ctx.lineTo(8, -92);
    ctx.lineTo(18, -65);
    ctx.fill();
    ctx.beginPath();
    ctx.moveTo(18, -65);
    ctx.lineTo(30, -92);
    ctx.lineTo(38, -65);
    ctx.fill();

    // Cheeks & Muzzle
    ctx.fillStyle = '#fff7ed';
    ctx.beginPath();
    ctx.ellipse(26, -34, 16, 12, 0, 0, Math.PI * 2);
    ctx.fill();

    // Eyes with blink
    ctx.fillStyle = '#1e1b4b';
    if (blinking) {
      ctx.fillRect(8, -46, 10, 3);
      ctx.fillRect(26, -46, 10, 3);
    } else {
      ctx.beginPath();
      ctx.arc(13, -46, 5, 0, Math.PI * 2);
      ctx.arc(31, -46, 5, 0, Math.PI * 2);
      ctx.fill();
      // Sparkle specular reflection
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(11, -48, 1.8, 0, Math.PI * 2);
      ctx.arc(29, -48, 1.8, 0, Math.PI * 2);
      ctx.fill();
    }

    // Black button nose
    ctx.fillStyle = '#1c1917';
    ctx.beginPath();
    ctx.arc(36, -36, 4, 0, Math.PI * 2);
    ctx.fill();

    // Mouth (Talking lip sync)
    ctx.fillStyle = '#991b1b';
    ctx.beginPath();
    if (mouthVal > 0.2) {
      ctx.ellipse(26, -26, 6, 4 + mouthVal * 7, 0, 0, Math.PI * 2);
    } else {
      ctx.arc(26, -26, 5, 0, Math.PI);
    }
    ctx.fill();

    // --- SWINGING LANTERN ARM & GLOW ---
    const armSwing = walking ? -Math.sin(t * stepFreq) * 12 : 0;
    const lanternX = 35 + armSwing;
    const lanternY = 4;
    ctx.fillStyle = '#78350f';
    ctx.fillRect(lanternX - 10, lanternY, 20, 24);
    ctx.fillStyle = '#fbbf24';
    ctx.fillRect(lanternX - 8, lanternY + 3, 16, 18);

    // Warm radial lantern glow
    let lGlow = ctx.createRadialGradient(lanternX, lanternY + 12, 5, lanternX, lanternY + 12, 75);
    lGlow.addColorStop(0, 'rgba(251, 191, 36, 0.85)');
    lGlow.addColorStop(0.6, 'rgba(245, 158, 11, 0.3)');
    lGlow.addColorStop(1, 'rgba(245, 158, 11, 0)');
    ctx.fillStyle = lGlow;
    ctx.beginPath();
    ctx.arc(lanternX, lanternY + 12, 75, 0, Math.PI * 2);
    ctx.fill();

    ctx.restore();
  };

  // --- DRAW PIP THE BABY BUNNY ---
  const drawPip = (ctx, w, h, t, walking, action, mouthVal, blinking) => {
    let charX = w * 0.42;
    let charY = h * 0.72;

    if (action === 'dance') {
      charX += Math.sin(t * 5) * 24;
      charY += Math.abs(Math.sin(t * 10)) * -14;
    } else if (action === 'hop') {
      charY += Math.abs(Math.sin(t * 8)) * -22;
    }

    ctx.save();
    ctx.translate(charX, charY);

    // Floppy ears with spring oscillation
    const earBounce = Math.sin(t * 6) * 0.12;
    ctx.fillStyle = '#fef3c7'; // Cream fur
    // Left ear
    ctx.save();
    ctx.translate(-14, -60);
    ctx.rotate(-0.25 + earBounce);
    ctx.beginPath();
    ctx.ellipse(0, -28, 12, 34, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fbcfe8'; // Pink inner ear
    ctx.beginPath();
    ctx.ellipse(0, -28, 6, 26, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // Right ear
    ctx.save();
    ctx.translate(14, -60);
    ctx.rotate(0.25 - earBounce);
    ctx.fillStyle = '#fef3c7';
    ctx.beginPath();
    ctx.ellipse(0, -28, 12, 34, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fbcfe8';
    ctx.beginPath();
    ctx.ellipse(0, -28, 6, 26, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();

    // Body in Sky-Blue Star Pyjamas
    ctx.fillStyle = '#7dd3fc';
    ctx.beginPath();
    ctx.ellipse(0, 0, 36, 42, 0, 0, Math.PI * 2);
    ctx.fill();

    // Tiny stars on pyjamas
    ctx.fillStyle = '#fef08a';
    drawStarShape(ctx, -14, -6, 5, 5, 2.5); ctx.fill();
    drawStarShape(ctx, 12, 8, 5, 5, 2.5); ctx.fill();
    drawStarShape(ctx, -4, 18, 5, 4, 2); ctx.fill();

    // Chubby Paws / Arms (Waving if action == 'wave')
    const waveAngle = action === 'wave' ? Math.sin(t * 8) * 0.4 : 0;
    ctx.fillStyle = '#fef3c7';
    // Left arm
    ctx.save();
    ctx.translate(-28, -6);
    ctx.rotate(waveAngle);
    ctx.beginPath();
    ctx.ellipse(0, -8, 10, 16, -0.4, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
    // Right arm
    ctx.beginPath();
    ctx.ellipse(28, 6, 10, 16, 0.4, 0, Math.PI * 2);
    ctx.fill();

    // Feet
    ctx.fillStyle = '#bae6fd';
    ctx.beginPath();
    ctx.ellipse(-18, 38, 14, 10, 0, 0, Math.PI * 2);
    ctx.ellipse(18, 38, 14, 10, 0, 0, Math.PI * 2);
    ctx.fill();

    // Head
    ctx.fillStyle = '#fef3c7';
    ctx.beginPath();
    ctx.arc(0, -44, 34, 0, Math.PI * 2);
    ctx.fill();

    // Rosy Cheeks
    ctx.fillStyle = 'rgba(244, 114, 182, 0.6)';
    ctx.beginPath();
    ctx.arc(-20, -36, 8, 0, Math.PI * 2);
    ctx.arc(20, -36, 8, 0, Math.PI * 2);
    ctx.fill();

    // Eyes with blink
    ctx.fillStyle = '#1e1b4b';
    if (blinking) {
      ctx.fillRect(-18, -48, 12, 3);
      ctx.fillRect(8, -48, 12, 3);
    } else {
      ctx.beginPath();
      ctx.arc(-14, -48, 6.5, 0, Math.PI * 2);
      ctx.arc(14, -48, 6.5, 0, Math.PI * 2);
      ctx.fill();
      // Double Specular Sparkle Highlights
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(-16, -50, 2.5, 0, Math.PI * 2);
      ctx.arc(-12, -46, 1.2, 0, Math.PI * 2);
      ctx.arc(12, -50, 2.5, 0, Math.PI * 2);
      ctx.arc(16, -46, 1.2, 0, Math.PI * 2);
      ctx.fill();
    }

    // Tiny pink button nose
    ctx.fillStyle = '#f472b6';
    ctx.beginPath();
    ctx.ellipse(0, -38, 4, 3, 0, 0, Math.PI * 2);
    ctx.fill();

    // Talking / Smiling Mouth
    ctx.fillStyle = '#be123c';
    ctx.beginPath();
    if (mouthVal > 0.2) {
      ctx.ellipse(0, -28, 7, 4 + mouthVal * 8, 0, 0, Math.PI * 2);
    } else {
      ctx.arc(0, -30, 6, 0, Math.PI);
    }
    ctx.fill();

    ctx.restore();
  };

  // Helper star drawing function
  const drawStarShape = (ctx, cx, cy, spikes, outerRadius, innerRadius) => {
    let rot = (Math.PI / 2) * 3;
    let x = cx;
    let y = cy;
    let step = Math.PI / spikes;

    ctx.beginPath();
    ctx.moveTo(cx, cy - outerRadius);
    for (let i = 0; i < spikes; i++) {
      x = cx + Math.cos(rot) * outerRadius;
      y = cy + Math.sin(rot) * outerRadius;
      ctx.lineTo(x, y);
      rot += step;

      x = cx + Math.cos(rot) * innerRadius;
      y = cy + Math.sin(rot) * innerRadius;
      ctx.lineTo(x, y);
      rot += step;
    }
    ctx.lineTo(cx, cy - outerRadius);
    ctx.closePath();
  };

  // Ambient floating particles
  const drawParticles = (ctx, w, h, t) => {
    ctx.save();
    for (let i = 0; i < 25; i++) {
      const px = (Math.sin(i * 123 + t * 0.5) * 0.5 + 0.5) * w;
      const py = (Math.cos(i * 321 + t * 0.7) * 0.5 + 0.5) * h;
      const alpha = 0.3 + 0.7 * Math.sin(t * 3 + i);
      ctx.fillStyle = `rgba(254, 240, 138, ${alpha})`;
      ctx.beginPath();
      ctx.arc(px, py, 2.5, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  };

  return (
    <div style={{ background: '#0f172a', borderRadius: '14px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.1)' }}>
      <div style={{ position: 'relative', width: '100%', aspectRatio: '16/9' }}>
        <canvas
          ref={canvasRef}
          width={1280}
          height={720}
          style={{ width: '100%', height: '100%', display: 'block' }}
        />

        {/* Lyrical Subtitle Ribbon */}
        <div style={{
          position: 'absolute', bottom: '16px', left: '50%', transform: 'translateX(-50%)',
          background: 'rgba(15, 23, 42, 0.85)', backdropFilter: 'blur(8px)',
          padding: '8px 24px', borderRadius: '999px',
          border: '1px solid rgba(251, 191, 36, 0.3)',
          color: '#fef08a', fontSize: '15px', fontWeight: '600', letterSpacing: '0.3px',
          boxShadow: '0 4px 20px rgba(0,0,0,0.5)', textAlign: 'center', pointerEvents: 'none'
        }}>
          &ldquo;{lyrics}&rdquo;
        </div>
      </div>

      {/* Real-time Cartoon Controls Bar */}
      <div style={{
        padding: '12px 18px', background: '#1e293b', display: 'flex',
        flexWrap: 'wrap', gap: '10px', alignItems: 'center', justifyContent: 'space-between',
        borderTop: '1px solid rgba(255,255,255,0.08)'
      }}>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          <button
            onClick={() => setInternalPlaying(!internalPlaying)}
            style={{
              background: internalPlaying ? '#f59e0b' : '#3b82f6', color: '#fff',
              border: 'none', borderRadius: '8px', padding: '6px 14px', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '600', fontSize: '13px'
            }}>
            {internalPlaying ? <Pause size={15} /> : <Play size={15} />}
            {internalPlaying ? 'Pause Canvas' : 'Play Canvas'}
          </button>

          <button
            onClick={() => setIsWalking(!isWalking)}
            style={{
              background: isWalking ? 'rgba(99, 102, 241, 0.25)' : 'rgba(255,255,255,0.06)',
              borderColor: isWalking ? '#6366f1' : 'transparent', borderStyle: 'solid', borderWidth: '1px',
              color: '#fff', borderRadius: '8px', padding: '6px 12px', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px'
            }}>
            <Footprints size={14} color="#a5b4fc" />
            Walk: {isWalking ? 'ON' : 'OFF'}
          </button>

          <button
            onClick={() => setIsTalking(!isTalking)}
            style={{
              background: isTalking ? 'rgba(236, 72, 153, 0.25)' : 'rgba(255,255,255,0.06)',
              borderColor: isTalking ? '#ec4899' : 'transparent', borderStyle: 'solid', borderWidth: '1px',
              color: '#fff', borderRadius: '8px', padding: '6px 12px', cursor: 'pointer',
              display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px'
            }}>
            <MessageSquare size={14} color="#f472b6" />
            Lip-Sync: {isTalking ? 'ON' : 'OFF'}
          </button>
        </div>

        {/* Character Action Mode Selector */}
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: '#94a3b8' }}>Action:</span>
          {['walk', 'dance', 'hop', 'wave'].map((act) => (
            <button
              key={act}
              onClick={() => setCharacterAction(act)}
              style={{
                background: characterAction === act ? '#f59e0b' : 'rgba(255,255,255,0.06)',
                color: characterAction === act ? '#000' : '#cbd5e1',
                border: 'none', borderRadius: '6px', padding: '4px 10px',
                fontSize: '11px', fontWeight: '700', textTransform: 'capitalize', cursor: 'pointer'
              }}>
              {act}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
