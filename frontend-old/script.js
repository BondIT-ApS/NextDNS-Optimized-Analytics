const LOCAL_API_KEY = '__LOCAL_API_KEY__';  // Will be replaced by Docker or entrypoint
const API_URL = '/api/logs';

document.addEventListener('DOMContentLoaded', () => {
    fetchLogs();
});

function fetchLogs() {
    fetch(API_URL, {
        headers: {
            Authorization: 'Basic ' + btoa('admin:' + LOCAL_API_KEY)
        }
    })
    .then(res => res.json())
    .then(data => {
        const tbody = document.querySelector('#logs-table tbody');
        tbody.innerHTML = '';
        if (!data || !data.data || data.data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5">No data found</td></tr>';
            return;
        }
        data.data.forEach(log => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${log.id}</td>
                <td>${log.timestamp}</td>
                <td>${log.domain}</td>
                <td>${log.action}</td>
                <td>${log.device}</td>
            `;
            tbody.appendChild(row);
        });
    })
    .catch(err => {
        console.error('Failed to load logs:', err);
        const tbody = document.querySelector('#logs-table tbody');
        tbody.innerHTML = '<tr><td colspan="5">Error loading logs</td></tr>';
    });
}
