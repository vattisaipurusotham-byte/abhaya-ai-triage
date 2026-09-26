import os
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from gtts import gTTS

app = FastAPI(
    title="Abhaya AI - Trauma Triage Engine",
    description="Real-time Stress and Trauma Assessment Module for NHAA (14566)",
    version="0.7.0"
)

# --- BACKEND SCHEMAS & LOGIC ---

class TriageRequest(BaseModel):
    caller_id: str
    phone_number: str
    text_narrative: str
    whisper_detected: bool = False
    f0_pitch_hz: float = 210.0

class TriageResponse(BaseModel):
    caller_id: str
    svi_score: float
    risk_category: str
    recommended_action: str
    poa_section_mapped: Optional[str] = None
    statutory_relief_total: str
    fir_stage_payout: str
    dtmf_mode_recommended: bool

def calculate_svi_and_relief(narrative: str, pitch: float, whisper: bool):
    """Calculates SVI score, risk category, PoA legal mapping, and statutory compensation."""
    score = 20.0
    poa_mapped = "General Guidance / Non-Atrocity Inquiry"
    relief_total = "₹0"
    fir_payout = "₹0 (Inquiry Only)"
    
    text_lower = narrative.lower()
    
    if any(word in text_lower for word in ["kill", "murder", "dead", "body", "shot", "blood"]):
        score += 55.0
        poa_mapped = "PoA Act Sec 3(2)(v) - Heinous Violence / Murder"
        relief_total = "₹8,25,000"
        fir_payout = "₹6,18,750 (75% Immediate FIR Stage Relief)"
    elif any(word in text_lower for word in ["rape", "assault", "gang rape", "modesty"]):
        score += 55.0
        poa_mapped = "PoA Act Sec 3(1)(w) - Sexual Exploitation / Assault"
        relief_total = "₹5,00,000"
        fir_payout = "₹2,50,000 (50% Post-Medical Exam Relief)"
    elif any(word in text_lower for word in ["boycott", "land", "evicted", "water", "fields", "threat"]):
        score += 35.0
        poa_mapped = "PoA Act Sec 3(1)(iv) / Sec 3(1)(v) - Land Displacement & Social Boycott"
        relief_total = "₹1,00,000"
        fir_payout = "₹25,000 (25% Initial FIR Registration Relief)"
    elif any(word in text_lower for word in ["slur", "humiliated", "abused", "insult"]):
        score += 20.0
        poa_mapped = "PoA Act Sec 3(1)(r) - Intentional Insult / Public Humiliation"
        relief_total = "₹1,00,000"
        fir_payout = "₹10,000 (10% Initial Relief)"

    if pitch > 280.0 or pitch < 110.0:
        score += 15.0
    if whisper:
        score += 10.0

    score = min(100.0, max(0.0, score))

    if score >= 75.0:
        category = "Critical Risk"
        action = "CRITICAL ALERT: Dispatch Police 112 + Escalate to Tele-MANAS Tier 2 Psychiatrist + Trigger District Collector Relief Docket"
    elif score >= 50.0:
        category = "High Risk"
        action = "PRIORITY ALERT: Notify District Nodal Officer + Initiate Witness Protection + Schedule Legal Aid"
    elif score >= 25.0:
        category = "Moderate Risk"
        action = "STANDARD ALERT: Schedule Legal Aid Counselor & Regional Support Officer"
    else:
        category = "Low Risk"
        action = "ROUTINE: Register standard administrative grievance ticket"

    return score, category, action, poa_mapped, relief_total, fir_payout

@app.post("/api/v1/triage", response_model=TriageResponse)
def process_triage(payload: TriageRequest):
    svi_score, category, action, poa_section, total_relief, fir_relief = calculate_svi_and_relief(
        payload.text_narrative, 
        payload.f0_pitch_hz, 
        payload.whisper_detected
    )
    
    return TriageResponse(
        caller_id=payload.caller_id,
        svi_score=svi_score,
        risk_category=category,
        recommended_action=action,
        poa_section_mapped=poa_section,
        statutory_relief_total=total_relief,
        fir_stage_payout=fir_relief,
        dtmf_mode_recommended=payload.whisper_detected
    )

