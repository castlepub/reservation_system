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
    console.log('Initializing app...');
    
    try {
        initializeApp();
        setupEventListeners();
        
        // Initialize public dropdowns immediately (no auth required)
        initializePublicDropdowns();
        
        // Check if user is logged in and load admin data
        if (authToken) {
            checkAuth();
            loadRestaurantSettings(); // Load settings for admin users
        }
        
        console.log('App initialized successfully');
    } catch (error) {
        console.error('Error initializing app:', error);
    }
});

function initializePublicDropdowns() {
    // Set default party size options (fallback)
    const publicPartySize = document.getElementById('partySize');
    if (publicPartySize && publicPartySize.children.length <= 1) {
        populatePartySizeDropdown(publicPartySize, 20); // Default max 20
    }
    
    // Load rooms for public form (no auth required for public API)
    loadRoomsPublic();
    
    // Set minimum date
    setMinDate();
    
    // Populate time slots
    populateTimeSlots();
}

function populatePartySizeDropdown(selectElement, maxSize = 20) {
    if (!selectElement) return;
    
    // Clear existing options except placeholder
    selectElement.innerHTML = '<option value="">Select size</option>';
    
    // Add options up to max size
    for (let i = 1; i <= maxSize; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = i === 1 ? '1 person' : `${i} people`;
        selectElement.appendChild(option);
    }
}

async function loadRoomsPublic() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/rooms`);
        
        if (response.ok) {
            const rooms = await response.json();
            populateRoomOptions(rooms);
        } else {
            console.log('No public rooms API available, using fallback');
            // Add fallback room options
            populateRoomOptions([
                { id: "", name: "Any room" }
            ]);
        }
    } catch (error) {
        console.error('Error loading public rooms:', error);
        // Add fallback room options
        populateRoomOptions([
            { id: "", name: "Any room" }
        ]);
    }
}

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

async function checkAuth() {
    if (!authToken) {
        console.log('No auth token, redirecting to login');
        return false;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const user = await response.json();
            console.log('Auth check successful for user:', user.username);
            return true;
        } else {
            console.log('Auth check failed, clearing token');
            authToken = null;
            localStorage.removeItem('authToken');
            return false;
        }
    } catch (error) {
        console.error('Auth check error:', error);
        authToken = null;
        localStorage.removeItem('authToken');
        return false;
    }
}

function setupEventListeners() {
    // Forms
    document.getElementById('reservationForm').addEventListener('submit', handleReservationSubmit);
    document.getElementById('adminLoginForm').addEventListener('submit', handleAdminLogin);
    // Removed adminReservationForm - it's now handled by the modal
    document.getElementById('addNoteForm').addEventListener('submit', handleAddNote);

    // Date and party size changes
    document.getElementById('date').addEventListener('change', function() {
        updateTimeSlotsForDate(this, 'time');
        checkAvailability();
    });
    
    document.getElementById('partySize').addEventListener('change', checkAvailability);
    
    // Admin form date changes
    const newDateInput = document.getElementById('newDate');
    if (newDateInput) {
        newDateInput.addEventListener('change', function() {
            updateTimeSlotsForDate(this, 'newTime');
        });
    }
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
    } else if (tabName === 'reservations') {
        loadAllReservations();
    } else if (tabName === 'settings') {
        loadSettingsData();
        loadRestaurantSettings(); // Load restaurant settings for dynamic forms
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
            window.loadedRooms = rooms; // Store for use in loadTablesData
        }
    } catch (error) {
        console.error('Error loading rooms:', error);
    }
}

function populateRoomOptions(rooms) {
    const roomSelects = ['room', 'adminRoom', 'newRoom'];
    
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
    
    // Convert backend format {working_hours: [...]} to frontend format {monday: {...}}
    let dayData = {};
    if (weeklySchedule.working_hours && Array.isArray(weeklySchedule.working_hours)) {
        weeklySchedule.working_hours.forEach(hours => {
            dayData[hours.day_of_week] = {
                is_open: hours.is_open,
                open_time: hours.open_time,
                close_time: hours.close_time
            };
        });
    }
    
    days.forEach((day, index) => {
        const daySchedule = dayData[day] || {
            is_open: true,
            open_time: '11:00',
            close_time: '23:00'
        };
        
        const dayElement = document.createElement('div');
        dayElement.className = `working-hours-day ${!daySchedule.is_open ? 'closed' : ''}`;
        dayElement.innerHTML = `
            <div class="day-name">${dayNames[index]}</div>
            <div class="day-toggle">
                <label>
                    <input type="checkbox" ${daySchedule.is_open ? 'checked' : ''} 
                           onchange="toggleDayOpen('${day}', this.checked)">
                    Open
                </label>
            </div>
            <div class="time-inputs" style="display: ${daySchedule.is_open ? 'flex' : 'none'}">
                <div class="time-input-group">
                    <label>Open:</label>
                    <input type="time" value="${daySchedule.open_time || '11:00'}" 
                           id="${day}-open" class="time-input" step="1800">
                </div>
                <span class="time-separator">to</span>
                <div class="time-input-group">
                    <label>Close:</label>
                    <input type="time" value="${daySchedule.close_time || '23:00'}" 
                           id="${day}-close" class="time-input" step="1800">
                </div>
            </div>
            <div class="closed-text" style="display: ${daySchedule.is_open ? 'none' : 'block'}">
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
            const isOpenCheckbox = document.getElementById(`${day}-open-checkbox`);
            const openTimeInput = document.getElementById(`${day}-open`);
            const closeTimeInput = document.getElementById(`${day}-close`);
            
            workingHoursData[day] = {
                is_open: isOpenCheckbox?.checked || false,
                open_time: openTimeInput?.value || '11:00',
                close_time: closeTimeInput?.value || '23:00'
            };
        }

        const response = await fetch(`${API_BASE_URL}/api/settings/working-hours`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(workingHoursData)
        });

        if (response.ok) {
            showMessage('Working hours saved successfully', 'success');
        } else {
            throw new Error('Failed to save working hours');
        }
    } catch (error) {
        console.error('Error saving working hours:', error);
        showMessage('Error saving working hours', 'error');
    }
}

