// API Configuration
const API_BASE_URL = window.location.origin;
let authToken = localStorage.getItem('authToken');
let dashboardStats = null;
let chartInstance = null;

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
    console.log('Auth token on init:', authToken ? 'Token exists' : 'No token');
    if (authToken) {
        console.log('Token found, showing admin dashboard');
        showAdminDashboard();
        loadDashboardData();
    } else {
        console.log('No token, user needs to login');
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
    document.getElementById('adminReservationForm').addEventListener('submit', handleAdminReservationSubmit);
    document.getElementById('addNoteForm').addEventListener('submit', handleAddNote);

    // Date and party size changes
    document.getElementById('date').addEventListener('change', function() {
        updateTimeSlotsForDate(this, 'time');
        checkAvailability();
    });
    document.getElementById('partySize').addEventListener('change', checkAvailability);

    // Admin date and party size changes
    document.getElementById('adminDate').addEventListener('change', function() {
        updateTimeSlotsForDate(this, 'adminTime');
        checkAvailabilityAdmin();
    });
    document.getElementById('adminPartySize').addEventListener('change', checkAvailabilityAdmin);

    // Settings event listeners
    document.getElementById('saveWorkingHours')?.addEventListener('click', saveWorkingHours);
    document.getElementById('addSpecialDay')?.addEventListener('click', addSpecialDay);
    document.getElementById('saveAllSettings')?.addEventListener('click', saveAllSettings);

    // Search functionality
    document.getElementById('customerSearch')?.addEventListener('input', filterCustomers);
    document.getElementById('todaySearch')?.addEventListener('input', filterTodayReservations);
    document.getElementById('reservationTypeFilter')?.addEventListener('change', filterTodayReservations);
}

// Dashboard Functions
async function loadDashboardData() {
    try {
        await Promise.all([
            loadDashboardStats(),
            loadDashboardNotes(),
            loadCustomers(),
            loadTodayReservations()
        ]);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showMessage('Error loading dashboard data', 'error');
    }
}

