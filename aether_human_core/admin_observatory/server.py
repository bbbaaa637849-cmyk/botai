"""
Admin Observatory Server: FastAPI & WebSockets Live Brain Telemetry Dashboard.
Provides real-time visualization of endocrine hormones, social constraints,
inner monologue stream of consciousness, affinity matrices, and simulated chat testing.
"""

from __future__ import annotations

import logging
import asyncio
import json
from typing import Dict, Any, List, Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from aether_human_core.config.settings import settings
from aether_human_core.psychology_engine.neuro_hormones import endocrine_engine
from aether_human_core.psychology_engine.circadian_rhythm import circadian_engine
from aether_human_core.psychology_engine.social_influence import SocialConstraintCompiler
from aether_human_core.psychology_engine.affinity_matrix import UserAffinityVector, RelationshipTier
from aether_human_core.cognitive_engine.orchestrator import cognitive_orchestrator
from aether_human_core.database.postgres.connection import db_manager
from aether_human_core.database.postgres.repositories.user_repo import UserRepository
from aether_human_core.database.postgres.repositories.behavioral_rule_repo import BehavioralRuleRepository

logger = logging.getLogger("Aether.Observatory")

app = FastAPI(
    title="Aether-Human Admin Observatory",
    description="Real-Time Cognitive Telemetry & Sentient Brain Introspection",
    version="1.0.0",
)


class ActiveWebsocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.active_connections.discard(d)


ws_manager = ActiveWebsocketManager()


class ChatSimulateRequest(BaseModel):
    sender_id: int = 12345678
    sender_name: str = "سارة"
    sender_gender: str = "female"
    chat_type: str = "private"  # private or supergroup
    chat_title: str = "خاص"
    message_text: str = "عمر وحشتني أوي، إنت فين دلوقتي؟"


@app.get("/api/telemetry")
async def get_system_telemetry() -> Dict[str, Any]:
    """
    Returns unified psychological and operational state of Omar's brain.
    """
    hormones = endocrine_engine.evaluate_psychological_mood()
    circadian = circadian_engine.evaluate_circadian_state()

    async with db_manager.session() as session:
        user_repo = UserRepository(session)
        rule_repo = BehavioralRuleRepository(session)
        top_users = await user_repo.get_top_affinity_users(limit=10)
        active_rules = await rule_repo.get_active_rules()

    users_data = [
        {
            "id": u.telegram_id,
            "name": u.first_name,
            "affinity": round(u.affinity_score, 1),
            "trust": round(u.trust_score, 1),
            "romantic": round(u.romantic_attachment, 1),
            "tier": u.relationship_tier,
        }
        for u in top_users
    ]

    rules_data = [
        {
            "id": r.id,
            "commander_id": r.user_id,
            "rule_type": r.rule_type,
            "instruction": r.instruction_text,
            "target_gender": r.target_gender,
            "is_active": r.is_active,
        }
        for r in active_rules
    ]

    return {
        "status": "OPERATIONAL",
        "entity_name": "عمر (Omar)",
        "psychological_mood": hormones,
        "circadian_rhythm": circadian,
        "active_social_constraints": rules_data,
        "affinity_matrix": users_data,
    }


@app.post("/api/chat/simulate")
async def simulate_chat_interaction(req: ChatSimulateRequest) -> Dict[str, Any]:
    """
    Simulates an incoming Telegram chat event through the entire cognitive architecture.
    """
    resp = await cognitive_orchestrator.process_incoming_event(
        telegram_message_id=9999,
        chat_id=req.sender_id,
        sender_id=req.sender_id,
        sender_name=req.sender_name,
        message_text=req.message_text,
        sender_gender=req.sender_gender,
        chat_type=req.chat_type,
        chat_title=req.chat_title,
    )

    # Broadcast event to WebSockets
    await ws_manager.broadcast({
        "event": "CHAT_INTERACTION",
        "sender": req.sender_name,
        "message": req.message_text,
        "decision": resp.decision_type,
        "response": resp.raw_response_text,
        "inner_monologue": resp.inner_monologue_text,
        "is_cold": resp.is_cold_dismissal,
        "is_shy": resp.is_shy,
        "loyalty_reported": bool(resp.loyalty_partner_id),
    })

    return {
        "decision_type": resp.decision_type,
        "raw_response_text": resp.raw_response_text,
        "reaction_emoji": resp.reaction_emoji,
        "is_shy": resp.is_shy,
        "is_cold_dismissal": resp.is_cold_dismissal,
        "loyalty_partner_id": resp.loyalty_partner_id,
        "loyalty_report_message": resp.loyalty_report_message,
        "inner_monologue": resp.inner_monologue_text,
    }