// Load restaurant settings and populate forms
async function loadRestaurantSettings() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/settings/restaurant`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const settings = await response.json();
            const settingsMap = {};
            
            settings.forEach(setting => {
                settingsMap[setting.setting_key] = setting.setting_value;
            });
            
            // Update max party size in forms immediately 
            const maxPartySize = parseInt(settingsMap.max_party_size) || 20;
            updateMaxPartySizeOptions(maxPartySize);
            
            // Populate settings form
            populateSettingsForm(settingsMap);
            
            return settingsMap;
        } else {
            console.error('Failed to load restaurant settings');
            return {};
        }
    } catch (error) {
        console.error('Error loading restaurant settings:', error);
        return {};
    }
}

function updateMaxPartySizeOptions(maxPartySize) {
    // Target all party size dropdowns (public, admin, and new reservation)
    const partySizeSelects = document.querySelectorAll('#partySize, #adminPartySize, #newPartySize, #editPartySize');
    
    partySizeSelects.forEach(select => {
        if (select) {
            // Store current value to restore if possible
            const currentValue = select.value;
            
            // Clear existing options except placeholder
            select.innerHTML = '<option value="">Select size</option>';
            
            // Add options up to max party size
            for (let i = 1; i <= maxPartySize; i++) {
                const option = document.createElement('option');
                option.value = i;
                option.textContent = i === 1 ? '1 person' : `${i} people`;
                select.appendChild(option);
            }
            
            // Restore previous value if it's still valid
            if (currentValue && parseInt(currentValue) <= maxPartySize) {
                select.value = currentValue;
            }
        }
    });
}

function populateSettingsForm(settings) {
    // Populate individual setting fields
    const restaurantName = document.getElementById('restaurantName');
    const maxPartySize = document.getElementById('maxPartySize');
    const minAdvanceHours = document.getElementById('minAdvanceHours');
    const maxReservationDays = document.getElementById('maxReservationDays');
    const timeSlotDuration = document.getElementById('timeSlotDuration');
    
    if (restaurantName) restaurantName.value = settings.restaurant_name || '';
    if (maxPartySize) maxPartySize.value = settings.max_party_size || '20';
    if (minAdvanceHours) minAdvanceHours.value = settings.min_advance_hours || '0';
    if (maxReservationDays) maxReservationDays.value = settings.max_reservation_days || '90';
    if (timeSlotDuration) timeSlotDuration.value = settings.time_slot_duration || '30';
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
        const rooms = await loadRoomsForTables();
        // Load tables
        const tables = await loadTables();
        
        // Populate room filter dropdown
        populateRoomFilter(rooms);
        
        // Populate room dropdown for add table form
        populateAddTableRoomDropdown(rooms);
        
        // Display tables
        displayTables(tables, rooms);
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
            // Store globally for room filtering
            window.loadedRooms = rooms;
            return rooms;
        } else {
            console.error('Failed to load rooms for tables');
            showMessage('Failed to load rooms. Please check your admin permissions.', 'error');
            return [];
        }
    } catch (error) {
        console.error('Error loading rooms for tables:', error);
        return [];
    }
}

async function loadTables() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/tables`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const tables = await response.json();
            return tables;
        } else {
            console.error('Failed to load tables');
            showMessage('Failed to load tables. Please check your admin permissions.', 'error');
            return [];
        }
    } catch (error) {
        console.error('Error loading tables:', error);
        showMessage('Error loading tables', 'error');
        return [];
    }
}