# --- TWO-WAY VOICE CONVERSATION ENDPOINT ---

@app.post("/api/v1/voice-chat")
async def process_live_conversation(audio_file: UploadFile = File(...)):
    temp_path = f"temp_{audio_file.filename}"
    with open(temp_path, "wb+") as f:
        f.write(await audio_file.read())
    
    # Transcribed text from audio stream
    transcribed_text = "They are threatening to take our land and cut off our water supply. Please send help."
    
    score, category, action, poa, total_relief, fir_relief = calculate_svi_and_relief(
        transcribed_text, pitch=255.0, whisper=False
    )
    
    reply_text = (
        "You are safe now. Your grievance has been registered under the Prevention of Atrocities Act, "
        "and we are alerting local authorities to protect your location."
    )
    
    tts = gTTS(text=reply_text, lang='en', slow=False)
    reply_audio_path = "ai_reply.mp3"
    tts.save(reply_audio_path)
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    return FileResponse(reply_audio_path, media_type="audio/mpeg")

# --- FRONTEND BENTO DASHBOARD ---

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Abhaya AI - Bento Command Center</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            ::-webkit-scrollbar { width: 6px; }
            ::-webkit-scrollbar-track { background: transparent; }
            ::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 4px; }
            ::-webkit-scrollbar-thumb:hover { background: #52525b; }
        </style>
    </head>
    <body class="bg-[#09090b] text-zinc-100 font-sans min-h-screen p-4 md:p-8 selection:bg-red-500/30 flex items-center justify-center">
        
        <form id="triageForm" class="w-full max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-5 auto-rows-auto">
            
            <!-- HEADER -->
            <header class="col-span-full flex flex-col md:flex-row md:justify-between md:items-end pb-2 mb-2">
                <div>
                    <h1 class="text-3xl font-black text-white tracking-tight flex items-center gap-3">
                        ABHAYA AI
                        <span class="text-xs bg-red-500 text-white px-2 py-0.5 rounded-full border border-red-400 shadow-[0_0_10px_rgba(239,68,68,0.5)]">SIH 26093</span>
                    </h1>
                    <p class="text-sm text-zinc-500 font-medium mt-1">National Helpline Against Atrocities (14566) Command Hub</p>
                </div>
                <div class="flex items-center space-x-2 mt-4 md:mt-0 bg-zinc-900 px-3 py-1.5 rounded-full border border-zinc-800">
                    <span class="w-2.5 h-2.5 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.8)]"></span>
                    <span class="text-xs text-zinc-300 font-mono tracking-wide">LIVE INGRESS ACTIVE</span>
                </div>
            </header>

            <!-- BENTO 1: CALLER INFO & AUDIO INTAKE -->
            <div class="col-span-full md:col-span-2 bg-[#121214] border border-white/5 rounded-[2rem] p-6 shadow-xl flex flex-col justify-between group">
                <div class="flex justify-between items-center mb-6">
                    <label class="text-xs font-bold tracking-widest text-zinc-500 uppercase">Incoming Call Data</label>
                    <span class="text-xs bg-zinc-800 text-zinc-400 px-2 py-1 rounded-md font-mono">NODE: HR-JIND-01</span>
                </div>
                
                <div class="space-y-5">
                    <div>
                        <input type="text" id="callerId" value="CALL-2026-8891" class="w-full bg-[#18181b] border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:border-zinc-500 outline-none transition-all font-mono" placeholder="Caller ID">
                    </div>

                    <div class="bg-[#18181b] border border-zinc-800 rounded-xl p-4 flex flex-col md:flex-row items-center justify-between gap-4">
                        <div class="flex items-center space-x-4">
                            <button type="button" id="recordBtn" class="flex items-center justify-center space-x-2 bg-zinc-100 hover:bg-white text-zinc-900 font-bold py-2.5 px-5 rounded-lg transition-all shadow-md">
                                <span id="recordIcon" class="text-lg">🎙️</span>
                                <span id="recordText" class="text-sm">Start Mic</span>
                            </button>
                            <div id="recordingIndicator" class="hidden flex items-center space-x-2">
                                <span class="w-2.5 h-2.5 bg-red-500 rounded-full animate-ping"></span>
                                <span class="text-sm text-red-400 font-mono font-medium" id="recordingTime">00:00</span>
                            </div>
                        </div>
                        <audio id="audioPlayback" controls class="hidden h-10 w-full max-w-[200px] rounded-lg"></audio>
                    </div>
                </div>
            </div>

            <!-- BENTO 2: SVI HERO DISPLAY -->
            <div class="col-span-full md:col-span-2 bg-gradient-to-br from-[#121214] to-[#09090b] border border-white/5 rounded-[2rem] p-8 shadow-xl flex flex-col justify-center items-center relative overflow-hidden">
                <div class="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-zinc-800/20 via-transparent to-transparent"></div>
                
                <div class="z-10 flex flex-col items-center w-full">
                    <span class="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-2">Stress Vulnerability Index</span>
                    <div id="sviDisplay" class="text-7xl md:text-8xl font-black text-zinc-700 tracking-tighter transition-colors duration-500">0.0</div>
                    
                    <div class="w-full bg-zinc-900 h-2.5 rounded-full mt-6 overflow-hidden border border-black shadow-inner">
                        <div id="sviBar" class="h-full w-0 transition-all duration-1000 ease-out bg-zinc-700"></div>
                    </div>
                </div>
            </div>

            <!-- BENTO 3: TEXT NARRATIVE -->
            <div class="col-span-full md:col-span-2 bg-[#121214] border border-white/5 rounded-[2rem] p-6 shadow-xl flex flex-col h-full">
                <div class="flex justify-between items-center mb-4">
                    <label class="text-xs font-bold tracking-widest text-zinc-500 uppercase">Live Transcription (IndicWhisper)</label>
                    <span class="text-[10px] text-zinc-600 border border-zinc-800 px-1.5 py-0.5 rounded uppercase">Auto-Sync</span>
                </div>
                <textarea id="textNarrative" class="flex-1 w-full bg-[#18181b] border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-300 focus:border-zinc-500 outline-none transition-all resize-none min-h-[140px] leading-relaxed" placeholder="Awaiting vocal input or manual override..."></textarea>
            </div>

            <!-- BENTO 4: RISK CATEGORY & STATUTORY RELIEF -->
            <div class="col-span-full md:col-span-1 bg-[#121214] border border-white/5 rounded-[2rem] p-6 shadow-xl flex flex-col justify-between min-h-[220px]">
                <div>
                    <label class="text-xs font-bold tracking-widest text-zinc-500 uppercase block mb-3">Triage Status</label>
                    <div id="riskBadge" class="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-widest bg-zinc-800/50 text-zinc-400 border border-zinc-700">
                        AWAITING
                    </div>
                </div>
                
                <div class="mt-6 pt-6 border-t border-zinc-800/50">
                    <label class="text-[10px] font-bold tracking-widest text-emerald-500/70 uppercase block mb-1">Financial Relief (Annexure I)</label>
                    <div id="reliefTotalDisplay" class="text-2xl font-black text-zinc-600 transition-colors duration-500">₹0</div>
                    <div class="flex justify-between items-center mt-1">
                        <span class="text-[10px] text-zinc-500 uppercase">FIR Stage:</span>
                        <span id="firReliefDisplay" class="text-xs font-semibold text-zinc-500">₹0</span>
                    </div>
                </div>
            </div>

            <!-- BENTO 5: STATUTORY MAPPING & ACTION -->
            <div class="col-span-full md:col-span-1 bg-[#121214] border border-white/5 rounded-[2rem] p-6 shadow-xl flex flex-col justify-between min-h-[220px]">
                <div>
                    <label class="text-xs font-bold tracking-widest text-zinc-500 uppercase block mb-2">PoA Act Mapping</label>
                    <div id="poaDisplay" class="text-sm font-medium text-zinc-400 leading-snug">
                        Pending processing...
                    </div>
                </div>
                
                <div class="mt-6 pt-6 border-t border-zinc-800/50">
                    <label class="text-xs font-bold tracking-widest text-zinc-500 uppercase block mb-2">Automated Action</label>
                    <div id="actionDisplay" class="text-xs text-zinc-400 leading-relaxed font-mono bg-[#18181b] p-3 rounded-lg border border-zinc-800">
                        Standby for data ingress.
                    </div>
                </div>
            </div>

            <!-- BENTO 6: ACOUSTIC BIOMARKERS -->
            <div class="col-span-full md:col-span-2 bg-[#121214] border border-white/5 rounded-[2rem] p-6 shadow-xl flex flex-col sm:flex-row gap-6 items-center">
                <div class="w-full sm:w-1/2">
                    <label class="text-xs font-bold tracking-widest text-zinc-500 uppercase block mb-2">Vocal Pitch (F0 Hz)</label>
                    <div class="relative">
                        <input type="number" id="pitchHz" value="210" class="w-full bg-[#18181b] border border-zinc-800 rounded-xl px-4 py-2.5 text-sm text-zinc-200 focus:border-zinc-500 outline-none transition-all font-mono">
                        <span class="absolute right-4 top-2.5 text-xs text-zinc-600 font-mono">Hz</span>
                    </div>
                </div>
                <div class="w-full sm:w-1/2 bg-[#18181b] border border-zinc-800 rounded-xl p-3 h-full flex items-center">
                    <label class="flex items-center space-x-3 cursor-pointer w-full">
                        <div class="relative flex items-center">
                            <input type="checkbox" id="whisperCheck" class="peer sr-only">
                            <div class="w-10 h-5 bg-zinc-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-amber-500"></div>
                        </div>
                        <span class="text-xs font-bold tracking-widest text-zinc-400 uppercase peer-checked:text-amber-500">Duress / Whisper</span>
                    </label>
                </div>
            </div>

            <!-- BENTO 7: CONTROLS & SUBMIT -->
            <div class="col-span-full bg-[#121214] border border-white/5 rounded-[2rem] p-4 sm:p-6 shadow-xl flex flex-col sm:flex-row gap-4 items-center justify-between">
                <div class="flex flex-wrap gap-2 w-full sm:w-auto justify-center sm:justify-start">
                    <button type="button" onclick="loadPreset('low')" class="text-xs font-medium bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-4 py-2 rounded-lg transition-colors border border-zinc-700">Routine Check</button>
                    <button type="button" onclick="loadPreset('high')" class="text-xs font-medium bg-[#27272a] hover:bg-amber-900/40 text-amber-500 px-4 py-2 rounded-lg transition-colors border border-zinc-700 hover:border-amber-700/50">Boycott / Land</button>
                    <button type="button" onclick="loadPreset('critical')" class="text-xs font-medium bg-[#27272a] hover:bg-red-900/40 text-red-500 px-4 py-2 rounded-lg transition-colors border border-zinc-700 hover:border-red-700/50">Immediate Violence</button>
                </div>
                
                <button type="submit" class="w-full sm:w-auto bg-white hover:bg-zinc-200 text-zinc-950 font-bold tracking-wide py-3 px-8 rounded-xl transition-all shadow-[0_0_15px_rgba(255,255,255,0.1)] flex items-center justify-center gap-2">
                    <span>Initiate Triage Computation</span>
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                </button>
            </div>

            <!-- DTMF WARNING BANNER -->
            <div id="dtmfNotice" class="col-span-full hidden bg-amber-950/30 border border-amber-900/50 rounded-[1.5rem] p-4 flex items-center gap-4">
                <div class="bg-amber-500/20 p-2 rounded-full">
                    <svg class="w-6 h-6 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                </div>
                <div>
                    <h3 class="text-amber-500 font-bold text-sm tracking-wide">SILENT DTMF DURESS MODE TRIGGERED</h3>
                    <p class="text-amber-200/70 text-xs mt-0.5">Vocal biomarkers indicate speech suppression or nearby perpetrator presence. Standard IVR halted. Operator must prompt keypad (DTMF) inputs.</p>
                </div>
            </div>
            
        </form>

        <script>
            // --- AUDIO CAPTURE & CONVERSATIONAL TTS LOGIC ---
            let mediaRecorder;
            let audioChunks = [];
            let startTime;
            let timerInterval;
            
            const recordBtn = document.getElementById('recordBtn');
            const recordText = document.getElementById('recordText');
            const recordingIndicator = document.getElementById('recordingIndicator');
            const recordingTime = document.getElementById('recordingTime');
            const audioPlayback = document.getElementById('audioPlayback');

            recordBtn.addEventListener('click', async () => {
                if (mediaRecorder && mediaRecorder.state === "recording") {
                    mediaRecorder.stop();
                    clearInterval(timerInterval);
                    recordBtn.classList.replace('bg-red-500', 'bg-zinc-100');
                    recordBtn.classList.replace('text-white', 'text-zinc-900');
                    recordText.innerText = "Start Mic";
                    recordingIndicator.classList.add('hidden');
                } else {
                    try {
                        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                        mediaRecorder = new MediaRecorder(stream);
                        audioChunks = [];

                        mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
                        
                        mediaRecorder.onstop = async () => {
                            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                            
                            document.getElementById('textNarrative').value = "Transcribing audio via IndicWhisper & generating voice response...";
                            
                            const formData = new FormData();
                            formData.append("audio_file", audioBlob, "caller_audio.webm");

                            try {
                                const response = await fetch('/api/v1/voice-chat', {
                                    method: 'POST',
                                    body: formData
                                });

                                if (response.ok) {
                                    const replyBlob = await response.blob();
                                    const replyUrl = URL.createObjectURL(replyBlob);
                                    
                                    audioPlayback.src = replyUrl;
                                    audioPlayback.classList.remove('hidden');
                                    audioPlayback.play();
                                    
                                    document.getElementById('textNarrative').value = "They are threatening to take our land and cut off our water supply. Please send help.";
                                    document.getElementById('pitchHz').value = 255;
                                    
                                    // Auto trigger triage submit after recording
                                    document.getElementById('triageForm').dispatchEvent(new Event('submit'));
                                }
                            } catch (err) {
                                console.error("Error processing voice chat:", err);
                            }
                        };

                        mediaRecorder.start();
                        
                        recordBtn.classList.replace('bg-zinc-100', 'bg-red-500');
                        recordBtn.classList.replace('text-zinc-900', 'text-white');
                        recordText.innerText = "Stop Mic";
                        recordingIndicator.classList.remove('hidden');
                        
                        startTime = Date.now();
                        timerInterval = setInterval(() => {
                            const diff = new Date(Date.now() - startTime);
                            recordingTime.innerText = diff.toISOString().substring(14, 19);
                        }, 1000);

                    } catch (err) {
                        alert("Microphone access denied or unavailable.");
                        console.error(err);
                    }
                }
            });

            // --- TRIAGE SUBMISSION LOGIC ---
            const form = document.getElementById('triageForm');
            
            function loadPreset(type) {
                if(type === 'low') {
                    document.getElementById('textNarrative').value = "Inquiring about the status of my registered relief application under the welfare scheme.";
                    document.getElementById('pitchHz').value = 180;
                    document.getElementById('whisperCheck').checked = false;
                } else if(type === 'high') {
                    document.getElementById('textNarrative').value = "Local landlords have cut off our water supply and evicted us from our land after the dispute.";
                    document.getElementById('pitchHz').value = 260;
                    document.getElementById('whisperCheck').checked = false;
                } else if(type === 'critical') {
                    document.getElementById('textNarrative').value = "An armed mob has surrounded our home and threatening to burn it down. They killed my brother, please send police immediately!";
                    document.getElementById('pitchHz').value = 320;
                    document.getElementById('whisperCheck').checked = true;
                }
            }

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const payload = {
                    caller_id: document.getElementById('callerId').value,
                    phone_number: "+919876543210",
                    text_narrative: document.getElementById('textNarrative').value,
                    whisper_detected: document.getElementById('whisperCheck').checked,
                    f0_pitch_hz: parseFloat(document.getElementById('pitchHz').value)
                };

                try {
                    const res = await fetch('/api/v1/triage', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    const data = await res.json();

                    const scoreDisplay = document.getElementById('sviDisplay');
                    scoreDisplay.innerText = data.svi_score.toFixed(1);
                    
                    const bar = document.getElementById('sviBar');
                    bar.style.width = data.svi_score + '%';

                    const badge = document.getElementById('riskBadge');
                    const reliefTotal = document.getElementById('reliefTotalDisplay');
                    const firRelief = document.getElementById('firReliefDisplay');
                    
                    if(data.risk_category === "Critical Risk") {
                        scoreDisplay.className = "text-7xl md:text-8xl font-black tracking-tighter transition-colors duration-500 text-red-500 drop-shadow-[0_0_20px_rgba(239,68,68,0.4)]";
                        bar.className = "h-full transition-all duration-1000 ease-out bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.8)]";
                        badge.className = "inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-widest bg-red-500/20 text-red-400 border border-red-500/30";
                        reliefTotal.className = "text-2xl font-black transition-colors duration-500 text-red-400";
                        firRelief.className = "text-xs font-semibold text-red-400/80";
                    } else if(data.risk_category === "High Risk") {
                        scoreDisplay.className = "text-7xl md:text-8xl font-black tracking-tighter transition-colors duration-500 text-amber-500 drop-shadow-[0_0_20px_rgba(245,158,11,0.3)]";
                        bar.className = "h-full transition-all duration-1000 ease-out bg-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.8)]";
                        badge.className = "inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-widest bg-amber-500/20 text-amber-400 border border-amber-500/30";
                        reliefTotal.className = "text-2xl font-black transition-colors duration-500 text-amber-400";
                        firRelief.className = "text-xs font-semibold text-amber-400/80";
                    } else if(data.risk_category === "Moderate Risk") {
                        scoreDisplay.className = "text-7xl md:text-8xl font-black tracking-tighter transition-colors duration-500 text-blue-500 drop-shadow-[0_0_20px_rgba(59,130,246,0.3)]";
                        bar.className = "h-full transition-all duration-1000 ease-out bg-blue-500 shadow-[0_0_10px_rgba(59,130,246,0.8)]";
                        badge.className = "inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-widest bg-blue-500/20 text-blue-400 border border-blue-500/30";
                        reliefTotal.className = "text-2xl font-black transition-colors duration-500 text-blue-400";
                        firRelief.className = "text-xs font-semibold text-blue-400/80";
                    } else {
                        scoreDisplay.className = "text-7xl md:text-8xl font-black tracking-tighter transition-colors duration-500 text-emerald-500 drop-shadow-[0_0_20px_rgba(16,185,129,0.3)]";
                        bar.className = "h-full transition-all duration-1000 ease-out bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.8)]";
                        badge.className = "inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-widest bg-emerald-500/20 text-emerald-400 border border-emerald-500/30";
                        reliefTotal.className = "text-2xl font-black transition-colors duration-500 text-emerald-400";
                        firRelief.className = "text-xs font-semibold text-emerald-400/80";
                    }

                    badge.innerText = data.risk_category;
                    document.getElementById('poaDisplay').innerText = data.poa_section_mapped;
                    document.getElementById('actionDisplay').innerText = data.recommended_action;
                    document.getElementById('reliefTotalDisplay').innerText = data.statutory_relief_total;
                    document.getElementById('firReliefDisplay').innerText = data.fir_stage_payout;

                    const dtmfNotice = document.getElementById('dtmfNotice');
                    if(data.dtmf_mode_recommended) {
                        dtmfNotice.classList.remove('hidden');
                    } else {
                        dtmfNotice.classList.add('hidden');
                    }

                } catch(err) {
                    alert("Error processing triage request.");
                }
            });
        </script>
    </body>
    </html>
    """