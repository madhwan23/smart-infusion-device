from ai_model import InfusionAIPredictor
ai = InfusionAIPredictor()
from flask import Flask, render_template_string
import random
import sqlite3
import numpy as np
from sklearn.linear_model import LinearRegression

app = Flask(__name__)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device TEXT,
            value INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- AI ----------------
def predict(values):
    if len(values) < 5:
        return None
    X = np.array(range(len(values))).reshape(-1, 1)
    y = np.array(values)
    model = LinearRegression()
    model.fit(X, y)
    future = len(values) + 5
    return model.predict([[future]])[0]

def estimate_time_to_empty(values):
    if len(values) < 5:
        return None
    diffs = np.diff(values)
    avg_drop = abs(np.mean(diffs))
    if avg_drop == 0:
        return None
    return int(values[-1] / avg_drop)

# ---------------- DEVICES ----------------
devices = ["Bed-1", "Bed-2", "Bed-3"]

# ---------------- UI ----------------
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Infusion Monitoring System</title>
<meta http-equiv="refresh" content="3">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
body {
    margin: 0;
    font-family: system-ui;
    background: #0b0f14;
    color: #e6edf3;
}

.header {
    padding: 18px 30px;
    border-bottom: 1px solid #1f2933;
    font-size: 20px;
    font-weight: 600;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 20px;
    padding: 25px;
}

.card {
    background: #11161c;
    border: 1px solid #1f2933;
    border-radius: 10px;
    padding: 18px;
}

.title {
    font-size: 15px;
    color: #9aa4af;
    margin-bottom: 10px;
}

.value {
    font-size: 22px;
    font-weight: 600;
}

.small {
    font-size: 14px;
    color: #9aa4af;
    margin-bottom: 5px;
}

.status {
    margin-top: 8px;
    font-size: 13px;
    padding: 4px 10px;
    border-radius: 6px;
    display: inline-block;
}

.ok { background: rgba(34,197,94,0.15); color: #22c55e; }
.warn { background: rgba(245,158,11,0.15); color: #f59e0b; }
.crit { background: rgba(239,68,68,0.15); color: #ef4444; }

canvas {
    margin-top: 12px;
}

.footer {
    text-align: center;
    font-size: 12px;
    color: #6b7280;
    padding: 15px;
}
</style>
</head>

<body>

<div class="header">
Infusion Monitoring Dashboard
</div>

<div class="grid">

{% for d in devices %}
<div class="card">

    <div class="title">{{d}}</div>

    <div class="value">Level: {{data[d]['level']}}</div>
    <div class="small">Prediction: {{data[d]['prediction']}}</div>
    <div class="small">Time to Empty: {{data[d]['time']}}</div>

    <div class="status
    {% if data[d]['level'] > 150 %} ok
    {% elif data[d]['level'] > 80 %} warn
    {% else %} crit
    {% endif %}">
        {% if data[d]['level'] > 150 %}
            Stable
        {% elif data[d]['level'] > 80 %}
            Attention Needed
        {% else %}
            Critical - Replace
        {% endif %}
    </div>

    <canvas id="chart_{{loop.index}}"></canvas>

    <script>
    new Chart(document.getElementById('chart_{{loop.index}}'), {
        type: 'line',
        data: {
            labels: {{data[d]['history_idx']}},
            datasets: [
                {
                    data: {{data[d]['history']}},
                    borderColor: '#3b82f6',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.3
                },
                {
                    data: Array({{data[d]['history']|length}}).fill(80),
                    borderColor: '#ef4444',
                    borderDash: [5,5],
                    pointRadius: 0
                }
            ]
        },
        options: {
            plugins: { legend: { display: false }},
            scales: {
                x: { display: false },
                y: { grid: { color: '#1f2933' } }
            }
        }
    });
    </script>

</div>
{% endfor %}

</div>

<div class="footer">
AI prediction • Real-time monitoring • Clinical prototype
</div>

</body>
</html>
"""

# ---------------- ROUTE ----------------
@app.route('/')
def home():
    result = {}

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    for d in devices:

        c.execute("SELECT value FROM readings WHERE device=? ORDER BY id DESC LIMIT 1", (d,))
        last = c.fetchone()

        if last:
            value = max(0, last[0] - random.randint(5, 12))
        else:
            value = random.randint(420, 500)

        c.execute("INSERT INTO readings (device, value) VALUES (?,?)", (d, value))
        conn.commit()

        c.execute("SELECT value FROM readings WHERE device=? ORDER BY id DESC LIMIT 15", (d,))
        rows = c.fetchall()
        history = [r[0] for r in rows][::-1]

        prediction = ai.predict_future_level(history)
        time_left = ai.estimate_time_to_empty(history)

        result[d] = {
            "level": value,
            "prediction": round(prediction,2) if prediction else "Calculating",
            "time": f"{time_left} sec" if time_left else "Estimating",
            "history": history,
            "history_idx": list(range(len(history)))
        }

    conn.close()

    return render_template_string(HTML, devices=devices, data=result)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)