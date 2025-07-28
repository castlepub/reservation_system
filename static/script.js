// API Configuration
const API_BASE_URL = 'http://localhost:8000';
let authToken = localStorage.getItem('authToken');

// DOM Elements
const sections = {
    home: document.getElementById('home'),
    reservations: document.getElementById('reservations'),
    admin: document.getElementById('admin'),
    adminDashboard: document.getElementById('adminDashboard')
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    try {
        initializeApp();
        setupEventListeners();
        loadRooms();
        populateTimeSlots();
        setMinDate();
    } catch (error) {
        console.error('Error initializing app:', error);
        showMessage('Error initializing application. Please refresh the page.', 'error');
    }
});

function initializeApp() {
    // Check if user is already logged in
    if (authToken) {
        showAdminDashboard();
    }
}

function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = this.getAttribute('href').substring(1);
            showSection(target);
        });
    });

    // Forms
    document.getElementById('reservationForm').addEventListener('submit', handleReservationSubmit);
    document.getElementById('adminLoginForm').addEventListener('submit', handleAdminLogin);

    // Date and party size changes
    document.getElementById('date').addEventListener('change', checkAvailability);
    document.getElementById('partySize').addEventListener('change', checkAvailability);
}

// Navigation Functions
function showSection(sectionName) {
    // Hide all sections
    Object.values(sections).forEach(section => {
        if (section) section.classList.add('hidden');
    });

    // Show target section
    if (sections[sectionName]) {
        sections[sectionName].classList.remove('hidden');
    }

    // Update navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[href="#${sectionName}"]`)?.classList.add('active');
}

function showReservationForm() {
    showSection('reservations');
}

function hideReservationForm() {
    showSection('home');
}

function showAdminLogin() {
    showSection('admin');
}

function hideAdminLogin() {
    showSection('home');
}

function showAdminDashboard() {
    showSection('adminDashboard');
    loadDashboardData();
}

// Form Functions
function setMinDate() {
    const dateInput = document.getElementById('date');
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    dateInput.min = tomorrow.toISOString().split('T')[0];
}

function populateTimeSlots() {
    const timeSelect = document.getElementById('time');
    timeSelect.innerHTML = '<option value="">Select time</option>';
    
    // Generate time slots from 11:00 to 22:30 in 30-minute intervals
    for (let hour = 11; hour <= 22; hour++) {
        for (let minute = 0; minute < 60; minute += 30) {
            if (hour === 22 && minute === 30) break; // Stop at 22:30
            const time = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
            const option = document.createElement('option');
            option.value = time;
            option.textContent = time;
            timeSelect.appendChild(option);
        }
    }
}

