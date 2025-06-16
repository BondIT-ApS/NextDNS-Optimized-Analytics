import React, { useEffect, useState } from 'react';

export default function LogTableClient() {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const LOCAL_API_KEY = import.meta.env.PUBLIC_LOCAL_API_KEY;
    const AUTH_HEADER = 'Basic ' + btoa(`admin:${LOCAL_API_KEY}`);

    fetch("/api/logs", {
      headers: {
        Authorization: AUTH_HEADER,
      },
    })
      .then((res) => res.json())
      .then((data) => setLogs(data.data || []))
      .catch((err) => {
        console.error("Failed to load logs", err);
      });
  }, []);

  return (
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
        {logs.length === 0 ? (
          <tr>
            <td colSpan="5">Loading...</td>
          </tr>
        ) : (
          logs.map((log) => (
            <tr key={log.id}>
              <td>{log.id}</td>
              <td>{log.timestamp}</td>
              <td>{log.domain}</td>
              <td>{log.action}</td>
              <td>{log.device}</td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  );
}
