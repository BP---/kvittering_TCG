"""
TCG Receipt Generator - Web Server

FastAPI server intended to run on a Raspberry Pi on a closed local network.
Laptops connected via ethernet can open the Pi's IP in a browser to:
  - print arbitrary text on the thermal printer
  - trigger the TCG receipt flow (random person + photo + print + DB record)

Usage:
    uvicorn webapp:app --host 0.0.0.0 --port 80
    # or simply:
    python webapp.py
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import receipt_core

app = FastAPI(title="TCG Receipt Generator")


class PrintTextRequest(BaseModel):
    text: str


class ReceiptRequest(BaseModel):
    testing: bool = False


INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TCG Receipt Generator</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    font-family: system-ui, sans-serif;
    background: #1a1a2e;
    color: #eee;
    margin: 0;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 2rem 1rem;
  }
  .card {
    background: #16213e;
    border-radius: 12px;
    padding: 2rem;
    width: 100%;
    max-width: 480px;
    box-shadow: 0 4px 24px rgba(0,0,0,.4);
  }
  h1 { margin-top: 0; font-size: 1.4rem; text-align: center; }
  h2 { font-size: 1rem; margin: 1.5rem 0 .5rem; border-top: 1px solid #2a3b5e; padding-top: 1.5rem; }
  textarea {
    width: 100%;
    min-height: 110px;
    border-radius: 8px;
    border: 1px solid #2a3b5e;
    background: #0f1729;
    color: #eee;
    padding: .75rem;
    font-size: 1rem;
    resize: vertical;
  }
  button {
    width: 100%;
    margin-top: .75rem;
    padding: .9rem;
    font-size: 1.05rem;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    color: #fff;
  }
  button:disabled { opacity: .5; cursor: wait; }
  #print-btn { background: #0f6e4f; }
  #print-btn:hover:not(:disabled) { background: #12835e; }
  #receipt-btn { background: #7b2cbf; }
  #receipt-btn:hover:not(:disabled) { background: #9143d6; }
  #status {
    margin-top: 1.25rem;
    padding: .75rem;
    border-radius: 8px;
    text-align: center;
    min-height: 1.2em;
    white-space: pre-wrap;
  }
  #status.ok { background: #103b2a; color: #7be0b0; }
  #status.err { background: #3b1020; color: #ff8fa3; }
  #status.busy { background: #2a2a45; color: #b8b8e0; }
</style>
</head>
<body>
<div class="card">
  <h1>🖨️ TCG Receipt Generator</h1>

  <h2 style="border:none;padding-top:0;margin-top:0">Print text</h2>
  <textarea id="text-input" placeholder="Write something to print..."></textarea>
  <button id="print-btn">Print</button>

  <h2>Receipt TCG</h2>
  <button id="receipt-btn">🎴 Generate TCG Receipt</button>

  <div id="status"></div>
</div>

<script>
const statusEl = document.getElementById('status');
const printBtn = document.getElementById('print-btn');
const receiptBtn = document.getElementById('receipt-btn');
const textInput = document.getElementById('text-input');

function setStatus(msg, cls) {
  statusEl.textContent = msg;
  statusEl.className = cls || '';
}

function setBusy(busy) {
  printBtn.disabled = busy;
  receiptBtn.disabled = busy;
}

async function post(url, body) {
  setBusy(true);
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body || {})
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    return data;
  } finally {
    setBusy(false);
  }
}

printBtn.addEventListener('click', async () => {
  const text = textInput.value.trim();
  if (!text) { setStatus('Write some text first.', 'err'); return; }
  setStatus('Printing...', 'busy');
  try {
    await post('/api/print-text', {text});
    setStatus('Printed! ✓', 'ok');
    textInput.value = '';
  } catch (e) {
    setStatus('Error: ' + e.message, 'err');
  }
});

receiptBtn.addEventListener('click', async () => {
  setStatus('Generating receipt (taking photo + printing)...', 'busy');
  try {
    const data = await post('/api/receipt');
    setStatus(`Receipt printed! ✓\\n${data.name} (Rarity: ${data.rarity})`, 'ok');
  } catch (e) {
    setStatus('Error: ' + e.message, 'err');
  }
});
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def index():
    return INDEX_HTML


@app.post("/api/print-text")
def print_text(req: PrintTextRequest):
    """Print arbitrary text on the thermal printer."""
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is empty.")
    try:
        receipt_core.print_free_text(text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "printed"}


@app.post("/api/receipt")
def generate_receipt(req: ReceiptRequest = ReceiptRequest()):
    """Run the TCG receipt flow: random person + photo + print + DB record."""
    try:
        result = receipt_core.generate_receipt(testing=req.testing)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "printed", **result}


@app.get("/api/health")
def health():
    """Report what hardware/services are available."""
    from getRandomPerson import check_pocketbase_connection
    return {
        "printer_available": receipt_core.PRINTER_AVAILABLE,
        "camera_available": receipt_core.CAMERA_AVAILABLE,
        "database_connected": check_pocketbase_connection(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