async function loadDashboardStats() {
    try {
        console.log('Loading dashboard stats with token:', authToken ? 'Token exists' : 'No token');
        const response = await fetch(`${API_BASE_URL}/api/dashboard/stats`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        console.log('Dashboard stats response status:', response.status);
        if (response.ok) {
            dashboardStats = await response.json();
            updateStatsDisplay();
            updateWeeklyChart();
            updateGuestNotes();
        } else {
            if (response.status === 401) {
                console.error('Authentication failed - redirecting to login');
                showMessage('Session expired. Please login again.', 'error');
                logout();
                return;
            }
            throw new Error('Failed to load dashboard stats');
        }
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
        showMessage('Error loading dashboard statistics', 'error');
    }
}

function updateStatsDisplay() {
    if (!dashboardStats) return;

    document.getElementById('todayReservations').textContent = dashboardStats.total_reservations_today;
    document.getElementById('todayGuests').textContent = dashboardStats.total_guests_today;
    document.getElementById('weekReservations').textContent = dashboardStats.total_reservations_week;
    document.getElementById('weekGuests').textContent = dashboardStats.total_guests_week;
}

function updateWeeklyChart() {
    if (!dashboardStats || !dashboardStats.weekly_forecast) return;

    const canvas = document.getElementById('weeklyChart');
    const ctx = canvas.getContext('2d');

    // Destroy existing chart if it exists
    if (chartInstance) {
        chartInstance.destroy();
    }

    // Simple chart implementation
    const data = dashboardStats.weekly_forecast;
    const maxValue = Math.max(...data.map(d => Math.max(d.reservations, d.guests)));
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Chart settings
    const margin = 40;
    const chartWidth = canvas.width - margin * 2;
    const chartHeight = canvas.height - margin * 2;
    const barWidth = chartWidth / (data.length * 2);
    
    // Draw axes
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;
    
    // Y axis
    ctx.beginPath();
    ctx.moveTo(margin, margin);
    ctx.lineTo(margin, margin + chartHeight);
    ctx.stroke();
    
    // X axis
    ctx.beginPath();
    ctx.moveTo(margin, margin + chartHeight);
    ctx.lineTo(margin + chartWidth, margin + chartHeight);
    ctx.stroke();
    
    // Draw bars
    data.forEach((day, index) => {
        const x = margin + (index * barWidth * 2);
        const reservationHeight = (day.reservations / maxValue) * chartHeight;
        const guestHeight = (day.guests / maxValue) * chartHeight;
        
        // Reservations bar
        ctx.fillStyle = '#667eea';
        ctx.fillRect(x, margin + chartHeight - reservationHeight, barWidth * 0.8, reservationHeight);
        
        // Guests bar
        ctx.fillStyle = '#764ba2';
        ctx.fillRect(x + barWidth, margin + chartHeight - guestHeight, barWidth * 0.8, guestHeight);
        
        // Day label
        ctx.fillStyle = '#4a5568';
        ctx.font = '12px Inter';
        ctx.textAlign = 'center';
        const dayName = day.day_name.substring(0, 3);
        ctx.fillText(dayName, x + barWidth, margin + chartHeight + 20);
    });
    
    // Legend
    ctx.fillStyle = '#667eea';
    ctx.fillRect(margin, 10, 15, 15);
    ctx.fillStyle = '#4a5568';
    ctx.font = '12px Inter';
    ctx.textAlign = 'left';
    ctx.fillText('Reservations', margin + 20, 22);
    
    ctx.fillStyle = '#764ba2';
    ctx.fillRect(margin + 120, 10, 15, 15);
    ctx.fillText('Guests', margin + 140, 22);
}

function updateGuestNotes() {
    if (!dashboardStats || !dashboardStats.guest_notes) return;

    const container = document.getElementById('guestNotes');
    
    if (dashboardStats.guest_notes.length === 0) {
        container.innerHTML = '<p class="text-center text-gray-500">No recent guest notes</p>';
        return;
    }

    container.innerHTML = dashboardStats.guest_notes.map(note => `
        <div class="guest-note-item">
            <div class="guest-note-header">
                <span class="guest-name">${note.customer_name}</span>
                <span class="reservation-type-badge type-${note.reservation_type}">${note.reservation_type}</span>
            </div>
            <p class="note-content">"${note.notes}"</p>
            <div class="note-meta">${formatDate(note.date)} • ${note.party_size} guests</div>
        </div>
    `).join('');
}

async function loadDashboardNotes() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/notes`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const notes = await response.json();
            updateDashboardNotes(notes);
        } else {
            throw new Error('Failed to load dashboard notes');
        }
    } catch (error) {
        console.error('Error loading dashboard notes:', error);
    }
}

function updateDashboardNotes(notes) {
    const container = document.getElementById('dashboardNotes');
    
    if (notes.length === 0) {
        container.innerHTML = '<p class="text-center text-gray-500">No notes yet. Add your first note!</p>';
        return;
    }

    container.innerHTML = notes.map(note => `
        <div class="note-item priority-${note.priority}">
            <div class="note-header">
                <span class="note-title">${note.title}</span>
                <button class="btn btn-sm btn-danger" onclick="deleteNote('${note.id}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
            <p class="note-content">${note.content}</p>
            <div class="note-meta">By ${note.author} • ${formatDateTime(note.created_at)}</div>
        </div>
    `).join('');
}

async function loadCustomers() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/customers`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const customers = await response.json();
            updateCustomersTable(customers);
        } else {
            throw new Error('Failed to load customers');
        }
    } catch (error) {
        console.error('Error loading customers:', error);
    }
}