@app.websocket("/ws/stream")
async def websocket_cognitive_stream(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Heartbeat telemetry push
            data = await get_system_telemetry()
            await websocket.send_json({"event": "TELEMETRY_HEARTBEAT", "data": data})
            await asyncio.sleep(3.0)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.get("/", response_class=HTMLResponse)
async def serve_observatory_dashboard() -> str:
    """
    Serves rich, state-of-the-art dark themed real-time UI dashboard.
    """
    html_content = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AETHER-HUMAN | مرصد العقل البشري الاصطناعي</title>
  <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #0a0d14;
      --card-bg: #121824;
      --border-color: #202b3c;
      --primary: #00d2ff;
      --accent: #ff2a6d;
      --dopamine: #ffd166;
      --oxytocin: #ef476f;
      --cortisol: #06d6a0;
      --serotonin: #118ab2;
      --text: #e6edf3;
      --text-muted: #8b949e;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg-dark);
      color: var(--text);
      font-family: 'Cairo', sans-serif;
      padding: 24px;
      line-height: 1.6;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border-color);
      margin-bottom: 24px;
    }
    .brand { font-size: 26px; font-weight: 900; color: var(--primary); letter-spacing: 1px; }
    .badge {
      background: rgba(0, 210, 255, 0.15);
      color: var(--primary);
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 700;
      border: 1px solid var(--primary);
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 20px;
      margin-bottom: 24px;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border-color);
      border-radius: 14px;
      padding: 20px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    }
    .card-title {
      font-size: 17px;
      font-weight: 700;
      color: var(--text);
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
      border-bottom: 1px solid var(--border-color);
      padding-bottom: 8px;
    }
    .metric-row {
      display: flex;
      justify-content: space-between;
      margin-bottom: 12px;
      font-size: 14px;
    }
    .progress-bar {
      height: 8px;
      background: #1c2433;
      border-radius: 4px;
      overflow: hidden;
      margin-bottom: 12px;
    }
    .progress-fill { height: 100%; transition: width 0.4s ease; }
    .fill-dopamine { background: var(--dopamine); }
    .fill-oxytocin { background: var(--oxytocin); }
    .fill-cortisol { background: var(--cortisol); }
    .fill-serotonin { background: var(--serotonin); }
    .chat-simulator {
      grid-column: 1 / -1;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    input, textarea, select, button {
      width: 100%;
      background: #0d121c;
      border: 1px solid var(--border-color);
      color: var(--text);
      padding: 10px 14px;
      border-radius: 8px;
      font-family: inherit;
      font-size: 14px;
      margin-bottom: 12px;
    }
    input:focus, textarea:focus { outline: none; border-color: var(--primary); }
    button {
      background: var(--primary);
      color: #000;
      font-weight: 700;
      cursor: pointer;
      border: none;
      transition: opacity 0.2s;
    }
    button:hover { opacity: 0.9; }
    .stream-box {
      background: #090c12;
      border: 1px solid var(--border-color);
      border-radius: 8px;
      padding: 14px;
      height: 280px;
      overflow-y: auto;
      font-size: 13px;
    }
    .stream-entry {
      border-bottom: 1px solid rgba(255,255,255,0.06);
      padding-bottom: 10px;
      margin-bottom: 10px;
    }
    .stream-tag { font-size: 11px; padding: 2px 6px; border-radius: 4px; margin-left: 6px; }
    .tag-monologue { background: rgba(255, 42, 109, 0.2); color: var(--accent); }
    .tag-reply { background: rgba(0, 210, 255, 0.2); color: var(--primary); }
  </style>
</head>
<body>
  <header>
    <div>
      <div class="brand">PROJECT AETHER-HUMAN</div>
      <div style="font-size: 13px; color: var(--text-muted);">مرصد الحالة النفسية والوعي الذاتي للبوت "عمر"</div>
    </div>
    <div class="badge" id="live-status">● متصل بالوعي الحي</div>
  </header>

  <div class="grid">
    <!-- Endocrine Hormones -->
    <div class="card">
      <div class="card-title">🧬 الهرمونات الرقمية والحالة النفسية</div>
      <div class="metric-row">
        <span>الدوبامين (الحماس/الفرح):</span>
        <span id="dopamine-val" style="color:var(--dopamine)">0.55</span>
      </div>
      <div class="progress-bar"><div id="dopamine-fill" class="progress-fill fill-dopamine" style="width: 55%"></div></div>

      <div class="metric-row">
        <span>الأوكسيتوسين (الدفء/القرب):</span>
        <span id="oxytocin-val" style="color:var(--oxytocin)">0.50</span>
      </div>
      <div class="progress-bar"><div id="oxytocin-fill" class="progress-fill fill-oxytocin" style="width: 50%"></div></div>

      <div class="metric-row">
        <span>الكورتيزول (التوتر/الزعل):</span>
        <span id="cortisol-val" style="color:var(--cortisol)">0.15</span>
      </div>
      <div class="progress-bar"><div id="cortisol-fill" class="progress-fill fill-cortisol" style="width: 15%"></div></div>

      <div class="metric-row">
        <span>السيروتونين (الاستقرار):</span>
        <span id="serotonin-val" style="color:var(--serotonin)">0.60</span>
      </div>
      <div class="progress-bar"><div id="serotonin-fill" class="progress-fill fill-serotonin" style="width: 60%"></div></div>

      <div style="margin-top: 14px; font-weight: 700; color: var(--primary);">
        المزاج الحالي: <span id="mood-label">رايق ومستقر</span>
      </div>
    </div>

    <!-- Circadian Rhythm -->
    <div class="card">
      <div class="card-title">⏰ الساعة البيولوجية وحياة عمر</div>
      <div class="metric-row">
        <span>توقيت القاهرة الحالي:</span>
        <span id="cairo-time">--:--:--</span>
      </div>
      <div class="metric-row">
        <span>الحالة البيولوجية:</span>
        <span id="bio-state" style="font-weight: 700; color: #00d2ff;">نشاط كامل</span>
      </div>
      <div class="metric-row">
        <span>معامل الأخطاء الإملائية:</span>
        <span id="typo-mult">1.0x</span>
      </div>
      <div class="metric-row">
        <span>سرعة الكتابة النسبية:</span>
        <span id="wpm-mult">1.0x</span>
      </div>
      <div id="bio-desc" style="font-size: 13px; color: var(--text-muted); margin-top: 10px;">
        في كامل نشاطه الطبيعي ومستعد للتواصل والشات.
      </div>
    </div>

    <!-- Active Constraints -->
    <div class="card">
      <div class="card-title">🛡️ القواعد السلوكية الفعالة (Social Constraints)</div>
      <div id="rules-list" style="font-size: 13px; color: var(--text-muted);">
        جاري فحص القيود السلوكية النشطة...
      </div>
    </div>
  </div>

  <!-- Chat Simulation & Cognitive Stream -->
  <div class="card chat-simulator">
    <div>
      <div class="card-title">💬 محاكي الرسائل واختبار العقل الباطن</div>
      <input type="text" id="sim-name" placeholder="اسم المتحدث (مثال: سارة / مريم / أحمد)" value="سارة">
      <select id="sim-gender">
        <option value="female" selected>أنثى (Female)</option>
        <option value="male">ذكر (Male)</option>
      </select>
      <select id="sim-chat-type">
        <option value="private" selected>محادثة خاصة (Private DM)</option>
        <option value="supergroup">جروب عام (Supergroup)</option>
      </select>
      <textarea id="sim-text" rows="3" placeholder="نص الرسالة التي تريد إرسالها لعمر...">عمر وحشتني أوي، إنت فين دلوقتي؟</textarea>
      <button onclick="triggerSimulate()">إرسال الرسالة ومشاهدة تفكير عمر ⚡</button>
    </div>

    <div>
      <div class="card-title">🧠 تيار الوعي والتفكير الباطن اللحظي (Stream)</div>
      <div class="stream-box" id="stream-box">
        <div class="stream-entry">
          <span class="stream-tag tag-monologue">النظام</span>
          <span style="color:var(--text-muted)">تم تفعيل مرصد التفكير المباشر بنجاح. أي محادثة واردة ستظهر هنا بتفاصيل التفكير الداخلي.</span>
        </div>
      </div>
    </div>
  </div>

  <script>
    async function refreshTelemetry() {
      try {
        const res = await fetch('/api/telemetry');
        const data = await res.json();
        const h = data.psychological_mood;
        const c = data.circadian_rhythm;

        document.getElementById('dopamine-val').textContent = h.dopamine;
        document.getElementById('dopamine-fill').style.width = (h.dopamine * 100) + '%';

        document.getElementById('oxytocin-val').textContent = h.oxytocin;
        document.getElementById('oxytocin-fill').style.width = (h.oxytocin * 100) + '%';

        document.getElementById('cortisol-val').textContent = h.cortisol;
        document.getElementById('cortisol-fill').style.width = (h.cortisol * 100) + '%';

        document.getElementById('serotonin-val').textContent = h.serotonin;
        document.getElementById('serotonin-fill').style.width = (h.serotonin * 100) + '%';

        document.getElementById('mood-label').textContent = h.mood_ar;
        document.getElementById('cairo-time').textContent = c.cairo_time_str;
        document.getElementById('bio-state').textContent = c.state_name;
        document.getElementById('bio-desc').textContent = c.description_ar;
        document.getElementById('typo-mult').textContent = c.typo_multiplier + 'x';
        document.getElementById('wpm-mult').textContent = c.wpm_multiplier + 'x';

        // Rules
        const rList = document.getElementById('rules-list');
        if (data.active_social_constraints.length === 0) {
          rList.innerHTML = '<span style="color:#06d6a0;">لا توجد قيود استثنائية مفروضة حالياً. البوت حر في تصرفاته.</span>';
        } else {
          rList.innerHTML = data.active_social_constraints.map(r => `
            <div style="padding:6px; background:#0a0d14; border-radius:6px; margin-bottom:6px; border-right:3px solid var(--accent)">
              <strong>${r.rule_type}</strong>: ${r.instruction} (أمر من المستخدم ${r.commander_id})
            </div>
          `).join('');
        }
      } catch (err) {
        console.error(err);
      }
    }

    async function triggerSimulate() {
      const name = document.getElementById('sim-name').value;
      const gender = document.getElementById('sim-gender').value;
      const chatType = document.getElementById('sim-chat-type').value;
      const text = document.getElementById('sim-text').value;

      const stream = document.getElementById('stream-box');
      stream.innerHTML += `
        <div class="stream-entry">
          <span class="stream-tag" style="background:#334">وارد من ${name}</span>
          <div>"${text}"</div>
        </div>
      `;
      stream.scrollTop = stream.scrollHeight;

      try {
        const res = await fetch('/api/chat/simulate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            sender_id: gender === 'female' ? 1001 : 1002,
            sender_name: name,
            sender_gender: gender,
            chat_type: chatType,
            message_text: text
          })
        });
        const out = await res.json();

        stream.innerHTML += `
          <div class="stream-entry">
            <span class="stream-tag tag-monologue">عقل عمر الباطن</span>
            <div style="color:var(--accent); font-style:italic;">"${out.inner_monologue}"</div>
            <div style="margin-top:6px;"><span class="stream-tag tag-reply">رد عمر النهائي</span> <strong>${out.raw_response_text}</strong></div>
            ${out.loyalty_report_message ? `<div style="margin-top:4px; color:#ffd166; font-size:12px;">🚨 وشاية للشريكة: ${out.loyalty_report_message}</div>` : ''}
          </div>
        `;
        stream.scrollTop = stream.scrollHeight;
        refreshTelemetry();
      } catch (e) {
        console.error(e);
      }
    }

    setInterval(refreshTelemetry, 5000);
    refreshTelemetry();
  </script>
</body>
</html>
"""
    return html_content
