import React, { useState, useEffect } from 'react';
import CartoonCanvas from './CartoonCanvas';
import {
  Sparkles,
  Clapperboard,
  Film,
  GitBranch,
  Volume2,
  Play,
  RotateCw,
  Download,
  Bot,
  Activity,
  Layers,
  CheckCircle2,
  Sliders
} from 'lucide-react';

const PRESETS = {
  twinkle: "Cute 3D animated toddler nursery rhyme, Twinkle Twinkle Little Star, 10 scenes of 8 seconds each. Soft pastel colours, rounded glossy toy-like shapes, warm glowing light, big sparkly eyes, smooth gentle motion. Characters: Pip the cream bunny with floppy ears in sky-blue star pyjamas, Twinkle the smiling yellow star, Fox the friendly orange cub with lantern. Female lullaby vocal singing the rhyme, music box, glockenspiel, harp, 90 BPM.",
  macdonald: "Cute 3D animated toddler nursery rhyme, Old MacDonald Had a Farm, 5 scenes of 8 seconds each. Chubby 3D animals: Daisy the spotted cow, Barnaby the fluffy sheep, Pippin the yellow duckling. Soft pastel farmyard, sunny gentle morning, happy walking animals.",
  humpty: "Cute 3D animated fairytale, Humpty Dumpty sat on a wall, 5 scenes of 8 seconds each. Soft rounded egg character in royal velvet jacket, gentle pastel castle garden, smiling sun, gentle happy rescue by fluffy royal ponies.",
  spider: "Cute 3D animated nursery rhyme, The Itsy Bitsy Spider, 5 scenes of 8 seconds each. Tiny friendly purple baby spider with big sparkly eyes climbing a smooth rounded water spout, smiling gentle rain cloud, warm golden sun drying up the rain."
};