async function loadRooms() {
    try {
        showLoading();
        const response = await fetch(`${API_BASE_URL}/api/rooms`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const rooms = await response.json();
        
        const roomSelect = document.getElementById('room');
        if (roomSelect) {
            roomSelect.innerHTML = '<option value="">Any room</option>';
            
            rooms.forEach(room => {
                const option = document.createElement('option');
                option.value = room.id;
                option.textContent = room.name;
                roomSelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading rooms:', error);
        showMessage('Error loading rooms. Please check if the server is running.', 'error');
    } finally {
        hideLoading();
    }
}

async function checkAvailability() {
    const date = document.getElementById('date').value;
    const partySize = document.getElementById('partySize').value;
    const roomId = document.getElementById('room').value;
    
    if (!date || !partySize) return;
    
    try {
        showLoading();
        const params = new URLSearchParams({
            date: date,
            party_size: partySize
        });
        
        if (roomId) {
            params.append('room_id', roomId);
        }
        
        const response = await fetch(`${API_BASE_URL}/api/availability?${params}`);
        const availability = await response.json();
        
        // Update time slots based on availability
        const timeSelect = document.getElementById('time');
        const availableTimes = availability.available_slots.map(slot => slot.time);
        
        Array.from(timeSelect.options).forEach(option => {
            if (option.value) {
                const isAvailable = availableTimes.includes(option.value);
                option.disabled = !isAvailable;
                option.style.color = isAvailable ? '#2d3748' : '#cbd5e0';
            }
        });
        
        if (availableTimes.length === 0) {
            showMessage('No available slots for this date and party size', 'error');
        }
    } catch (error) {
        showMessage('Error checking availability', 'error');
    } finally {
        hideLoading();
    }
}

async function handleReservationSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const reservationData = {
        customer_name: formData.get('customerName'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        party_size: parseInt(formData.get('partySize')),
        date: formData.get('date'),
        time: formData.get('time'),
        room_id: formData.get('room') || null,
        notes: formData.get('notes') || null
    };
    
    try {
        showLoading();
        const response = await fetch(`${API_BASE_URL}/api/reservations`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(reservationData)
        });
        
        if (response.ok) {
            const reservation = await response.json();
            showMessage('Reservation created successfully! Check your email for confirmation.', 'success');
            e.target.reset();
            showSection('home');
        } else {
            const error = await response.json();
            showMessage(error.detail || 'Error creating reservation', 'error');
        }
    } catch (error) {
        showMessage('Error creating reservation', 'error');
    } finally {
        hideLoading();
    }
}

async function handleAdminLogin(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const loginData = {
        username: formData.get('username'),
        password: formData.get('password')
    };
    
    try {
        showLoading();
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams(loginData)
        });
        
        if (response.ok) {
            const tokenData = await response.json();
            authToken = tokenData.access_token;
            localStorage.setItem('authToken', authToken);
            showMessage('Login successful!', 'success');
            showAdminDashboard();
        } else {
            const error = await response.json();
            showMessage(error.detail || 'Login failed', 'error');
        }
    } catch (error) {
        showMessage('Error during login', 'error');
    } finally {
        hideLoading();
    }
}

function logout() {
    authToken = null;
    localStorage.removeItem('authToken');
    showMessage('Logged out successfully', 'success');
    showSection('home');
}

// Dashboard Functions
async function loadDashboardData() {
    await Promise.all([
        loadReservations(),
        loadRoomsForAdmin(),
        loadTablesForAdmin()
    ]);
}

async function loadReservations() {
    try {
        const today = new Date().toISOString().split('T')[0];
        const response = await fetch(`${API_BASE_URL}/api/admin/reservations?date=${today}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const reservations = await response.json();
            displayReservations(reservations);
        }
    } catch (error) {
        showMessage('Error loading reservations', 'error');
    }
}

function displayReservations(reservations) {
    const container = document.getElementById('reservationsList');
    
    if (reservations.length === 0) {
        container.innerHTML = '<p class="no-data">No reservations for today</p>';
        return;
    }
    
    container.innerHTML = reservations.map(reservation => `
        <div class="reservation-card">
            <div class="card-header">
                <h4 class="card-title">${reservation.customer_name}</h4>
                <span class="card-status status-${reservation.status}">${reservation.status}</span>
            </div>
            <div class="card-details">
                <div class="detail-item">
                    <span class="detail-label">Time</span>
                    <span class="detail-value">${reservation.time}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Party Size</span>
                    <span class="detail-value">${reservation.party_size} people</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Room</span>
                    <span class="detail-value">${reservation.room_name}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Contact</span>
                    <span class="detail-value">${reservation.email}<br>${reservation.phone}</span>
                </div>
            </div>
            ${reservation.notes ? `<p><strong>Notes:</strong> ${reservation.notes}</p>` : ''}
            <div class="card-actions">
                <button class="btn btn-sm btn-secondary" onclick="editReservation('${reservation.id}')">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn btn-sm btn-danger" onclick="cancelReservation('${reservation.id}')">
                    <i class="fas fa-times"></i> Cancel
                </button>
            </div>
        </div>
    `).join('');
}

async function loadRoomsForAdmin() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/rooms`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const rooms = await response.json();
            displayRooms(rooms);
        }
    } catch (error) {
        showMessage('Error loading rooms', 'error');
    }
}

function displayRooms(rooms) {
    const container = document.getElementById('roomsList');
    
    if (rooms.length === 0) {
        container.innerHTML = '<p class="no-data">No rooms found</p>';
        return;
    }
    
    container.innerHTML = rooms.map(room => `
        <div class="room-card">
            <div class="card-header">
                <h4 class="card-title">${room.name}</h4>
                <span class="card-status ${room.active ? 'status-confirmed' : 'status-cancelled'}">
                    ${room.active ? 'Active' : 'Inactive'}
                </span>
            </div>
            <p>${room.description || 'No description'}</p>
            <div class="card-actions">
                <button class="btn btn-sm btn-secondary" onclick="editRoom('${room.id}')">
                    <i class="fas fa-edit"></i> Edit
                </button>
            </div>
        </div>
    `).join('');
}

async function loadTablesForAdmin() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/tables`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const tables = await response.json();
            displayTables(tables);
        }
    } catch (error) {
        showMessage('Error loading tables', 'error');
    }
}

function displayTables(tables) {
    const container = document.getElementById('tablesList');
    
    if (tables.length === 0) {
        container.innerHTML = '<p class="no-data">No tables found</p>';
        return;
    }
    
    container.innerHTML = tables.map(table => `
        <div class="table-card">
            <div class="card-header">
                <h4 class="card-title">${table.name}</h4>
                <span class="card-status ${table.active ? 'status-confirmed' : 'status-cancelled'}">
                    ${table.active ? 'Active' : 'Inactive'}
                </span>
            </div>
            <div class="card-details">
                <div class="detail-item">
                    <span class="detail-label">Capacity</span>
                    <span class="detail-value">${table.capacity} seats</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Combinable</span>
                    <span class="detail-value">${table.combinable ? 'Yes' : 'No'}</span>
                </div>
            </div>
            <div class="card-actions">
                <button class="btn btn-sm btn-secondary" onclick="editTable('${table.id}')">
                    <i class="fas fa-edit"></i> Edit
                </button>
            </div>
        </div>
    `).join('');
}

// Tab Functions
function showTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab content
    const tabContent = document.getElementById(`${tabName}Tab`);
    if (tabContent) {
        tabContent.classList.add('active');
    }
    
    // Add active class to clicked button
    event.target.classList.add('active');
}

// Utility Functions
function showLoading() {
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

function showMessage(message, type = 'success') {
    const container = document.getElementById('messageContainer');
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}`;
    messageElement.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(messageElement);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        messageElement.remove();
    }, 5000);
}

// Placeholder functions for future implementation
function showNewReservationForm() {
    showMessage('New reservation form coming soon!', 'success');
}

function showNewRoomForm() {
    showMessage('New room form coming soon!', 'success');
}

function showNewTableForm() {
    showMessage('New table form coming soon!', 'success');
}

function editReservation(id) {
    showMessage(`Edit reservation ${id} coming soon!`, 'success');
}

function cancelReservation(id) {
    if (confirm('Are you sure you want to cancel this reservation?')) {
        showMessage(`Cancel reservation ${id} coming soon!`, 'success');
    }
}

function editRoom(id) {
    showMessage(`Edit room ${id} coming soon!`, 'success');
}

function editTable(id) {
    showMessage(`Edit table ${id} coming soon!`, 'success');
}

function generateReport() {
    const date = document.getElementById('reportDate').value;
    if (!date) {
        showMessage('Please select a date', 'error');
        return;
    }
    
    showMessage(`Generating report for ${date}...`, 'success');
    // Implementation for report generation
} 