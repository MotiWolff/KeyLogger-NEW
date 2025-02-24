// Initialize toast
const toastEl = document.getElementById('alert-toast');
const toast = new bootstrap.Toast(toastEl);

// Get CSRF token from meta tag - move this inside DOMContentLoaded
let csrfToken;
let devices = [];
let isEncrypted = {};  // Store encryption state for each device

// Wrap all initialization code in DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token after DOM is loaded
    csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
    
    // Initial device refresh
    refreshDevices();
    
    // Set up periodic refresh
    setInterval(refreshDevices, 30000); // Update every 30 seconds
});

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

function updateDevicesList(devices) {
    const devicesList = document.getElementById('devices-list');
    const template = document.getElementById('device-template');
    devicesList.innerHTML = '';
    
    if (devices.length === 0) {
        devicesList.innerHTML = '<div class="alert alert-info">No Windows devices connected. Click "New Connection" to add a device.</div>';
        return;
    }
    
    devices.forEach(device => {
        const clone = template.content.cloneNode(true);
        const deviceItem = clone.querySelector('.device-item');
        
        // Set device ID as data attribute
        deviceItem.dataset.deviceId = device.id;
        
        // Update device information
        clone.querySelector('.device-id').textContent = `ID: ${device.id}`;
        clone.querySelector('.device-name-text').textContent = device.name || 'Unnamed Device';
        
        // Update status badge
        const statusBadge = clone.querySelector('.device-status');
        if (device.is_logging) {
            statusBadge.className = 'device-status badge bg-warning';
            statusBadge.textContent = 'Logging';
            // Update button states
            clone.querySelector('[onclick="startLogging(this)"]').disabled = true;
            clone.querySelector('[onclick="stopLogging(this)"]').disabled = false;
        } else if (device.is_active) {
            statusBadge.className = 'device-status badge bg-success';
            statusBadge.textContent = 'Connected';
        } else {
            statusBadge.className = 'device-status badge bg-secondary';
            statusBadge.textContent = 'Disconnected';
        }
        
        devicesList.appendChild(clone);
    });
}

async function toggleLogs(btn) {
    const deviceItem = btn.closest('.device-item');
    const deviceId = deviceItem.dataset.deviceId;
    const logsContainer = deviceItem.querySelector('.logs-container');
    const logsContent = logsContainer.querySelector('.logs-content');
    
    if (logsContainer.style.display === 'none') {
        try {
            const response = await fetch(`/api/logs/${deviceId}`, {
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            
            if (response.ok) {
                const logs = await response.json();
                if (logs.length > 0) {
                    logsContent.innerHTML = logs.join('<br>');
                } else {
                    logsContent.textContent = 'No logs available';
                }
                logsContainer.style.display = 'block';
                btn.innerHTML = '<i class="bi bi-eye-slash"></i> Hide Logs';
            } else {
                throw new Error('Failed to fetch logs');
            }
        } catch (error) {
            console.error('Error:', error);
            showAlert('Failed to fetch logs', 'danger');
        }
    } else {
        logsContainer.style.display = 'none';
        btn.innerHTML = '<i class="bi bi-eye"></i> View Logs';
    }
}

async function startLogging(btn) {
    const deviceId = btn.closest('.device-item').dataset.deviceId;
    try {
        const response = await fetch('/api/toggle_logging', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                device_id: deviceId,
                action: 'start'
            })
        });
        
        if (response.ok) {
            btn.disabled = true;
            btn.nextElementSibling.disabled = false;
            const statusBadge = btn.closest('.device-item').querySelector('.device-status');
            statusBadge.textContent = 'Logging';
            statusBadge.className = 'device-status badge bg-warning';
            showAlert('Logging started successfully', 'success');
        } else {
            throw new Error('Failed to start logging');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Failed to start logging', 'danger');
    }
}

async function stopLogging(btn) {
    const deviceId = btn.closest('.device-item').dataset.deviceId;
    try {
        const response = await fetch('/api/toggle_logging', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                device_id: deviceId,
                action: 'stop'
            })
        });
        
        if (response.ok) {
            btn.disabled = true;
            btn.previousElementSibling.disabled = false;
            const statusBadge = btn.closest('.device-item').querySelector('.device-status');
            statusBadge.textContent = 'Connected';
            statusBadge.className = 'device-status badge bg-success';
            showAlert('Logging stopped successfully', 'success');
        } else {
            throw new Error('Failed to stop logging');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Failed to stop logging', 'danger');
    }
}

async function removeDevice(btn) {
    const deviceItem = btn.closest('.device-item');
    const deviceId = deviceItem.dataset.deviceId;
    
    // Ask for confirmation
    if (!confirm('Are you sure you want to remove this device? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/remove_device', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                device_id: deviceId
            })
        });
        
        if (response.ok) {
            deviceItem.remove();
            showAlert('Device removed successfully', 'success');
            
            // Check if there are any devices left
            const devicesList = document.getElementById('devices-list');
            if (!devicesList.children.length) {
                devicesList.innerHTML = '<div class="alert alert-info">No Windows devices connected. Click "New Connection" to add a device.</div>';
            }
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to remove device');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Failed to remove device: ' + error.message, 'danger');
    }
}

async function toggleEncryption(btn) {
    const deviceId = btn.closest('.device-item').dataset.deviceId;
    try {
        const response = await fetch('/api/toggle_encryption', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                device_id: deviceId
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            const icon = btn.querySelector('i');
            if (data.is_encrypted) {
                icon.className = 'bi bi-lock-fill';
                btn.title = 'Encryption enabled';
            } else {
                icon.className = 'bi bi-unlock';
                btn.title = 'Encryption disabled';
            }
            showAlert(`Encryption ${data.is_encrypted ? 'enabled' : 'disabled'}`, 'success');
        } else {
            throw new Error('Failed to toggle encryption');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Failed to toggle encryption', 'danger');
    }
}

async function refreshDevices() {
    try {
        const response = await fetch('/api/devices?type=windows', {
            headers: {
                'X-CSRFToken': csrfToken
            }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const devices = await response.json();
        updateDevicesList(devices);
    } catch (error) {
        console.error('Error fetching devices:', error);
        const devicesList = document.getElementById('devices-list');
        devicesList.innerHTML = '<div class="alert alert-danger">Error loading devices. Please try again later.</div>';
    }
}

async function createNewConnection() {
    try {
        const response = await fetch('/api/register_device', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                type: 'windows'
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Show connection details to the user
            showConnectionModal(data.device_id, data.host, data.port);
            
            refreshDevices();
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to register device');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert(error.message || 'Failed to register Windows device', 'danger');
    }
}

function showConnectionModal(deviceId, host, port) {
    const modalHtml = `
        <div class="modal fade" id="connectionModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">New Windows Device Connection</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p>Use these details on your Windows device:</p>
                        <pre class="bg-light p-3">
Device ID: ${deviceId}
Host: ${host}
Port: ${port}</pre>
                        <p>Run this command on your Windows device:</p>
                        <pre class="bg-light p-3">python windows_client.py ${deviceId} ${host} ${port}</pre>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add modal to document
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('connectionModal'));
    modal.show();
    
    // Remove modal from DOM after it's hidden
    document.getElementById('connectionModal').addEventListener('hidden.bs.modal', function () {
        this.remove();
    });
} 