export default function App() {
  const [prompt, setPrompt] = useState(PRESETS.twinkle);
  const [sceneCount, setSceneCount] = useState(10);
  const [sceneDuration, setSceneDuration] = useState(8);
  const [voice, setVoice] = useState('en-US-JennyNeural');
  const [bpm, setBpm] = useState(90);

  const [storyboard, setStoryboard] = useState([]);
  const [activeSceneIndex, setActiveSceneIndex] = useState(0);
  const [gitCommits, setGitCommits] = useState([]);

  const [progress, setProgress] = useState({ isRunning: false, text: '', percent: 0 });
  const [activeTab, setActiveTab] = useState('canvas'); // 'canvas' or 'rendered'
  const [videoUrl, setVideoUrl] = useState('/api/video');

  useEffect(() => {
    fetchStoryboard();
    fetchGitHistory();
  }, []);

  const fetchStoryboard = async () => {
    try {
      const res = await fetch('/api/storyboard');
      const data = await res.json();
      if (data.scenes && data.scenes.length > 0) {
        setStoryboard(data.scenes);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const fetchGitHistory = async () => {
    try {
      const res = await fetch('/api/git-history');
      const data = await res.json();
      if (data.commits) {
        setGitCommits(data.commits);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleGenerateStoryboard = async () => {
    setProgress({ isRunning: true, text: 'Consulting local Ollama Mistral model...', percent: 25 });
    try {
      const res = await fetch('/api/generate-storyboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt, num_scenes: parseInt(sceneCount), scene_dur: parseInt(sceneDuration) })
      });
      const data = await res.json();
      if (data.scenes) {
        setStoryboard(data.scenes);
        setActiveSceneIndex(0);
      }
      setProgress({ isRunning: true, text: 'Mistral Storyboard successfully created & committed!', percent: 100 });
      setTimeout(() => setProgress({ isRunning: false, text: '', percent: 0 }), 1500);
      fetchGitHistory();
    } catch (e) {
      alert("Error: " + e);
      setProgress({ isRunning: false, text: '', percent: 0 });
    }
  };

  const handleRenderVideo = async () => {
    setProgress({ isRunning: true, text: 'Starting animation & vocal rendering pipeline...', percent: 5 });
    try {
      await fetch('/api/generate-video', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ voice, bpm: parseInt(bpm) })
      });
      pollVideoProgress();
    } catch (e) {
      alert("Render error: " + e);
      setProgress({ isRunning: false, text: '', percent: 0 });
    }
  };

  const pollVideoProgress = () => {
    const timer = setInterval(async () => {
      try {
        const res = await fetch('/api/progress');
        const data = await res.json();
        setProgress({ isRunning: true, text: data.status, percent: data.percent });

        if (data.percent >= 100) {
          clearInterval(timer);
          setTimeout(() => {
            setProgress({ isRunning: false, text: '', percent: 0 });
            setVideoUrl(`/api/video?t=${Date.now()}`);
            setActiveTab('rendered');
            fetchGitHistory();
          }, 1200);
        }
      } catch (e) {
        clearInterval(timer);
      }
    }, 1500);
  };

  const handleGitCommit = async () => {
    const msg = window.prompt("Enter Git commit message:", "Updated nursery rhyme video: walking animations and neural vocals");
    if (!msg) return;
    try {
      const res = await fetch('/api/git-commit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg })
      });
      const data = await res.json();
      if (data.success) {
        alert("Git commit recorded!");
        fetchGitHistory();
      } else {
        alert("No changes or already up to date.");
      }
    } catch (e) {
      alert("Git error: " + e);
    }
  };

  const currentSceneData = storyboard[activeSceneIndex] || {
    scene_number: 1,
    lyric: "Twinkle, twinkle, little star, how I wonder what you are.",
    action: "Pip gazes out the windowsill at dusk",
    walking_character: "Pip"
  };

  return (
    <div style={{ minHeight: '100vh', background: 'radial-gradient(circle at 15% 10%, #1e1b4b 0%, #090d16 65%)', color: '#f8fafc', padding: '24px', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      <div style={{ maxWidth: '1350px', margin: '0 auto' }}>
        
        {/* Header */}
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '20px', borderBottom: '1px solid rgba(255,255,255,0.08)', marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{ width: '46px', height: '46px', borderRadius: '12px', background: 'linear-gradient(135deg, #f59e0b, #ec4899)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 16px rgba(245, 158, 11, 0.3)' }}>
              <Sparkles size={24} color="#fff" />
            </div>
            <div>
              <h1 style={{ fontSize: '24px', fontWeight: '800', background: 'linear-gradient(to right, #fef08a, #f472b6, #93c5fd)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                3D Nursery Rhyme Video AI Studio
              </h1>
              <p style={{ fontSize: '13px', color: '#94a3b8' }}>
                Local Mistral 7B &bull; React Real-Time Cartoon Engine &bull; Walking & Talking Lip-Sync &bull; Git Versioning
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px', borderRadius: '999px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', fontSize: '12px', fontWeight: '600' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }}></span>
              Local Mistral (Ollama)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 14px', borderRadius: '999px', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', fontSize: '12px', fontWeight: '600', color: '#a5b4fc' }}>
              <GitBranch size={13} />
              Git Versioning Active
            </div>
          </div>
        </header>

        {/* Main Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.15fr 0.85fr', gap: '24px' }}>
          
          {/* Left Column: AI Studio Controls & Git History */}
          <div>
            {/* Prompt & AI Studio Card */}
            <div style={{ background: '#131b2e', borderRadius: '14px', border: '1px solid rgba(255,255,255,0.08)', padding: '22px', marginBottom: '22px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#fef08a', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <Bot size={18} color="#f59e0b" /> Prompt & Mistral AI Decomposition
              </h3>

              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                style={{
                  width: '100%', minHeight: '110px', background: '#0b1120', border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: '10px', padding: '12px', color: '#fff', fontSize: '13.5px', lineHeight: '1.5',
                  resize: 'vertical', marginBottom: '12px', outline: 'none'
                }}
              />

              {/* Presets */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginBottom: '18px' }}>
                <span style={{ fontSize: '12px', color: '#94a3b8', alignSelf: 'center' }}>Presets:</span>
                {Object.keys(PRESETS).map((key) => (
                  <button
                    key={key}
                    onClick={() => setPrompt(PRESETS[key])}
                    style={{
                      background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)',
                      borderRadius: '20px', padding: '4px 12px', color: '#cbd5e1', fontSize: '12px', cursor: 'pointer'
                    }}>
                    {key.toUpperCase()}
                  </button>
                ))}
              </div>

              {/* Form Controls */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '14px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Scene Count
                  </label>
                  <select
                    value={sceneCount}
                    onChange={(e) => setSceneCount(e.target.value)}
                    style={{ width: '100%', background: '#0b1120', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '8px', padding: '8px 10px', color: '#fff' }}>
                    <option value={10}>10 Scenes (80s Total)</option>
                    <option value={5}>5 Scenes (40s Total)</option>
                    <option value={3}>3 Scenes (24s Total)</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Scene Duration
                  </label>
                  <select
                    value={sceneDuration}
                    onChange={(e) => setSceneDuration(e.target.value)}
                    style={{ width: '100%', background: '#0b1120', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '8px', padding: '8px 10px', color: '#fff' }}>
                    <option value={8}>8 Seconds per scene</option>
                    <option value={5}>5 Seconds per scene</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '18px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Neural Singing Voice
                  </label>
                  <select
                    value={voice}
                    onChange={(e) => setVoice(e.target.value)}
                    style={{ width: '100%', background: '#0b1120', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '8px', padding: '8px 10px', color: '#fff' }}>
                    <option value="en-US-JennyNeural">Jenny (Soft Bedtime Lullaby)</option>
                    <option value="en-US-AnaNeural">Ana (Sweet Toddler/Child Voice)</option>
                    <option value="en-GB-SoniaNeural">Sonia (British Classical Lullaby)</option>
                    <option value="en-US-AriaNeural">Aria (Warm Storyteller)</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: '700', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>
                    Tempo / Arrangement
                  </label>
                  <select
                    value={bpm}
                    onChange={(e) => setBpm(e.target.value)}
                    style={{ width: '100%', background: '#0b1120', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '8px', padding: '8px 10px', color: '#fff' }}>
                    <option value={90}>90 BPM (Gentle Music Box & Harp)</option>
                    <option value={80}>80 BPM (Dreamy Bedtime)</option>
                    <option value={100}>100 BPM (Cheerful Rhythm)</option>
                  </select>
                </div>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                <button
                  onClick={handleGenerateStoryboard}
                  style={{
                    background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', color: '#fff', border: 'none',
                    borderRadius: '8px', padding: '10px 16px', fontWeight: '700', fontSize: '13px', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', gap: '6px'
                  }}>
                  <Bot size={15} /> 1. Plan with Mistral AI
                </button>

                <button
                  onClick={handleRenderVideo}
                  style={{
                    background: 'linear-gradient(135deg, #f59e0b, #ec4899)', color: '#fff', border: 'none',
                    borderRadius: '8px', padding: '10px 16px', fontWeight: '700', fontSize: '13px', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', gap: '6px'
                  }}>
                  <Film size={15} /> 2. Render Full Animated Video
                </button>

                <button
                  onClick={handleGitCommit}
                  style={{
                    background: 'rgba(255,255,255,0.08)', color: '#fff', border: '1px solid rgba(255,255,255,0.15)',
                    borderRadius: '8px', padding: '10px 14px', fontWeight: '600', fontSize: '13px', cursor: 'pointer',
                    display: 'flex', alignItems: 'center', gap: '6px'
                  }}>
                  <GitBranch size={15} /> Git Checkpoint
                </button>
              </div>

              {/* Progress Box */}
              {progress.isRunning && (
                <div style={{ marginTop: '14px', background: '#0b1120', borderRadius: '8px', padding: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#94a3b8', marginBottom: '6px' }}>
                    <span>{progress.text}</span>
                    <span>{progress.percent}%</span>
                  </div>
                  <div style={{ width: '100%', height: '8px', background: 'rgba(255,255,255,0.1)', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${progress.percent}%`, height: '100%', background: 'linear-gradient(90deg, #f59e0b, #ec4899, #6366f1)', transition: 'width 0.3s' }}></div>
                  </div>
                </div>
              )}
            </div>

            {/* Git Version Tracking Card */}
            <div style={{ background: '#131b2e', borderRadius: '14px', border: '1px solid rgba(255,255,255,0.08)', padding: '22px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#fef08a', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <GitBranch size={18} color="#a5b4fc" /> Git Version History & Checkpoints
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '200px', overflowY: 'auto' }}>
                {gitCommits.map((c, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 10px', background: '#0b1120', borderRadius: '6px', fontSize: '12px', borderLeft: '3px solid #6366f1' }}>
                    <div>
                      <span style={{ fontFamily: 'monospace', color: '#f59e0b', fontWeight: '700' }}>{c.hash}</span>
                      <span style={{ marginLeft: '8px', color: '#cbd5e1' }}>{c.message}</span>
                    </div>
                    <span style={{ color: '#64748b', fontSize: '11px' }}>{c.date}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Cartoon Stage & Video Player */}
          <div>
            <div style={{ background: '#131b2e', borderRadius: '14px', border: '1px solid rgba(255,255,255,0.08)', padding: '22px', marginBottom: '22px' }}>
              
              {/* Tab Selector */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={() => setActiveTab('canvas')}
                    style={{
                      background: activeTab === 'canvas' ? '#f59e0b' : 'rgba(255,255,255,0.06)',
                      color: activeTab === 'canvas' ? '#000' : '#fff',
                      border: 'none', borderRadius: '8px', padding: '6px 14px', fontWeight: '700', fontSize: '13px', cursor: 'pointer'
                    }}>
                    🎭 Live Cartoon Stage (Walking & Lip-Sync)
                  </button>
                  <button
                    onClick={() => setActiveTab('rendered')}
                    style={{
                      background: activeTab === 'rendered' ? '#6366f1' : 'rgba(255,255,255,0.06)',
                      color: '#fff', border: 'none', borderRadius: '8px', padding: '6px 14px', fontWeight: '700', fontSize: '13px', cursor: 'pointer'
                    }}>
                    🎬 Rendered Master Video
                  </button>
                </div>

                {activeTab === 'canvas' && (
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                    <span style={{ fontSize: '12px', color: '#94a3b8' }}>Scene:</span>
                    <select
                      value={activeSceneIndex}
                      onChange={(e) => setActiveSceneIndex(parseInt(e.target.value))}
                      style={{ background: '#0b1120', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '6px', padding: '4px 8px', color: '#fef08a', fontSize: '12px' }}>
                      {storyboard.map((sc, idx) => (
                        <option key={idx} value={idx}>Scene {sc.scene_number}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              {/* Tab 1: Live Interactive Cartoon Stage */}
              {activeTab === 'canvas' ? (
                <div>
                  <CartoonCanvas
                    currentScene={currentSceneData.scene_number}
                    lyrics={currentSceneData.lyric}
                    isPlaying={true}
                  />
                  <div style={{ marginTop: '10px', fontSize: '12px', color: '#94a3b8', display: 'flex', justifyContent: 'space-between' }}>
                    <span>Action: <strong>{currentSceneData.action}</strong></span>
                    <span>Walking: <strong>{currentSceneData.walking_character || 'Pip/Fox'}</strong></span>
                  </div>
                </div>
              ) : (
                /* Tab 2: Rendered Master Video Player */
                <div>
                  <video
                    src={videoUrl}
                    controls
                    style={{ width: '100%', borderRadius: '12px', boxShadow: '0 8px 30px rgba(0,0,0,0.6)', display: 'block' }}
                  />
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', padding: '8px 12px', background: '#0b1120', borderRadius: '8px', fontSize: '13px' }}>
                    <div>
                      <strong>Twinkle_Twinkle_Little_Star_3D.mp4</strong>
                      <div style={{ fontSize: '11px', color: '#94a3b8' }}>80s &bull; H.264 &bull; AAC Neural Vocals &bull; 24 FPS</div>
                    </div>
                    <a
                      href={videoUrl}
                      download="Twinkle_Twinkle_Little_Star_3D.mp4"
                      style={{ background: '#f59e0b', color: '#000', padding: '6px 14px', borderRadius: '6px', textDecoration: 'none', fontWeight: '700', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Download size={14} /> Download MP4
                    </a>
                  </div>
                </div>
              )}
            </div>

            {/* Storyboard Scene Scrubber Card */}
            <div style={{ background: '#131b2e', borderRadius: '14px', border: '1px solid rgba(255,255,255,0.08)', padding: '22px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', color: '#fef08a', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
                <Layers size={18} color="#ec4899" /> 10-Scene Storyboard & Walking Director
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '340px', overflowY: 'auto' }}>
                {storyboard.map((sc, idx) => (
                  <div
                    key={idx}
                    onClick={() => setActiveSceneIndex(idx)}
                    style={{
                      background: activeSceneIndex === idx ? '#1e293b' : '#0b1120',
                      borderLeft: `4px solid ${activeSceneIndex === idx ? '#f59e0b' : '#475569'}`,
                      borderRadius: '8px', padding: '10px 14px', cursor: 'pointer', transition: 'all 0.2s'
                    }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                      <strong style={{ fontSize: '13px', color: activeSceneIndex === idx ? '#fef08a' : '#fff' }}>
                        Scene {sc.scene_number}: &ldquo;{sc.lyric}&rdquo;
                      </strong>
                      <span style={{ fontSize: '11px', color: '#94a3b8' }}>{sc.duration}s</span>
                    </div>
                    <p style={{ fontSize: '12px', color: '#94a3b8', margin: '2px 0' }}>{sc.action}</p>
                    <div style={{ fontSize: '11px', color: '#a5b4fc', marginTop: '4px' }}>
                      🚶 Motion: {sc.motion_type || sc.walking_character || 'Walking / Swaying'}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