function updateCustomersTable(customers) {
    const container = document.getElementById('customersList');
    
    if (customers.length === 0) {
        container.innerHTML = '<p class="text-center">No customers found</p>';
        return;
    }

    container.innerHTML = `
        <table>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Total Reservations</th>
                    <th>Last Visit</th>
                    <th>Favorite Room</th>
                </tr>
            </thead>
            <tbody>
                ${customers.map(customer => `
                    <tr>
                        <td>${customer.customer_name}</td>
                        <td>${customer.email}</td>
                        <td>${customer.phone}</td>
                        <td>${customer.total_reservations}</td>
                        <td>${customer.last_visit ? formatDate(customer.last_visit) : 'Never'}</td>
                        <td>${customer.favorite_room || 'None'}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

async function loadTodayReservations() {
    try {
        const typeFilter = document.getElementById('reservationTypeFilter')?.value || '';
        const searchFilter = document.getElementById('todaySearch')?.value || '';
        
        const params = new URLSearchParams();
        if (typeFilter) params.append('reservation_type', typeFilter);
        if (searchFilter) params.append('search', searchFilter);
        
        const response = await fetch(`${API_BASE_URL}/api/dashboard/today?${params}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const reservations = await response.json();
            updateTodayReservations(reservations);
        } else {
            throw new Error('Failed to load today\'s reservations');
        }
    } catch (error) {
        console.error('Error loading today\'s reservations:', error);
    }
}

function updateTodayReservations(reservations) {
    const container = document.getElementById('todayReservationsList');
    
    if (reservations.length === 0) {
        container.innerHTML = '<p class="text-center">No reservations for today</p>';
        return;
    }

    container.innerHTML = reservations.map(reservation => `
        <div class="today-reservation-card">
            <div class="reservation-header">
                <div class="customer-info">
                    <h4>${reservation.customer_name}</h4>
                    <span class="reservation-type-badge type-${reservation.reservation_type}">
                        ${reservation.reservation_type}
                    </span>
                </div>
                <div class="reservation-time">${formatTime(reservation.time)}</div>
            </div>
            <div class="reservation-details">
                <div class="detail-item">
                    <div class="detail-label">Party Size</div>
                    <div class="detail-value">${reservation.party_size}</div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Tables</div>
                    <div class="detail-value">
                        <div class="table-tags">
                            ${reservation.table_names.map(table => `<span class="table-tag">${table}</span>`).join('')}
                        </div>
                    </div>
                </div>
                <div class="detail-item">
                    <div class="detail-label">Status</div>
                    <div class="detail-value">${reservation.status}</div>
                </div>
            </div>
            ${reservation.notes ? `<div class="customer-notes"><strong>Notes:</strong> ${reservation.notes}</div>` : ''}
            ${reservation.admin_notes ? `<div class="admin-notes"><strong>Admin Notes:</strong> ${reservation.admin_notes}</div>` : ''}
        </div>
    `).join('');
}

// Modal Functions
function showAddNoteModal() {
    document.getElementById('addNoteModal').classList.remove('hidden');
}

function hideAddNoteModal() {
    document.getElementById('addNoteModal').classList.add('hidden');
    document.getElementById('addNoteForm').reset();
}

async function handleAddNote(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const noteData = {
        title: formData.get('title'),
        content: formData.get('content'),
        priority: formData.get('priority')
    };

    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/notes`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(noteData)
        });

        if (response.ok) {
            hideAddNoteModal();
            loadDashboardNotes();
            showMessage('Note added successfully', 'success');
        } else {
            throw new Error('Failed to add note');
        }
    } catch (error) {
        console.error('Error adding note:', error);
        showMessage('Error adding note', 'error');
    }
}

async function deleteNote(noteId) {
    if (!confirm('Are you sure you want to delete this note?')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/notes/${noteId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            loadDashboardNotes();
            showMessage('Note deleted successfully', 'success');
        } else {
            throw new Error('Failed to delete note');
        }
    } catch (error) {
        console.error('Error deleting note:', error);
        showMessage('Error deleting note', 'error');
    }
}

