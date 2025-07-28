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
    if (authToken) {
        showAdminDashboard();
        loadDashboardData();
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
        const response = await fetch(`${API_BASE_URL}/api/dashboard/stats`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            dashboardStats = await response.json();
            updateStatsDisplay();
            updateWeeklyChart();
            updateGuestNotes();
        } else {
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
    } else if (tabName === 'add-reservation') {
        loadRooms(); // Load rooms for the form
        populateTimeSlots('adminTime'); // Populate time slots for admin form
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

        if (response.ok) {
            const data = await response.json();
            authToken = data.access_token;
            localStorage.setItem('authToken', authToken);
            
            showAdminDashboard();
            loadDashboardData();
            showMessage(`Welcome back, ${data.user.username}!`, 'success');
        } else {
            const error = await response.json();
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