function displayTables(tables, rooms) {
    const tablesGrid = document.getElementById('tablesGrid');
    
    if (tables.length === 0) {
        tablesGrid.innerHTML = '<div class="empty-text">No tables found</div>';
        return;
    }
    
    let html = '';
    
    tables.forEach(table => {
        const room = rooms.find(r => r.id === table.room_id);
        const roomName = room ? room.name : 'Unknown Room';
        
        html += `
            <div class="table-card">
                <div class="table-header">
                    <h5>${table.name}</h5>
                    <span class="table-id">ID: ${table.id.substring(0, 8)}...</span>
                </div>
                <div class="table-details">
                    <div class="detail-row">
                        <i class="fas fa-door-open"></i>
                        <span>${roomName}</span>
                    </div>
                    <div class="detail-row">
                        <i class="fas fa-users"></i>
                        <span>${table.capacity} seats</span>
                    </div>
                    <div class="detail-row">
                        <i class="fas fa-link"></i>
                        <span>${table.combinable ? 'Combinable' : 'Not combinable'}</span>
                    </div>
                    <div class="detail-row">
                        <i class="fas fa-circle"></i>
                        <span class="${table.active ? 'status-active' : 'status-inactive'}">
                            ${table.active ? 'Active' : 'Inactive'}
                        </span>
                    </div>
                </div>
                <div class="table-actions">
                    <button class="btn-small btn-secondary" onclick="editTable('${table.id}')">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn-small btn-danger" onclick="deleteTable('${table.id}')">
                        <i class="fas fa-trash"></i> Delete
                    </button>
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

function populateRoomFilter(rooms) {
    const roomFilter = document.getElementById('roomFilter');
    if (roomFilter) {
        // Clear existing options except "All Rooms"
        roomFilter.innerHTML = '<option value="">All Rooms</option>';
        
        rooms.forEach(room => {
            const option = document.createElement('option');
            option.value = room.id;
            option.textContent = room.name;
            roomFilter.appendChild(option);
        });
        
        // Add change event listener
        roomFilter.addEventListener('change', function() {
            filterTablesByRoom(this.value);
        });
    }
}

function populateAddTableRoomDropdown(rooms) {
    const tableRoom = document.getElementById('tableRoom');
    if (tableRoom) {
        // Clear existing options
        tableRoom.innerHTML = '<option value="">Select Room</option>';
        
        rooms.forEach(room => {
            const option = document.createElement('option');
            option.value = room.id;
            option.textContent = room.name;
            tableRoom.appendChild(option);
        });
    }
}

function filterTablesByRoom(roomId) {
    const tableCards = document.querySelectorAll('.table-card');
    
    tableCards.forEach(card => {
        if (!roomId) {
            // Show all tables
            card.style.display = 'block';
        } else {
            // Check if table belongs to selected room
            const roomSpan = card.querySelector('.detail-row span');
            if (roomSpan && roomSpan.textContent.includes(getRoomNameById(roomId))) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        }
    });
}

function getRoomNameById(roomId) {
    // This will be populated when rooms are loaded
    return window.loadedRooms?.find(r => r.id === roomId)?.name || '';
}

// Reservation Management Functions
async function loadAllReservations() {
    try {
        // Get the selected date filter
        const dateFilter = document.getElementById('reservationDateFilter').value;
        let url = `${API_BASE_URL}/api/admin/reservations`;
        
        // Add date filter if selected
        if (dateFilter) {
            url += `?date_filter=${dateFilter}`;
        }
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const reservations = await response.json();
            displayReservations(reservations);
        } else {
            console.error('Failed to load reservations');
            document.getElementById('reservationsList').innerHTML = '<div class="error-text">Failed to load reservations</div>';
        }
    } catch (error) {
        console.error('Error loading reservations:', error);
        document.getElementById('reservationsList').innerHTML = '<div class="error-text">Error loading reservations</div>';
    }
}

function displayReservations(reservations) {
    const reservationsList = document.getElementById('reservationsList');
    
    if (reservations.length === 0) {
        reservationsList.innerHTML = '<div class="empty-text">No reservations found</div>';
        return;
    }
    
    let html = '<div class="reservations-grid">';
    
    reservations.forEach(reservation => {
        const statusClass = reservation.status.toLowerCase();
        const date = new Date(reservation.date).toLocaleDateString();
        const time = reservation.time;
        
        html += `
            <div class="reservation-card ${statusClass}">
                <div class="reservation-header">
                    <h5>${reservation.customer_name}</h5>
                    <span class="status-badge status-${statusClass}">${reservation.status}</span>
                </div>
                <div class="reservation-details">
                    <div class="detail-row">
                        <i class="fas fa-calendar"></i>
                        <span>${date} at ${time}</span>
                    </div>
                    <div class="detail-row">
                        <i class="fas fa-users"></i>
                        <span>${reservation.party_size} people</span>
                    </div>
                    <div class="detail-row">
                        <i class="fas fa-door-open"></i>
                        <span>${reservation.room_name || 'Any room'}</span>
                    </div>
                    <div class="detail-row">
                        <i class="fas fa-envelope"></i>
                        <span>${reservation.email}</span>
                    </div>
                    <div class="detail-row">
                        <i class="fas fa-phone"></i>
                        <span>${reservation.phone}</span>
                    </div>
                    ${reservation.notes ? `
                        <div class="detail-row">
                            <i class="fas fa-comment"></i>
                            <span>${reservation.notes}</span>
                        </div>
                    ` : ''}
                </div>
                <div class="reservation-actions">
                    <button class="btn-small btn-secondary" onclick="editReservation('${reservation.id}')">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    <button class="btn-small btn-danger" onclick="cancelReservation('${reservation.id}')">
                        <i class="fas fa-times"></i> Cancel
                    </button>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    reservationsList.innerHTML = html;
}

function showAddReservationForm() {
    document.getElementById('addReservationModal').classList.remove('hidden');
    
    // Load and populate rooms
    loadRooms();
    
    // Load restaurant settings and update party size
    loadRestaurantSettings().then(() => {
        // Populate time slots
        populateTimeSlots('newTime');
        
        // Populate party size dropdown
        const partySizeSelect = document.getElementById('newPartySize');
        if (partySizeSelect) {
            populatePartySizeDropdown(partySizeSelect, 20);
        }
    });
}

function hideAddReservationForm() {
    document.getElementById('addReservationModal').classList.add('hidden');
    document.getElementById('addReservationForm').reset();
}

async function handleAddReservation(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
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
            showMessage('Reservation created successfully', 'success');
            hideAddReservationForm();
            loadAllReservations(); // Reload reservations list
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
    }
}

async function cancelReservation(reservationId) {
    if (!confirm('Are you sure you want to cancel this reservation?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/reservations/${reservationId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                status: 'cancelled'
            })
        });
        
        if (response.ok) {
            showMessage('Reservation cancelled successfully', 'success');
            loadAllReservations(); // Reload reservations list
        } else {
            throw new Error('Failed to cancel reservation');
        }
    } catch (error) {
        console.error('Error cancelling reservation:', error);
        showMessage('Error cancelling reservation', 'error');
    }
}