// Filter Functions
function filterCustomers() {
    const searchTerm = document.getElementById('customerSearch').value.toLowerCase();
    const rows = document.querySelectorAll('#customersList tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

function filterTodayReservations() {
    loadTodayReservations(); // Reload with filters
}

// Print Functions
function printNameTags() {
    const reservations = Array.from(document.querySelectorAll('.today-reservation-card'));
    
    const printContent = reservations.map(card => {
        const name = card.querySelector('.customer-info h4').textContent;
        const time = card.querySelector('.reservation-time').textContent;
        const tables = Array.from(card.querySelectorAll('.table-tag')).map(tag => tag.textContent).join(', ');
        
        return `
            <div class="name-tag">
                <h3>${name}</h3>
                <p><strong>Time:</strong> ${time}</p>
                <p><strong>Table:</strong> ${tables}</p>
                <p><strong>The Castle Pub</strong></p>
            </div>
        `;
    }).join('');

    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
        <html>
            <head>
                <title>Name Tags</title>
                <style>
                    .name-tag {
                        width: 8cm; height: 5cm; border: 2px solid #333;
                        margin: 0.5cm; padding: 0.5cm; page-break-inside: avoid;
                        display: inline-block; text-align: center; font-family: Arial;
                    }
                    .name-tag h3 { margin: 0; font-size: 18pt; }
                    .name-tag p { margin: 0.2cm 0; font-size: 12pt; }
                </style>
            </head>
            <body>${printContent}</body>
        </html>
    `);
    printWindow.document.close();
    printWindow.print();
}

// Admin Reservation Form
async function handleAdminReservationSubmit(e) {
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
        reservation_type: formData.get('reservationType'),
        notes: formData.get('notes') || null,
        admin_notes: formData.get('adminNotes') || null
    };

    try {
        const response = await fetch(`${API_BASE_URL}/api/reservations`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(reservationData)
        });

        if (response.ok) {
            const reservation = await response.json();
            showMessage('Reservation created successfully', 'success');
            e.target.reset();
            loadDashboardData(); // Refresh dashboard data
        } else {
            const error = await response.json();
            console.error('Admin reservation creation failed:', error);
            
            // Show detailed validation errors
            if (error.detail && Array.isArray(error.detail)) {
                const errorMessages = error.detail.map(err => `${err.loc?.join('.')}: ${err.msg}`).join('\n');
                throw new Error(`Validation errors:\n${errorMessages}`);
            }
            
            throw new Error(error.detail || JSON.stringify(error) || 'Failed to create reservation');
        }
    } catch (error) {
        console.error('Error creating reservation:', error);
        showMessage(error.message || 'Failed to create reservation', 'error');
    }
}

async function checkAvailabilityAdmin() {
    const date = document.getElementById('adminDate').value;
    const partySize = document.getElementById('adminPartySize').value;
    
    if (date && partySize) {
        await checkAvailability(); // Reuse existing function
    }
}

// Tab Management
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    const selectedTab = document.getElementById(tabName + 'Tab');
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to clicked tab button
    event.target.classList.add('active');
    
    // Load data for specific tabs
    if (tabName === 'dashboard') {
        loadDashboardStats();
    } else if (tabName === 'customers') {
        loadCustomers();
    } else if (tabName === 'today') {
        loadTodayReservations();
    } else if (tabName === 'settings') {
        loadSettingsData();
    } else if (tabName === 'add-reservation') {
        loadRooms(); // Load rooms for the form
        populateTimeSlots('adminTime'); // Populate time slots for admin form
    } else if (tabName === 'tables') {
        loadTablesData();
    }
}

// Existing functions (keeping the original functionality)
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
        reservation_type: formData.get('reservationType') || 'dining',
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
            hideReservationForm();
        } else {
            const error = await response.json();
            console.error('Reservation creation failed:', error);
            
            // Show detailed validation errors for 422
            if (response.status === 422 && error.detail && Array.isArray(error.detail)) {
                const errorMessages = error.detail.map(err => {
                    const field = err.loc?.slice(1).join('.') || 'unknown field';
                    return `${field}: ${err.msg}`;
                }).join('\n');
                throw new Error(`Validation errors:\n${errorMessages}`);
            }
            
            throw new Error(error.detail || JSON.stringify(error) || 'Failed to create reservation');
        }
    } catch (error) {
        console.error('Error creating reservation:', error);
        showMessage(error.message || 'Failed to create reservation', 'error');
    } finally {
        hideLoading();
    }
}

async function handleAdminLogin(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    
    try {
        showLoading();
        
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            body: formData
        });

        console.log('Login response status:', response.status);
        if (response.ok) {
            const data = await response.json();
            console.log('Login successful, got token');
            authToken = data.access_token;
            localStorage.setItem('authToken', authToken);
            
            showAdminDashboard();
            loadDashboardData();
            showMessage(`Welcome back, ${data.user.username}!`, 'success');
        } else {
            const error = await response.json();
            console.error('Login failed:', error);
            throw new Error(error.detail || 'Login failed');
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage(error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Navigation Functions
function showSection(sectionName) {
    Object.values(sections).forEach(section => {
        section.classList.add('hidden');
    });
    
    const targetSection = sections[sectionName];
    if (targetSection) {
        targetSection.classList.remove('hidden');
    }
    
    // Update navigation active state
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    const activeLink = document.querySelector(`[href="#${sectionName}"]`);
    if (activeLink) {
        activeLink.classList.add('active');
    }
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
}

function logout() {
    authToken = null;
    localStorage.removeItem('authToken');
    showSection('home');
    showMessage('Logged out successfully', 'success');
}

// Utility Functions
async function loadRooms() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/rooms`);
        if (response.ok) {
            const rooms = await response.json();
            populateRoomOptions(rooms);
        }
    } catch (error) {
        console.error('Error loading rooms:', error);
    }
}

