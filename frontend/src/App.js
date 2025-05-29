import React, { useState, useEffect } from "react";
const API_URL = "http://localhost:5000/api";

function App() {
  const [prompts, setPrompts] = useState([]);
  const [promptValue, setPromptValue] = useState("");
  const [promptText, setPromptText] = useState("");
  const [text, setText] = useState("");
  const [openaiKey, setOpenaiKey] = useState("");
  const [compliantKey, setCompliantKey] = useState("");
  const [output, setOutput] = useState("");
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/prompts`)
      .then((res) => res.json())
      .then(setPrompts);
  }, []);

  // Fetch full prompt text by value
  const handlePromptSelect = async (e) => {
    const value = e.target.value;
    setPromptValue(value);
    if (value) {
      const res = await fetch(`${API_URL}/get-prompt-template`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value }),
      });
      const data = await res.json();
      setPromptText(data.prompt);
    } else {
      setPromptText("");
    }
  };

  // Handle prompt file upload (txt or pdf)
  const handlePromptUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.type === "application/pdf") {
      // Use PDF.js or pdf-parse in backend for true PDF, but here we'll just alert.
      alert("For production, use backend to extract PDF text. For now, please upload .txt file.");
      return;
    }
    // For .txt files
    const reader = new FileReader();
    reader.onload = (evt) => setPromptText(evt.target.result);
    reader.readAsText(file);
  };

  const handleStoreKeys = async () => {
    await fetch(`${API_URL}/store-keys`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ openai_key: openaiKey, compliant_key: compliantKey }),
    });
    setLoggedIn(true);
  };

  const handleProcess = async () => {
    const res = await fetch(`${API_URL}/process`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: promptText, text }),
    });
    const data = await res.json();
    setOutput(data.output || data.error);
  };

  const handleLogout = async () => {
    await fetch(`${API_URL}/logout`, {
      method: "POST",
      credentials: "include",
    });
    setLoggedIn(false);
    setOpenaiKey("");
    setCompliantKey("");
    setOutput("");
    setPromptText("");
    setPromptValue("");
  };

  if (!loggedIn) {
    return (
      <div style={{ maxWidth: 400, margin: "auto", marginTop: 80 }}>
        <h2>Enter API Keys</h2>
        <input type="password" placeholder="OpenAI API Key" value={openaiKey} onChange={(e) => setOpenaiKey(e.target.value)} />
        <br />
        <br />
        <input type="password" placeholder="CompliantGPT API Key" value={compliantKey} onChange={(e) => setCompliantKey(e.target.value)} />
        <br />
        <br />
        <button onClick={handleStoreKeys} disabled={!openaiKey || !compliantKey}>
          Continue
        </button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 800, margin: "auto", marginTop: 40 }}>
      <h2>Prompt Processor MVP</h2>
      <label>
        Select Prompt:&nbsp;
        <select value={promptValue} onChange={handlePromptSelect}>
          <option value="">-- Select --</option>
          {prompts.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
      </label>
      &nbsp;or&nbsp;
      <label>
        Upload Prompt:
        <input type="file" accept=".txt" onChange={handlePromptUpload} />
      </label>
      <br />
      <br />
      <textarea
        placeholder="System prompt will appear here..."
        value={promptText}
        onChange={(e) => setPromptText(e.target.value)}
        rows={12}
        cols={90}
      ></textarea>
      <br />
      <textarea
        placeholder="Paste medical text here..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={5}
        cols={90}
      ></textarea>
      <br />
      <button onClick={handleProcess} disabled={!promptText || !text}>
        Generate
      </button>
      <button style={{ marginLeft: 16 }} onClick={handleLogout}>
        Logout
      </button>
      <br />
      <br />
      <textarea readOnly value={output} rows={12} cols={90} />
      <br />
      <button onClick={() => navigator.clipboard.writeText(output)} disabled={!output}>
        Copy to Clipboard
      </button>
    </div>
  );
}

export default App;
