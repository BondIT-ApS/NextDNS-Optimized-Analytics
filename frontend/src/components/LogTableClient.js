const LOCAL_API_KEY = import.meta.env.PUBLIC_LOCAL_API_KEY;
const AUTH_HEADER = "Basic " + btoa(`admin:${LOCAL_API_KEY}`);

fetch("/api/logs", {
  headers: {
    Authorization: AUTH_HEADER,
  },
})
  .then((res) => res.json())
  .then((data) => {
    const logs = data.data || [];
    const root = document.getElementById("log-table-root");
    root.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Timestamp</th>
            <th>Domain</th>
            <th>Action</th>
            <th>Device</th>
          </tr>
        </thead>
        <tbody>
          ${logs
            .map(
              (log) => `
            <tr>
              <td>${log.id}</td>
              <td>${log.timestamp}</td>
              <td>${log.domain}</td>
              <td>${log.action}</td>
              <td>${log.device}</td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    `;
  })
  .catch((err) => {
    console.error("Failed to load logs", err);
    document.getElementById("log-table-root").textContent =
      "Error loading logs.";
  });