function populateRoomOptions(rooms) {
    const roomSelects = ['room', 'adminRoom'];
    
    roomSelects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            // Keep the first option (Any room)
            while (select.options.length > 1) {
                select.removeChild(select.lastChild);
            }
            
            rooms.forEach(room => {
                const option = document.createElement('option');
                option.value = room.id;
                option.textContent = room.name;
                select.appendChild(option);
            });
        }
    });
}

function populateTimeSlots(selectId = 'time') {
    const timeSelect = document.getElementById(selectId);
    if (!timeSelect) return;
    
    // Keep the first option
    while (timeSelect.options.length > 1) {
        timeSelect.removeChild(timeSelect.lastChild);
    }
    
    // Generate time slots from 11:00 to 22:30 (default fallback)
    for (let hour = 11; hour <= 22; hour++) {
        for (let minute = 0; minute < 60; minute += 30) {
            const timeString = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
            const option = document.createElement('option');
            option.value = timeString;
            option.textContent = timeString;
            timeSelect.appendChild(option);
        }
    }
}

async function updateTimeSlotsForDate(dateInput, timeSelectId) {
    const selectedDate = new Date(dateInput.value);
    if (!selectedDate || isNaN(selectedDate)) return;
    
    const dayOfWeek = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'][selectedDate.getDay()];
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/settings/working-hours/${dayOfWeek}/time-slots`);
        if (response.ok) {
            const data = await response.json();
            const timeSelect = document.getElementById(timeSelectId);
            
            // Clear existing options except the first
            while (timeSelect.options.length > 1) {
                timeSelect.removeChild(timeSelect.lastChild);
            }
            
            if (data.time_slots && data.time_slots.length > 0) {
                data.time_slots.forEach(timeSlot => {
                    const option = document.createElement('option');
                    option.value = timeSlot;
                    option.textContent = timeSlot;
                    timeSelect.appendChild(option);
                });
            } else {
                // Restaurant is closed
                const option = document.createElement('option');
                option.value = '';
                option.textContent = data.message || 'Restaurant is closed';
                option.disabled = true;
                timeSelect.appendChild(option);
            }
        } else {
            // Fallback to default time slots
            populateTimeSlots(timeSelectId);
        }
    } catch (error) {
        console.error('Error loading time slots:', error);
        // Fallback to default time slots
        populateTimeSlots(timeSelectId);
    }
}

function setMinDate() {
    const dateInputs = ['date', 'adminDate'];
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const minDate = tomorrow.toISOString().split('T')[0];
    
    dateInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.min = minDate;
        }
    });
}

async function checkAvailability() {
    // This function can be enhanced to show real-time availability
    console.log('Checking availability...');
}

function showLoading() {
    document.getElementById('loadingOverlay').classList.remove('hidden');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden');
}

function showMessage(message, type = 'info') {
    const container = document.getElementById('messageContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;
    messageDiv.innerHTML = `
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" class="message-close">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(messageDiv);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentElement) {
            messageDiv.remove();
        }
    }, 5000);
}

