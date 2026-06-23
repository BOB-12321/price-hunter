// Price Hunter — landing page behaviour.
// Phase 1: healthcheck ping + version display.
// Later phases will replace this with the basket / hunt / store-management UI.

(() => {
  const dot = document.getElementById("health-dot");
  const text = document.getElementById("health-text");
  const version = document.getElementById("version-text");

  async function ping() {
    try {
      const res = await fetch("/healthz", { cache: "no-store" });
      if (!res.ok) throw new Error("status " + res.status);
      const data = await res.json();
      dot.className = "dot dot-green";
      text.textContent = "Service is up";
      version.textContent = `v${data.version} · ${data.env}`;
    } catch (err) {
      dot.className = "dot dot-red";
      text.textContent = "Service is unreachable";
      version.textContent = String(err);
    }
  }

  ping();
  // Refresh every 30s so a quick glance stays current.
  setInterval(ping, 30_000);
})();