function editReservation(reservationId) {
    // Load the reservation data and show edit modal
    showEditReservationForm(reservationId);
}

async function showEditReservationForm(reservationId) {
    try {
        // Fetch the current reservation data
        const response = await fetch(`${API_BASE_URL}/api/admin/reservations/${reservationId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const reservation = await response.json();
            
            // Load rooms and tables for the form
            await loadRooms();
            await loadTablesData();
            
            // Create and show edit modal
            const modal = document.createElement('div');
            modal.id = 'editReservationModal';
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content large-modal">
                    <div class="modal-header">
                        <h4>Edit Reservation - ${reservation.customer_name}</h4>
                        <button class="close-btn" onclick="hideEditReservationForm()">&times;</button>
                    </div>
                    <form id="editReservationForm" onsubmit="handleEditReservation(event, '${reservationId}')">
                        <div class="form-row">
                            <div class="form-group">
                                <label for="editCustomerName">Customer Name *</label>
                                <input type="text" id="editCustomerName" name="customerName" value="${reservation.customer_name}" required>
                            </div>
                            <div class="form-group">
                                <label for="editEmail">Email *</label>
                                <input type="email" id="editEmail" name="email" value="${reservation.email}" required>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="editPhone">Phone *</label>
                                <input type="tel" id="editPhone" name="phone" value="${reservation.phone}" required>
                            </div>
                            <div class="form-group">
                                <label for="editReservationType">Type *</label>
                                <select id="editReservationType" name="reservationType" required>
                                    <option value="dining" ${reservation.reservation_type === 'dining' ? 'selected' : ''}>Dining</option>
                                    <option value="fun" ${reservation.reservation_type === 'fun' ? 'selected' : ''}>Fun</option>
                                    <option value="team_event" ${reservation.reservation_type === 'team_event' ? 'selected' : ''}>Team Event</option>
                                    <option value="birthday" ${reservation.reservation_type === 'birthday' ? 'selected' : ''}>Birthday</option>
                                    <option value="party" ${reservation.reservation_type === 'party' ? 'selected' : ''}>Party</option>
                                    <option value="special_event" ${reservation.reservation_type === 'special_event' ? 'selected' : ''}>Special Event</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="editDate">Date *</label>
                                <input type="date" id="editDate" name="date" value="${reservation.date}" required>
                            </div>
                            <div class="form-group">
                                <label for="editTime">Time *</label>
                                <select id="editTime" name="time" required>
                                    <option value="${reservation.time}">${reservation.time}</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="editPartySize">Party Size *</label>
                                <select id="editPartySize" name="partySize" required>
                                    <!-- Will be populated dynamically -->
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="editStatus">Status *</label>
                                <select id="editStatus" name="status" required>
                                    <option value="pending" ${reservation.status === 'pending' ? 'selected' : ''}>Pending</option>
                                    <option value="confirmed" ${reservation.status === 'confirmed' ? 'selected' : ''}>Confirmed</option>
                                    <option value="cancelled" ${reservation.status === 'cancelled' ? 'selected' : ''}>Cancelled</option>
                                    <option value="completed" ${reservation.status === 'completed' ? 'selected' : ''}>Completed</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="editRoom">Room</label>
                                <select id="editRoom" name="room">
                                    <option value="">Any room</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="editTables">Assigned Tables</label>
                                <div id="editTablesContainer" class="tables-selection">
                                    <div class="current-tables">
                                        <strong>Current Tables:</strong>
                                        <div id="currentTablesList">
                                            ${reservation.tables ? reservation.tables.map(t => `${t.table_name} (${t.capacity})`).join(', ') : 'None assigned'}
                                        </div>
                                    </div>
                                    <div class="table-selection-controls">
                                        <button type="button" class="btn btn-sm btn-secondary" onclick="showTableSelectionModal('${reservationId}')">
                                            <i class="fas fa-edit"></i> Change Tables
                                        </button>
                                        <button type="button" class="btn btn-sm btn-danger" onclick="clearAssignedTables('${reservationId}')">
                                            <i class="fas fa-times"></i> Clear Tables
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="form-group">
                            <label for="editNotes">Customer Notes</label>
                            <textarea id="editNotes" name="notes" rows="2">${reservation.notes || ''}</textarea>
                        </div>
                        <div class="form-group">
                            <label for="editAdminNotes">Admin Notes (Internal)</label>
                            <textarea id="editAdminNotes" name="adminNotes" rows="2">${reservation.admin_notes || ''}</textarea>
                        </div>
                        <div class="form-actions">
                            <button type="button" class="btn btn-secondary" onclick="hideEditReservationForm()">Cancel</button>
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save"></i> Update Reservation
                            </button>
                        </div>
                    </form>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Populate party size dropdown
            const partySizeSelect = document.getElementById('editPartySize');
            if (partySizeSelect) {
                populatePartySizeDropdown(partySizeSelect, 20);
                partySizeSelect.value = reservation.party_size;
            }
            
            // Populate room dropdown
            const roomSelect = document.getElementById('editRoom');
            if (roomSelect && window.loadedRooms) {
                window.loadedRooms.forEach(room => {
                    const option = document.createElement('option');
                    option.value = room.id;
                    option.textContent = room.name;
                    if (reservation.room_id === room.id) {
                        option.selected = true;
                    }
                    roomSelect.appendChild(option);
                });
            }
            
            // Set up date change handler to update time slots
            const dateInput = document.getElementById('editDate');
            const timeSelect = document.getElementById('editTime');
            if (dateInput && timeSelect) {
                dateInput.addEventListener('change', function() {
                    updateTimeSlotsForDate(this, 'editTime');
                });
            }
            
        } else {
            throw new Error('Failed to load reservation data');
        }
    } catch (error) {
        console.error('Error showing edit form:', error);
        showMessage('Error loading reservation data: ' + error.message, 'error');
    }
}

function hideEditReservationForm() {
    const modal = document.getElementById('editReservationModal');
    if (modal) {
        modal.remove();
    }
}

async function showTableSelectionModal(reservationId) {
    try {
        // Fetch available tables for the reservation
        const response = await fetch(`${API_BASE_URL}/api/admin/reservations/${reservationId}/available-tables`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const availableTables = data.available_tables;
            const currentTables = data.current_tables || [];
            const partySize = data.party_size;
            const currentTotalCapacity = data.current_total_capacity;
            const seatsShortage = data.seats_shortage;
            const seatsExcess = data.seats_excess;
            const capacityStatus = data.capacity_status;
            
            // Create capacity status message
            let capacityMessage = '';
            let capacityClass = '';
            if (capacityStatus === 'perfect') {
                capacityMessage = `Perfect! ${currentTotalCapacity} seats for ${partySize} people`;
                capacityClass = 'capacity-perfect';
            } else if (capacityStatus === 'shortage') {
                capacityMessage = `Need ${seatsShortage} more seats (${currentTotalCapacity}/${partySize})`;
                capacityClass = 'capacity-shortage';
            } else {
                capacityMessage = `${seatsExcess} extra seats (${currentTotalCapacity}/${partySize})`;
                capacityClass = 'capacity-excess';
            }
            
            // Create table selection modal
            const modal = document.createElement('div');
            modal.id = 'tableSelectionModal';
            modal.className = 'modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <div class="modal-header">
                        <h4>Select Tables for Reservation</h4>
                        <button class="close-btn" onclick="hideTableSelectionModal()">&times;</button>
                    </div>
                    <div class="table-selection-content">
                        <div class="capacity-info ${capacityClass}">
                            <h5>Party Size: ${partySize} people</h5>
                            <div class="capacity-status">${capacityMessage}</div>
                        </div>
                        <div class="current-selection">
                            <h5>Currently Selected:</h5>
                            <div id="selectedTablesList">
                                ${currentTables.map(t => `<span class="selected-table" data-table-id="${t.id}">${t.table_name} (${t.capacity})</span>`).join('')}
                            </div>
                            <div id="currentCapacityInfo" class="capacity-summary">
                                Total: ${currentTotalCapacity} seats
                            </div>
                        </div>
                        <div class="available-tables">
                            <h5>Available Tables:</h5>
                            <div class="tables-grid">
                                ${availableTables.map(table => `
                                    <div class="table-option ${currentTables.some(t => t.id === table.id) ? 'selected' : ''}" 
                                         data-table-id="${table.id}"
                                         onclick="toggleTableSelection('${table.id}', '${table.name}', ${table.capacity})">
                                        <div class="table-name">${table.name}</div>
                                        <div class="table-capacity">${table.capacity} seats</div>
                                        <div class="table-room">${table.room_name}</div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                    <div class="modal-actions">
                        <button type="button" class="btn btn-secondary" onclick="hideTableSelectionModal()">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="saveTableSelection('${reservationId}')">
                            <i class="fas fa-save"></i> Save Table Selection
                        </button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to load available tables');
        }
    } catch (error) {
        console.error('Error showing table selection modal:', error);
        showMessage('Error loading available tables: ' + error.message, 'error');
    }
}