// Utility formatting functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateTimeString) {
    const date = new Date(dateTimeString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatTime(timeString) {
    const [hours, minutes] = timeString.split(':');
    const date = new Date();
    date.setHours(parseInt(hours), parseInt(minutes));
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
} 

// Settings Functions
async function loadSettingsData() {
    try {
        await Promise.all([
            loadWorkingHours(),
            loadRestaurantSettings(),
            loadSpecialDays()
        ]);
    } catch (error) {
        console.error('Error loading settings:', error);
        showMessage('Error loading settings data', 'error');
    }
}

async function loadWorkingHours() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/settings/working-hours`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            updateWorkingHoursDisplay(data);
        } else {
            throw new Error('Failed to load working hours');
        }
    } catch (error) {
        console.error('Error loading working hours:', error);
        showMessage('Error loading working hours', 'error');
    }
}

function updateWorkingHoursDisplay(weeklySchedule) {
    const container = document.getElementById('workingHoursContainer');
    const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
    const dayNames = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    
    container.innerHTML = '';
    
    days.forEach((day, index) => {
        const dayData = weeklySchedule[day] || {
            is_open: true,
            open_time: '11:00',
            close_time: '23:00'
        };
        
        const dayElement = document.createElement('div');
        dayElement.className = `working-hours-day ${!dayData.is_open ? 'closed' : ''}`;
        dayElement.innerHTML = `
            <div class="day-name">${dayNames[index]}</div>
            <div class="day-toggle">
                <label>
                    <input type="checkbox" ${dayData.is_open ? 'checked' : ''} 
                           onchange="toggleDayOpen('${day}', this.checked)">
                    Open
                </label>
            </div>
            <div class="time-inputs" style="display: ${dayData.is_open ? 'flex' : 'none'}">
                <input type="time" value="${dayData.open_time || '11:00'}" 
                       id="${day}-open" class="time-input">
                <span>to</span>
                <input type="time" value="${dayData.close_time || '23:00'}" 
                       id="${day}-close" class="time-input">
            </div>
            <div class="closed-text" style="display: ${dayData.is_open ? 'none' : 'block'}">
                <span class="text-muted">Closed</span>
            </div>
        `;
        container.appendChild(dayElement);
    });
}

function toggleDayOpen(day, isOpen) {
    const dayElement = document.querySelector(`.working-hours-day:has(#${day}-open)`);
    const timeInputs = dayElement.querySelector('.time-inputs');
    const closedText = dayElement.querySelector('.closed-text');
    
    if (isOpen) {
        dayElement.classList.remove('closed');
        timeInputs.style.display = 'flex';
        closedText.style.display = 'none';
    } else {
        dayElement.classList.add('closed');
        timeInputs.style.display = 'none';
        closedText.style.display = 'block';
    }
}

async function saveWorkingHours() {
    try {
        const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
        const workingHoursData = {};
        
        for (const day of days) {
            const isOpenCheckbox = document.querySelector(`input[onchange*="${day}"]`);
            const openTimeInput = document.getElementById(`${day}-open`);
            const closeTimeInput = document.getElementById(`${day}-close`);
            
            workingHoursData[day] = {
                is_open: isOpenCheckbox?.checked || false,
                open_time: openTimeInput?.value || '11:00',
                close_time: closeTimeInput?.value || '23:00'
            };
        }

        for (const [day, hours] of Object.entries(workingHoursData)) {
            const response = await fetch(`${API_BASE_URL}/api/settings/working-hours/${day}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    is_open: hours.is_open,
                    open_time: hours.is_open ? hours.open_time : null,
                    close_time: hours.is_open ? hours.close_time : null
                })
            });

            if (!response.ok) {
                const error = await response.text();
                console.error(`Failed to save working hours for ${day}:`, error);
                throw new Error(`Failed to save working hours for ${day}`);
            }
        }

        showMessage('Working hours saved successfully', 'success');
    } catch (error) {
        console.error('Error saving working hours:', error);
        showMessage('Error saving working hours', 'error');
    }
}

async function loadRestaurantSettings() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/settings/restaurant`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const settings = await response.json();
            updateRestaurantSettingsDisplay(settings);
        }
    } catch (error) {
        console.error('Error loading restaurant settings:', error);
    }
}

function updateRestaurantSettingsDisplay(settings) {
    // Set default values if settings exist
    settings.forEach(setting => {
        const element = document.getElementById(getSettingElementId(setting.setting_key));
        if (element) {
            element.value = setting.setting_value;
        }
    });
}

function getSettingElementId(settingKey) {
    const mapping = {
        'restaurant_name': 'restaurantName',
        'restaurant_phone': 'restaurantPhone', 
        'restaurant_address': 'restaurantAddress',
        'max_party_size': 'maxPartySize',
        'min_advance_hours': 'minAdvanceHours',
        'max_advance_days': 'maxAdvanceDays'
    };
    return mapping[settingKey] || settingKey;
}

async function saveAllSettings() {
    try {
        const settingsData = [
            { setting_key: 'restaurant_name', setting_value: document.getElementById('restaurantName').value },
            { setting_key: 'restaurant_phone', setting_value: document.getElementById('restaurantPhone').value },
            { setting_key: 'restaurant_address', setting_value: document.getElementById('restaurantAddress').value },
            { setting_key: 'max_party_size', setting_value: document.getElementById('maxPartySize').value },
            { setting_key: 'min_advance_hours', setting_value: document.getElementById('minAdvanceHours').value },
            { setting_key: 'max_advance_days', setting_value: document.getElementById('maxAdvanceDays').value }
        ];

        for (const setting of settingsData) {
            const response = await fetch(`${API_BASE_URL}/api/settings/restaurant/${setting.setting_key}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    setting_key: setting.setting_key,
                    setting_value: setting.setting_value,
                    description: `Restaurant ${setting.setting_key.replace('_', ' ')}`
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to save setting: ${setting.setting_key}`);
            }
        }

        // Also save working hours
        await saveWorkingHours();
        
        showMessage('All settings saved successfully', 'success');
    } catch (error) {
        console.error('Error saving settings:', error);
        showMessage('Error saving settings', 'error');
    }
}

async function loadSpecialDays() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/settings/special-days`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const specialDays = await response.json();
            updateSpecialDaysDisplay(specialDays);
        }
    } catch (error) {
        console.error('Error loading special days:', error);
        // It's OK if this fails - feature might not be implemented yet
    }
}

function updateSpecialDaysDisplay(specialDays) {
    const container = document.getElementById('specialDaysContainer');
    container.innerHTML = '';
    
    if (specialDays.length === 0) {
        container.innerHTML = '<div class="loading-text">No special days configured</div>';
        return;
    }
    
    specialDays.forEach(day => {
        const dayElement = document.createElement('div');
        dayElement.className = 'special-day-item';
        dayElement.innerHTML = `
            <div class="special-day-info">
                <div class="special-day-date">${new Date(day.date).toLocaleDateString()}</div>
                <div class="special-day-reason">${day.reason}</div>
            </div>
            <button class="btn btn-sm btn-danger" onclick="removeSpecialDay('${day.id}')">
                <i class="fas fa-trash"></i>
            </button>
        `;
        container.appendChild(dayElement);
    });
}

async function addSpecialDay() {
    const dateInput = document.getElementById('specialDate');
    const reasonInput = document.getElementById('specialReason');
    
    if (!dateInput.value || !reasonInput.value) {
        showMessage('Please enter both date and reason', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/settings/special-days`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                date: dateInput.value,
                reason: reasonInput.value
            })
        });

        if (response.ok) {
            dateInput.value = '';
            reasonInput.value = '';
            loadSpecialDays();
            showMessage('Special day added successfully', 'success');
        } else {
            throw new Error('Failed to add special day');
        }
    } catch (error) {
        console.error('Error adding special day:', error);
        showMessage('Error adding special day', 'error');
    }
}

