async function sendDouble() {
    const value = parseInt(document.getElementById("inputNumber").value);
    const res = await fetch("/api/double", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value })
    });
    const data = await res.json();
    document.getElementById("result").innerText = `Resultado: ${data.result}`;
  }