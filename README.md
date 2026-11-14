# 🔥 NovaMind AI — Flame in Freefall

**NASA Space Apps Challenge 2026 — Interactive microgravity combustion dashboard**

Fire behaves differently in microgravity than on Earth. NovaMind AI turns NASA's
[PSI-69 Flame Extinguishment Experiment (FLEX)](https://psi.nasa.gov/)
data into accessible, evidence-based fire-safety insight.

---

## 🚀 Quick start

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/novamind-flame.git
cd novamind-flame

# 2. Virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows PowerShell
# source venv/bin/activate    # macOS/Linux

# 3. Install
python -m pip install -r requirements.txt

# 4. Generate the NASA FLEX dataset (275 experiments)
python scripts/prepare_data.py

# 5. Launch
streamlit run app.py