function hideTableSelectionModal() {
    const modal = document.getElementById('tableSelectionModal');
    if (modal) {
        modal.remove();
    }
}

function toggleTableSelection(tableId, tableName, capacity) {
    const tableOption = document.querySelector(`[data-table-id="${tableId}"]`);
    const selectedTablesList = document.getElementById('selectedTablesList');
    const currentCapacityInfo = document.getElementById('currentCapacityInfo');
    
    if (tableOption.classList.contains('selected')) {
        // Remove from selection
        tableOption.classList.remove('selected');
        const tableSpan = selectedTablesList.querySelector(`[data-table-id="${tableId}"]`);
        if (tableSpan) {
            tableSpan.remove();
        }
    } else {
        // Add to selection
        tableOption.classList.add('selected');
        const tableSpan = document.createElement('span');
        tableSpan.className = 'selected-table';
        tableSpan.setAttribute('data-table-id', tableId);
        tableSpan.textContent = `${tableName} (${capacity})`;
        selectedTablesList.appendChild(tableSpan);
    }
    
    // Update capacity summary
    if (currentCapacityInfo) {
        const selectedTables = Array.from(selectedTablesList.querySelectorAll('.selected-table'));
        const totalCapacity = selectedTables.reduce((sum, span) => {
            const capacityText = span.textContent.match(/\((\d+)\)/);
            return sum + (capacityText ? parseInt(capacityText[1]) : 0);
        }, 0);
        
        // Get party size from the modal header
        const partySizeElement = document.querySelector('.capacity-info h5');
        const partySizeMatch = partySizeElement?.textContent.match(/(\d+)/);
        const partySize = partySizeMatch ? parseInt(partySizeMatch[1]) : 0;
        
        let capacityMessage = `Total: ${totalCapacity} seats`;
        if (partySize > 0) {
            if (totalCapacity === partySize) {
                capacityMessage += ` (Perfect!)`;
            } else if (totalCapacity < partySize) {
                const shortage = partySize - totalCapacity;
                capacityMessage += ` (Need ${shortage} more)`;
            } else {
                const excess = totalCapacity - partySize;
                capacityMessage += ` (${excess} extra)`;
            }
        }
        
        currentCapacityInfo.textContent = capacityMessage;
    }
}