async function removeSpecialDay(dayId) {
    if (!confirm('Are you sure you want to remove this special day?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/settings/special-days/${dayId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            loadSpecialDays();
            showMessage('Special day removed successfully', 'success');
        } else {
            throw new Error('Failed to remove special day');
        }
    } catch (error) {
        console.error('Error removing special day:', error);
        showMessage('Error removing special day', 'error');
    }
} 

// Table Management Functions
async function loadTablesData() {
    try {
        // Load rooms for filter
        await loadRoomsForTables();
        // Load tables
        await loadTables();
    } catch (error) {
        console.error('Error loading tables data:', error);
        showMessage('Error loading tables data', 'error');
    }
}

async function loadRoomsForTables() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/rooms`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const rooms = await response.json();
            
            // Populate room filter
            const roomFilter = document.getElementById('roomFilter');
            const tableRoom = document.getElementById('tableRoom');
            
            // Clear existing options (keep "All Rooms" for filter)
            while (roomFilter.options.length > 1) {
                roomFilter.removeChild(roomFilter.lastChild);
            }
            
            // Clear table room select
            while (tableRoom.options.length > 1) {
                tableRoom.removeChild(tableRoom.lastChild);
            }
            
            rooms.forEach(room => {
                // Add to filter
                const filterOption = document.createElement('option');
                filterOption.value = room.id;
                filterOption.textContent = room.name;
                roomFilter.appendChild(filterOption);
                
                // Add to add table form
                const tableOption = document.createElement('option');
                tableOption.value = room.id;
                tableOption.textContent = room.name;
                tableRoom.appendChild(tableOption);
            });
        }
    } catch (error) {
        console.error('Error loading rooms for tables:', error);
    }
}

async function loadTables(roomId = null) {
    try {
        let url = `${API_BASE_URL}/api/admin/tables`;
        if (roomId) {
            url += `?room_id=${roomId}`;
        }
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const tables = await response.json();
            displayTables(tables);
        } else {
            console.error('Failed to load tables');
            document.getElementById('tablesGrid').innerHTML = '<div class="error-text">Failed to load tables</div>';
        }
    } catch (error) {
        console.error('Error loading tables:', error);
        document.getElementById('tablesGrid').innerHTML = '<div class="error-text">Error loading tables</div>';
    }
}

function displayTables(tables) {
    const tablesGrid = document.getElementById('tablesGrid');
    
    if (tables.length === 0) {
        tablesGrid.innerHTML = '<div class="empty-text">No tables found. Add some tables to get started!</div>';
        return;
    }
    
    // Group tables by room
    const tablesByRoom = tables.reduce((acc, table) => {
        const roomName = table.room?.name || 'Unknown Room';
        if (!acc[roomName]) {
            acc[roomName] = [];
        }
        acc[roomName].push(table);
        return acc;
    }, {});
    
    let html = '';
    
    Object.entries(tablesByRoom).forEach(([roomName, roomTables]) => {
        html += `
            <div class="room-section">
                <h4 class="room-title">${roomName}</h4>
                <div class="tables-row">
        `;
        
        roomTables.forEach(table => {
            html += `
                <div class="table-card">
                    <div class="table-header">
                        <h5>${table.name}</h5>
                        <div class="table-actions">
                            <button class="btn-small btn-secondary" onclick="editTable('${table.id}')">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn-small btn-danger" onclick="deleteTable('${table.id}', '${table.name}')">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                    <div class="table-info">
                        <div class="info-item">
                            <i class="fas fa-users"></i>
                            <span>${table.capacity} seats</span>
                        </div>
                        <div class="info-item">
                            <i class="fas fa-${table.combinable ? 'link' : 'unlink'}"></i>
                            <span>${table.combinable ? 'Combinable' : 'Stand-alone'}</span>
                        </div>
                        <div class="info-item">
                            <i class="fas fa-${table.active ? 'check-circle' : 'times-circle'}"></i>
                            <span>${table.active ? 'Active' : 'Inactive'}</span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    });
    
    tablesGrid.innerHTML = html;
}

