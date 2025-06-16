import React, { useEffect, useState } from "react";

const API_URL = "http://localhost:5000/logs";
const API_KEY = "your_local_api_key";  // Replace with .env logic later

function App() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    fetch(API_URL, {
      headers: {
        Authorization: "Basic " + btoa(`admin:${API_KEY}`)
      }
    })
      .then(res => res.json())
      .then(data => setLogs(data.data || []))
      .catch(err => console.error("Error fetching logs:", err));
  }, []);

  return (
    <div>
      <h1>DNS Logs</h1>
      <table border="1" cellPadding="5">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Domain</th>
            <th>Action</th>
            <th>Device</th>
          </tr>
        </thead>
        <tbody>
          {logs.map(log => (
            <tr key={log.id}>
              <td>{log.timestamp}</td>
              <td>{log.domain}</td>
              <td>{log.action}</td>
              <td>{log.device}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default App;