async function saveTableSelection(reservationId) {
    try {
        const selectedTables = Array.from(document.querySelectorAll('#selectedTablesList .selected-table'))
            .map(span => span.getAttribute('data-table-id'));
        
        const response = await fetch(`${API_BASE_URL}/api/admin/reservations/${reservationId}/tables`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                table_ids: selectedTables
            })
        });
        
        if (response.ok) {
            showMessage('Table assignment updated successfully', 'success');
            hideTableSelectionModal();
            
            // Update the current tables display in the edit form
            const currentTablesList = document.getElementById('currentTablesList');
            if (currentTablesList) {
                const tableNames = selectedTables.map(tableId => {
                    const tableOption = document.querySelector(`[data-table-id="${tableId}"]`);
                    if (tableOption) {
                        const name = tableOption.querySelector('.table-name')?.textContent || 'Unknown';
                        const capacity = tableOption.querySelector('.table-capacity')?.textContent || '';
                        return `${name} (${capacity})`;
                    }
                    return '';
                }).filter(name => name);
                currentTablesList.textContent = tableNames.join(', ') || 'None assigned';
            }
        } else {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to update table assignment');
        }
    } catch (error) {
        console.error('Error saving table selection:', error);
        showMessage('Error updating table assignment: ' + error.message, 'error');
    }
}