function showAddTableForm() {
    document.getElementById('addTableModal').classList.remove('hidden');
}

function hideAddTableForm() {
    document.getElementById('addTableModal').classList.add('hidden');
    document.getElementById('addTableForm').reset();
}

async function handleAddTable(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const tableData = {
        room_id: formData.get('room_id'),
        name: formData.get('name'),
        capacity: parseInt(formData.get('capacity')),
        combinable: formData.get('combinable') === 'on'
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/tables`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(tableData)
        });
        
        if (response.ok) {
            showMessage('Table added successfully', 'success');
            hideAddTableForm();
            loadTables(); // Reload tables
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to add table');
        }
    } catch (error) {
        console.error('Error adding table:', error);
        showMessage('Error adding table: ' + error.message, 'error');
    }
}

async function deleteTable(tableId, tableName) {
    if (!confirm(`Are you sure you want to delete table "${tableName}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/tables/${tableId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            showMessage('Table deleted successfully', 'success');
            loadTables(); // Reload tables
        } else {
            throw new Error('Failed to delete table');
        }
    } catch (error) {
        console.error('Error deleting table:', error);
        showMessage('Error deleting table', 'error');
    }
}

// Add event listeners for date changes in both forms
document.addEventListener('DOMContentLoaded', function() {
    // Add event listener for public reservation form
    setTimeout(() => {
        const dateInput = document.getElementById('date');
        const timeSelect = document.getElementById('time');
        
        if (dateInput && timeSelect) {
            dateInput.addEventListener('change', function() {
                if (this.value) {
                    updateTimeSlotsForDate(this, 'time');
                }
            });
        }

        // Add event listener for admin reservation form
        const adminDateInput = document.getElementById('adminDate');
        const adminTimeSelect = document.getElementById('adminTime');
        
        if (adminDateInput && adminTimeSelect) {
            adminDateInput.addEventListener('change', function() {
                if (this.value) {
                    updateTimeSlotsForDate(this, 'adminTime');
                }
            });
        }

        // Add event listener for room filter if it exists
        const roomFilter = document.getElementById('roomFilter');
        if (roomFilter) {
            roomFilter.addEventListener('change', function() {
                const selectedRoom = this.value;
                loadTables(selectedRoom || null);
            });
        }
    }, 1000);
}); 