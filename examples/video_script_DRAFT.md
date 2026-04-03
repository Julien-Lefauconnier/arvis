 SCRIPT VIDÉO EXEMPLES (TRÈS IMPORTANT)

👉 durée cible : **30–45 secondes**

---

## 🎥 SCÈNE 1 — HOOK (5 sec)

💻 Terminal :

```bash
python examples/01_basic_gate_refusal.py
```

🧠 Output :
```json
{
  "verdict": "REQUIRE_CONFIRMATION"
}
```

🎙️ narration :

    “This system refuses to answer.”

---

🎥 SCÈNE 2 — CONTRASTE (10 sec)

🎙️ narration :

    “Most AI systems always respond.
    ARVIS enforces stability before execution.”


---

🎥 SCÈNE 3 — DÉTERMINISME (10 sec)

```bash
python examples/02_replay_determinism.py
```

🧠 Output :
```text
Run 1: ...
Run 2: ...
✅ Deterministic behavior confirmed
```

🎙️ narration :

    “Same input. Same output. Every time.”

---

🎥 SCÈNE 4 — STABILITÉ (10 sec)

```bash
python examples/03_stability_vs_uncertainty.py
```

🎙️ narration :

    “It detects unstable or unsafe reasoning…”

---

🎥 SCÈNE 5 — CONCLUSION (5 sec)

🎙️ narration :

    “ARVIS is not an AI model.
    It’s a Cognitive Operating System.”