async function clearAssignedTables(reservationId) {
    if (!confirm('Are you sure you want to clear all assigned tables for this reservation?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/reservations/${reservationId}/tables`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                table_ids: []
            })
        });
        
        if (response.ok) {
            showMessage('Table assignment cleared successfully', 'success');
            
            // Update the current tables display
            const currentTablesList = document.getElementById('currentTablesList');
            if (currentTablesList) {
                currentTablesList.textContent = 'None assigned';
            }
        } else {
            throw new Error('Failed to clear table assignment');
        }
    } catch (error) {
        console.error('Error clearing table assignment:', error);
        showMessage('Error clearing table assignment: ' + error.message, 'error');
    }
}

async function handleEditReservation(event, reservationId) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const reservationData = {
        customer_name: formData.get('customerName'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        party_size: parseInt(formData.get('partySize')),
        date: formData.get('date'),
        time: formData.get('time'),
        reservation_type: formData.get('reservationType'),
        status: formData.get('status'),
        notes: formData.get('notes') || null,
        admin_notes: formData.get('adminNotes') || null
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/reservations/${reservationId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(reservationData)
        });
        
        if (response.ok) {
            showMessage('Reservation updated successfully', 'success');
            hideEditReservationForm();
            loadAllReservations(); // Reload reservations list
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update reservation');
        }
    } catch (error) {
        console.error('Error updating reservation:', error);
        showMessage('Error updating reservation: ' + error.message, 'error');
    }
} 