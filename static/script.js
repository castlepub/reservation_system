// API Configuration
const API_BASE_URL = window.location.origin;
let authToken = localStorage.getItem('authToken');
let dashboardStats = null;
let chartInstance = null;

// DOM Elements - will be initialized after DOM loads
let sections = {};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Initialize sections after DOM is loaded
    sections = {
        home: document.getElementById('home'),
        reservations: document.getElementById('reservations'),
        admin: document.getElementById('admin'),
        adminDashboard: document.getElementById('adminDashboard')
    };
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
        
        // Check URL parameters for tab
        const urlParams = new URLSearchParams(window.location.search);
        const tabParam = urlParams.get('tab');
        
        if (tabParam) {
            // Show the tab from URL parameter
            showTab(tabParam);
        } else {
            // Default to dashboard
            loadDashboardData();
        }
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
    
    // Room management forms
    const addRoomForm = document.getElementById('addRoomForm');
    const editRoomForm = document.getElementById('editRoomForm');
    if (addRoomForm) {
        addRoomForm.addEventListener('submit', handleAddRoom);
    }
    if (editRoomForm) {
        editRoomForm.addEventListener('submit', handleEditRoom);
    }

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

// PDF Generation Functions
async function generateDailyPDF() {
    try {
        const today = new Date().toISOString().split('T')[0];
        const response = await fetch(`${API_BASE_URL}/admin/reports/daily?report_date=${today}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = `daily_report_${today}.html`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            showMessage('Daily PDF report generated successfully!', 'success');
        } else {
            throw new Error('Failed to generate PDF');
        }
    } catch (error) {
        console.error('Error generating daily PDF:', error);
        showMessage('Error generating PDF report', 'error');
    }
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
    // Update URL without page reload
    const url = new URL(window.location);
    url.searchParams.set('tab', tabName);
    window.history.pushState({}, '', url);
    
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab content
    const selectedTab = document.getElementById(tabName + 'Tab');
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to selected tab button
    const selectedButton = document.querySelector(`[onclick="showTab('${tabName}')"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
    
    // Load data for specific tabs
    if (tabName === 'dailyView') {
        loadDailyView();
    } else if (tabName === 'today') {
        loadTodayReservations();
    } else if (tabName === 'dashboard') {
        loadDashboardData();
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
        duration_hours: parseInt(formData.get('duration')),
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
    const username = formData.get('username');
    const password = formData.get('password');
    
    try {
        showLoading();
        
        // Use proper auth endpoint
        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({
                'username': username,
                'password': password
            })
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
    console.log('showReservationForm called');
    // Open the same modal as the "+ Add Reservation" button
    showAddReservationForm();
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
    const date = document.getElementById('date').value;
    const partySize = document.getElementById('partySize').value;
    const duration = document.getElementById('duration').value;
    const room = document.getElementById('room').value;
    
    if (date && partySize && duration) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/availability`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    date: date,
                    party_size: parseInt(partySize),
                    duration_hours: parseInt(duration),
                    room_id: room || null
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                updateTimeSlotsDisplay(data.available_slots);
            } else {
                console.error('Availability check failed');
            }
        } catch (error) {
            console.error('Error checking availability:', error);
        }
    }
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
            loadRestaurantSettings(),
            loadSpecialDays()
        ]);
        
        // Initialize layout editor
        initializeLayoutEditorOnLoad();
        
    } catch (error) {
        console.error('Error loading settings data:', error);
        showMessage('Error loading settings', 'error');
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
        const response = await fetch(`${API_BASE_URL}/admin/rooms`, {
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
        const response = await fetch(`${API_BASE_URL}/admin/tables`, {
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
        const response = await fetch(`${API_BASE_URL}/admin/tables`, {
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
        const response = await fetch(`${API_BASE_URL}/admin/tables/${tableId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            showMessage('Table deleted successfully', 'success');
            loadTables(); // Reload tables
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete table');
        }
    } catch (error) {
        console.error('Error deleting table:', error);
        showMessage('Error deleting table: ' + error.message, 'error');
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
        let url = `${API_BASE_URL}/admin/reservations`;
        
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
    console.log('showAddReservationForm called');
    
    const modal = document.getElementById('addReservationModal');
    console.log('Modal element:', modal);
    
    if (!modal) {
        console.error('addReservationModal not found!');
        showMessage('Modal not found - please refresh the page', 'error');
        return;
    }
    
    modal.classList.remove('hidden');
    console.log('Modal should now be visible');
    
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
    // Parse time string to proper format
    const timeString = formData.get('time');
    let timeValue = timeString;
    
    // If time is in HH:MM format, convert it to proper time format
    if (timeString && timeString.includes(':')) {
        const [hours, minutes] = timeString.split(':');
        timeValue = `${hours.padStart(2, '0')}:${minutes.padStart(2, '0')}:00`;
    }
    
    const reservationData = {
        customer_name: formData.get('customerName'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        party_size: parseInt(formData.get('partySize')),
        date: formData.get('date'),
        time: timeValue,
        duration_hours: parseInt(formData.get('duration')),
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
        const response = await fetch(`${API_BASE_URL}/admin/reservations/${reservationId}`, {
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
        const response = await fetch(`${API_BASE_URL}/admin/reservations/${reservationId}/available-tables`, {
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
        
        const response = await fetch(`${API_BASE_URL}/admin/reservations/${reservationId}/tables`, {
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
        const response = await fetch(`${API_BASE_URL}/admin/reservations/${reservationId}/tables`, {
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
        const response = await fetch(`${API_BASE_URL}/admin/reservations/${reservationId}`, {
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

// Daily View Variables
let currentViewDate = new Date();
let currentRoomId = null;
let dailyViewData = null;

// Daily View Functions
function showTab(tabName) {
    // Update URL without page reload
    const url = new URL(window.location);
    url.searchParams.set('tab', tabName);
    window.history.pushState({}, '', url);
    
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab content
    const selectedTab = document.getElementById(tabName + 'Tab');
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to selected tab button
    const selectedButton = document.querySelector(`[onclick="showTab('${tabName}')"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
    
    // Load data for specific tabs
    if (tabName === 'dailyView') {
        loadDailyView();
    } else if (tabName === 'today') {
        loadTodayReservations();
    } else if (tabName === 'dashboard') {
        loadDashboardData();
    }
}

async function loadDailyView() {
    try {
        const dateStr = currentViewDate.toISOString().split('T')[0];
        const response = await fetch(`${API_BASE_URL}/api/layout/daily/${dateStr}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            dailyViewData = await response.json();
            updateDateDisplay();
            renderReservationsList();
            renderRoomTabs();
            renderTableLayout();
        } else {
            throw new Error('Failed to load daily view');
        }
    } catch (error) {
        console.error('Error loading daily view:', error);
        showMessage('Error loading daily view', 'error');
    }
}

function updateDateDisplay() {
    const dateDisplay = document.getElementById('currentDate');
    if (dateDisplay) {
        const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
        dateDisplay.textContent = currentViewDate.toLocaleDateString('en-US', options);
    }
}

function renderReservationsList() {
    const container = document.getElementById('dailyReservationsList');
    if (!container || !dailyViewData) return;
    
    container.innerHTML = '';
    
    // Handle case where reservations array is undefined or empty
    if (!dailyViewData.reservations || !Array.isArray(dailyViewData.reservations) || dailyViewData.reservations.length === 0) {
        container.innerHTML = '<div class="no-reservations-message">No reservations for this date</div>';
        return;
    }
    
    dailyViewData.reservations.forEach(reservation => {
        const reservationElement = document.createElement('div');
        reservationElement.className = 'reservation-item';
        reservationElement.onclick = () => selectReservation(reservation.id);
        
        const timeRange = `${reservation.time}-${addHours(reservation.time, reservation.duration_hours || 2)}`;
        
        reservationElement.innerHTML = `
            <div class="reservation-header">
                <span class="reservation-time">${timeRange}</span>
                <span class="reservation-party">${reservation.party_size}p</span>
            </div>
            <div class="reservation-customer">${reservation.customer_name}</div>
            <div class="reservation-details">
                ${reservation.room_name} • ${reservation.reservation_type}
                ${reservation.notes ? `<br><small>${reservation.notes}</small>` : ''}
            </div>
            ${reservation.table_names && reservation.table_names.length > 0 ? 
                `<div class="reservation-tables">Tables: ${reservation.table_names.join(', ')}</div>` : 
                '<div class="reservation-tables">No tables assigned</div>'
            }
        `;
        
        container.appendChild(reservationElement);
    });
}

function renderRoomTabs() {
    const container = document.getElementById('roomTabs');
    if (!container || !dailyViewData || !dailyViewData.rooms) return;
    
    container.innerHTML = '';
    
    // Handle case where rooms array is empty
    if (!Array.isArray(dailyViewData.rooms) || dailyViewData.rooms.length === 0) {
        container.innerHTML = '<div class="no-rooms-message">No rooms available</div>';
        return;
    }
    
    dailyViewData.rooms.forEach((room, index) => {
        const tabElement = document.createElement('button');
        tabElement.className = `room-tab ${index === 0 ? 'active' : ''}`;
        tabElement.textContent = room.name;
        tabElement.onclick = () => switchRoom(room.id);
        
        container.appendChild(tabElement);
        
        if (index === 0) {
            currentRoomId = room.id;
        }
    });
}

function renderTableLayout() {
    const container = document.getElementById('tableLayout');
    if (!container || !dailyViewData || !currentRoomId) return;
    
    container.innerHTML = '';
    
    const currentRoom = dailyViewData.rooms.find(room => room.id === currentRoomId);
    if (!currentRoom) {
        container.innerHTML = '<div class="no-room-message">Room not found</div>';
        return;
    }
    
    // Add room features
    if (currentRoom.layout?.show_entrance) {
        const entrance = document.createElement('div');
        entrance.className = 'room-entrance';
        entrance.textContent = 'ENTRANCE';
        container.appendChild(entrance);
    }
    
    if (currentRoom.layout?.show_bar) {
        const bar = document.createElement('div');
        bar.className = 'room-bar';
        bar.textContent = 'BAR';
        container.appendChild(bar);
    }
    
    // Handle case where tables array is undefined or empty
    if (!currentRoom.tables || !Array.isArray(currentRoom.tables) || currentRoom.tables.length === 0) {
        container.innerHTML += '<div class="no-tables-message">No tables in this room</div>';
        return;
    }
    
    // Add tables
    currentRoom.tables.forEach(table => {
        const tableElement = document.createElement('div');
        tableElement.className = `table-element ${table.layout?.shape || 'rectangular'}`;
        tableElement.style.left = `${table.layout?.x_position || 50}px`;
        tableElement.style.top = `${table.layout?.y_position || 50}px`;
        tableElement.style.width = `${table.layout?.width || 80}px`;
        tableElement.style.height = `${table.layout?.height || 60}px`;
        tableElement.style.backgroundColor = table.layout?.color || '#4A90E2';
        tableElement.style.borderColor = table.layout?.border_color || '#2E5BBA';
        tableElement.style.color = table.layout?.text_color || '#FFFFFF';
        tableElement.style.fontSize = `${table.layout?.font_size || 12}px`;
        tableElement.style.zIndex = table.layout?.z_index || 1;
        
        tableElement.innerHTML = `
            ${table.layout?.show_name !== false ? `<div class="table-name">${table.name}</div>` : ''}
            ${table.layout?.show_capacity !== false ? `<div class="table-capacity">${table.capacity}p</div>` : ''}
        `;
        
        // Determine table status
        const tableReservations = getTableReservations(table.id);
        if (tableReservations.length > 0) {
            tableElement.classList.add('reserved');
            tableElement.title = `Reserved: ${tableReservations.map(r => `${r.customer_name} (${r.time})`).join(', ')}`;
        } else {
            tableElement.classList.add('available');
            tableElement.title = `Available: ${table.name} (${table.capacity} seats)`;
        }
        
        tableElement.onclick = () => showTableDetails(table.id);
        container.appendChild(tableElement);
    });
}

function getTableReservations(tableId) {
    if (!dailyViewData) return [];
    
    return dailyViewData.reservations.filter(reservation => 
        reservation.table_names.some(tableName => {
            const table = dailyViewData.rooms
                .flatMap(room => room.tables)
                .find(t => t.id === tableId);
            return table && table.name === tableName;
        })
    );
}

function switchRoom(roomId) {
    currentRoomId = roomId;
    
    // Update active tab
    const tabs = document.querySelectorAll('.room-tab');
    tabs.forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');
    
    renderTableLayout();
}

function selectReservation(reservationId) {
    // Remove previous selection
    document.querySelectorAll('.reservation-item').forEach(item => 
        item.classList.remove('selected')
    );
    
    // Add selection to clicked item
    event.target.closest('.reservation-item').classList.add('selected');
    
    // Highlight related tables
    highlightReservationTables(reservationId);
}

function highlightReservationTables(reservationId) {
    const reservation = dailyViewData.reservations.find(r => r.id === reservationId);
    if (!reservation) return;
    
    // Reset all table highlights
    document.querySelectorAll('.table-element').forEach(table => {
        table.style.boxShadow = '';
        table.style.transform = '';
    });
    
    // Highlight tables for this reservation
    reservation.table_names.forEach(tableName => {
        const tableElement = document.querySelector(`[title*="${tableName}"]`);
        if (tableElement) {
            tableElement.style.boxShadow = '0 0 10px #667eea';
            tableElement.style.transform = 'scale(1.1)';
        }
    });
}

function showTableDetails(tableId) {
    const table = dailyViewData.rooms
        .flatMap(room => room.tables)
        .find(t => t.id === tableId);
    
    if (!table) return;
    
    const reservations = getTableReservations(tableId);
    let details = `Table: ${table.name}\nCapacity: ${table.capacity} seats\nRoom: ${table.room_name}`;
    
    if (reservations.length > 0) {
        details += '\n\nReservations:';
        reservations.forEach(r => {
            details += `\n• ${r.customer_name} (${r.time}-${addHours(r.time, r.duration_hours)})`;
        });
    } else {
        details += '\n\nStatus: Available';
    }
    
    alert(details);
}

function previousDay() {
    currentViewDate.setDate(currentViewDate.getDate() - 1);
    loadDailyView();
}

function nextDay() {
    currentViewDate.setDate(currentViewDate.getDate() + 1);
    loadDailyView();
}

function goToToday() {
    currentViewDate = new Date();
    loadDailyView();
}

function filterReservations(filter) {
    // Update active filter button
    document.querySelectorAll('.filter-buttons .btn').forEach(btn => 
        btn.classList.remove('active')
    );
    event.target.classList.add('active');
    
    // Filter reservations (implement based on your needs)
    console.log('Filtering reservations:', filter);
}

function addHours(timeStr, hours) {
    const [hours_str, minutes] = timeStr.split(':');
    const date = new Date();
    date.setHours(parseInt(hours_str), parseInt(minutes), 0);
    date.setHours(date.getHours() + hours);
    return date.toTimeString().slice(0, 5);
}

async function editTable(tableId) {
    try {
        // Get table details
        const response = await fetch(`${API_BASE_URL}/admin/tables/${tableId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch table details');
        }
        
        const table = await response.json();
        
        // Populate room dropdown in edit modal
        const editRoomSelect = document.getElementById('editTableRoom');
        if (editRoomSelect) {
            // Get rooms data from the current state or fetch it
            const roomsResponse = await fetch(`${API_BASE_URL}/admin/rooms`, {
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            });
            
            if (roomsResponse.ok) {
                const rooms = await roomsResponse.json();
                editRoomSelect.innerHTML = '<option value="">Select Room</option>';
                rooms.forEach(room => {
                    const option = document.createElement('option');
                    option.value = room.id;
                    option.textContent = room.name;
                    editRoomSelect.appendChild(option);
                });
            }
        }
        
        // Populate edit form
        document.getElementById('editTableId').value = table.id;
        document.getElementById('editTableName').value = table.name;
        document.getElementById('editTableCapacity').value = table.capacity;
        document.getElementById('editTableCombinable').checked = table.combinable;
        document.getElementById('editTableRoom').value = table.room_id;
        
        // Show edit modal
        document.getElementById('editTableModal').classList.remove('hidden');
        
    } catch (error) {
        console.error('Error loading table for edit:', error);
        showMessage('Error loading table details: ' + error.message, 'error');
    }
}

async function handleEditTable(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const tableId = formData.get('table_id');
    const tableData = {
        room_id: formData.get('room_id'),
        name: formData.get('name'),
        capacity: parseInt(formData.get('capacity')),
        combinable: formData.get('combinable') === 'on'
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/admin/tables/${tableId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(tableData)
        });
        
        if (response.ok) {
            showMessage('Table updated successfully', 'success');
            hideEditTableForm();
            loadTables(); // Reload tables
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update table');
        }
    } catch (error) {
        console.error('Error updating table:', error);
        showMessage('Error updating table: ' + error.message, 'error');
    }
}

function hideEditTableForm() {
    document.getElementById('editTableModal').classList.add('hidden');
    document.getElementById('editTableForm').reset();
}

// Layout Editor Variables
let currentLayoutRoom = null;
let currentLayoutData = null;
let selectedTable = null;
let isDragging = false;
let dragOffset = { x: 0, y: 0 };
let gridEnabled = true;
let tableCounter = 1;

// Layout Editor Functions
async function initializeLayoutEditor() {
    try {
        // Load rooms for layout editor
        const response = await fetch(`${API_BASE_URL}/admin/rooms`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const rooms = await response.json();
            const roomSelect = document.getElementById('layoutRoomSelect');
            roomSelect.innerHTML = '<option value="">Choose a room...</option>';
            
            rooms.forEach(room => {
                const option = document.createElement('option');
                option.value = room.id;
                option.textContent = room.name;
                roomSelect.appendChild(option);
            });
            
            // Add event listener for room selection
            roomSelect.addEventListener('change', handleRoomSelection);
        }
    } catch (error) {
        console.error('Error initializing layout editor:', error);
        showMessage('Error loading rooms for layout editor', 'error');
    }
}

async function handleRoomSelection(event) {
    const roomId = event.target.value;
    if (!roomId) {
        clearLayoutCanvas();
        return;
    }
    
    currentLayoutRoom = roomId;
    await loadRoomLayout(roomId);
}

async function loadRoomLayout(roomId) {
    try {
        const today = new Date().toISOString().split('T')[0];
        const response = await fetch(`${API_BASE_URL}/api/layout/editor/${roomId}?target_date=${today}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            currentLayoutData = await response.json();
            renderLayoutCanvas();
            renderLayoutReservations();
        } else {
            throw new Error('Failed to load room layout');
        }
    } catch (error) {
        console.error('Error loading room layout:', error);
        showMessage('Error loading room layout', 'error');
    }
}

function renderLayoutCanvas() {
    const canvas = document.getElementById('layoutCanvas');
    canvas.innerHTML = '';
    
    if (!currentLayoutData) return;
    
    // Set canvas size based on room layout
    const roomLayout = currentLayoutData.room_layout;
    canvas.style.width = `${roomLayout.width}px`;
    canvas.style.height = `${roomLayout.height}px`;
    canvas.style.backgroundColor = roomLayout.background_color;
    
    // Add grid if enabled
    if (gridEnabled) {
        canvas.classList.add('grid-enabled');
    } else {
        canvas.classList.remove('grid-enabled');
    }
    
    // Add room features
    if (roomLayout.show_entrance) {
        const entrance = document.createElement('div');
        entrance.className = 'room-entrance';
        entrance.textContent = 'ENTRANCE';
        canvas.appendChild(entrance);
    }
    
    if (roomLayout.show_bar) {
        const bar = document.createElement('div');
        bar.className = 'room-bar';
        bar.textContent = 'BAR';
        canvas.appendChild(bar);
    }
    
    // Render tables
    currentLayoutData.tables.forEach(table => {
        const tableElement = createTableElement(table);
        canvas.appendChild(tableElement);
    });
    
    // Add click handler for canvas
    canvas.addEventListener('click', handleCanvasClick);
}

function createTableElement(tableData) {
    const tableElement = document.createElement('div');
    tableElement.className = `layout-table ${tableData.shape} ${getTableStatus(tableData)}`;
    tableElement.style.left = `${tableData.x_position}px`;
    tableElement.style.top = `${tableData.y_position}px`;
    tableElement.style.width = `${tableData.width}px`;
    tableElement.style.height = `${tableData.height}px`;
    tableElement.style.backgroundColor = tableData.color;
    tableElement.style.borderColor = tableData.border_color;
    tableElement.style.color = tableData.text_color;
    tableElement.style.fontSize = `${tableData.font_size}px`;
    tableElement.style.zIndex = tableData.z_index;
    
    // Add table content
    let content = '';
    if (tableData.show_name) {
        content += `<div class="table-name">${tableData.table_name}</div>`;
    }
    if (tableData.show_capacity) {
        content += `<div class="table-capacity">${tableData.capacity}p</div>`;
    }
    tableElement.innerHTML = content;
    
    // Add event listeners
    tableElement.addEventListener('click', (e) => {
        e.stopPropagation();
        selectTable(tableData.layout_id, tableElement);
    });
    
    tableElement.addEventListener('dblclick', (e) => {
        e.stopPropagation();
        openTableReservation(tableData);
    });
    
    // Make draggable
    makeTableDraggable(tableElement, tableData);
    
    return tableElement;
}

function getTableStatus(tableData) {
    if (tableData.reservations && tableData.reservations.length > 0) {
        return 'reserved';
    }
    return 'available';
}

function selectTable(layoutId, element) {
    // Remove previous selection
    document.querySelectorAll('.layout-table.selected').forEach(table => {
        table.classList.remove('selected');
    });
    
    // Add selection
    element.classList.add('selected');
    selectedTable = layoutId;
    
    // Show properties panel
    showTableProperties(layoutId);
}

function showTableProperties(layoutId) {
    const tableData = currentLayoutData.tables.find(t => t.layout_id === layoutId);
    if (!tableData) return;
    
    // Populate properties form
    document.getElementById('layoutTableName').value = tableData.table_name;
    document.getElementById('tableCapacity').value = tableData.capacity;
    document.getElementById('tableShape').value = tableData.shape;
    document.getElementById('tableColor').value = tableData.color;
    document.getElementById('tableShowName').checked = tableData.show_name;
    document.getElementById('tableShowCapacity').checked = tableData.show_capacity;
    
    // Show properties panel
    document.getElementById('tableProperties').style.display = 'block';
}

function makeTableDraggable(element, tableData) {
    element.addEventListener('mousedown', (e) => {
        if (e.target === element) {
            isDragging = true;
            selectedTable = tableData.layout_id;
            
            const rect = element.getBoundingClientRect();
            const canvasRect = document.getElementById('layoutCanvas').getBoundingClientRect();
            
            dragOffset.x = e.clientX - rect.left;
            dragOffset.y = e.clientY - rect.top;
            
            element.classList.add('dragging');
            
            e.preventDefault();
        }
    });
    
    document.addEventListener('mousemove', (e) => {
        if (isDragging && selectedTable) {
            const canvas = document.getElementById('layoutCanvas');
            const canvasRect = canvas.getBoundingClientRect();
            
            let newX = e.clientX - canvasRect.left - dragOffset.x;
            let newY = e.clientY - canvasRect.top - dragOffset.y;
            
            // Snap to grid if enabled
            if (gridEnabled) {
                newX = Math.round(newX / 20) * 20;
                newY = Math.round(newY / 20) * 20;
            }
            
            // Keep within canvas bounds
            newX = Math.max(0, Math.min(newX, canvas.offsetWidth - element.offsetWidth));
            newY = Math.max(0, Math.min(newY, canvas.offsetHeight - element.offsetHeight));
            
            element.style.left = `${newX}px`;
            element.style.top = `${newY}px`;
        }
    });
    
    document.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            document.querySelectorAll('.layout-table.dragging').forEach(table => {
                table.classList.remove('dragging');
            });
            
            // Auto-save position
            if (selectedTable) {
                updateTablePosition(selectedTable);
            }
        }
    });
}

async function updateTablePosition(layoutId) {
    try {
        const tableElement = document.querySelector(`.layout-table.selected`);
        if (!tableElement) return;
        
        const x = parseFloat(tableElement.style.left);
        const y = parseFloat(tableElement.style.top);
        
        const response = await fetch(`${API_BASE_URL}/api/layout/tables/${layoutId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                x_position: x,
                y_position: y
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to update table position');
        }
        
        // Update local data
        const tableData = currentLayoutData.tables.find(t => t.layout_id === layoutId);
        if (tableData) {
            tableData.x_position = x;
            tableData.y_position = y;
        }
    } catch (error) {
        console.error('Error updating table position:', error);
        showMessage('Error updating table position', 'error');
    }
}

function addTableToLayout(shape) {
    if (!currentLayoutRoom) {
        showMessage('Please select a room first', 'warning');
        return;
    }
    
    const canvas = document.getElementById('layoutCanvas');
    const rect = canvas.getBoundingClientRect();
    
    // Default position (center of canvas)
    const x = Math.round((rect.width / 2 - 50) / 20) * 20;
    const y = Math.round((rect.height / 2 - 40) / 20) * 20;
    
    // Create new table data
    const newTable = {
        table_id: `temp_${Date.now()}`,
        room_id: currentLayoutRoom,
        x_position: x,
        y_position: y,
        width: shape === 'bar_stool' ? 40 : 100,
        height: shape === 'bar_stool' ? 40 : 80,
        shape: shape,
        color: '#4A90E2',
        border_color: '#2E5BBA',
        text_color: '#FFFFFF',
        show_capacity: true,
        show_name: true,
        font_size: 12,
        custom_capacity: 4,
        is_connected: false,
        connected_to: null,
        z_index: 1,
        table_name: `T${tableCounter++}`,
        capacity: 4,
        reservations: []
    };
    
    // Add to local data
    currentLayoutData.tables.push(newTable);
    
    // Create and add table element
    const tableElement = createTableElement(newTable);
    canvas.appendChild(tableElement);
    
    // Select the new table
    selectTable(newTable.layout_id, tableElement);
    
    // Save to backend
    saveNewTable(newTable);
}

async function saveNewTable(tableData) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/layout/tables`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                table_id: tableData.table_id,
                room_id: tableData.room_id,
                x_position: tableData.x_position,
                y_position: tableData.y_position,
                width: tableData.width,
                height: tableData.height,
                shape: tableData.shape,
                color: tableData.color,
                border_color: tableData.border_color,
                text_color: tableData.text_color,
                show_capacity: tableData.show_capacity,
                show_name: tableData.show_name,
                font_size: tableData.font_size,
                custom_capacity: tableData.custom_capacity,
                is_connected: tableData.is_connected,
                connected_to: tableData.connected_to,
                z_index: tableData.z_index
            })
        });
        
        if (response.ok) {
            const savedTable = await response.json();
            // Update the temporary ID with the real one
            const tableData = currentLayoutData.tables.find(t => t.table_id === `temp_${Date.now()}`);
            if (tableData) {
                tableData.layout_id = savedTable.id;
                tableData.table_id = savedTable.table_id;
            }
        } else {
            throw new Error('Failed to save new table');
        }
    } catch (error) {
        console.error('Error saving new table:', error);
        showMessage('Error saving new table', 'error');
    }
}

async function updateTableProperties() {
    if (!selectedTable) return;
    
    try {
        const formData = {
            table_name: document.getElementById('layoutTableName').value,
            capacity: parseInt(document.getElementById('tableCapacity').value),
            shape: document.getElementById('tableShape').value,
            color: document.getElementById('tableColor').value,
            show_name: document.getElementById('tableShowName').checked,
            show_capacity: document.getElementById('tableShowCapacity').checked
        };
        
        const response = await fetch(`${API_BASE_URL}/api/layout/tables/${selectedTable}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            // Update local data
            const tableData = currentLayoutData.tables.find(t => t.layout_id === selectedTable);
            if (tableData) {
                Object.assign(tableData, formData);
            }
            
            // Re-render canvas
            renderLayoutCanvas();
            showMessage('Table properties updated successfully', 'success');
        } else {
            throw new Error('Failed to update table properties');
        }
    } catch (error) {
        console.error('Error updating table properties:', error);
        showMessage('Error updating table properties', 'error');
    }
}

async function deleteSelectedTable() {
    if (!selectedTable) return;
    
    if (!confirm('Are you sure you want to delete this table?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/layout/tables/${selectedTable}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.ok) {
            // Remove from local data
            currentLayoutData.tables = currentLayoutData.tables.filter(t => t.layout_id !== selectedTable);
            
            // Re-render canvas
            renderLayoutCanvas();
            
            // Hide properties panel
            document.getElementById('tableProperties').style.display = 'none';
            selectedTable = null;
            
            showMessage('Table deleted successfully', 'success');
        } else {
            throw new Error('Failed to delete table');
        }
    } catch (error) {
        console.error('Error deleting table:', error);
        showMessage('Error deleting table', 'error');
    }
}

function toggleGrid() {
    gridEnabled = !gridEnabled;
    const canvas = document.getElementById('layoutCanvas');
    
    if (gridEnabled) {
        canvas.classList.add('grid-enabled');
    } else {
        canvas.classList.remove('grid-enabled');
    }
}

function renderLayoutReservations() {
    const container = document.getElementById('layoutReservationsList');
    if (!container || !currentLayoutData) return;
    
    container.innerHTML = '';
    
    if (!currentLayoutData.reservations || currentLayoutData.reservations.length === 0) {
        container.innerHTML = '<div class="no-reservations">No reservations for today</div>';
        return;
    }
    
    currentLayoutData.reservations.forEach(reservation => {
        const reservationElement = document.createElement('div');
        reservationElement.className = 'reservation-item';
        reservationElement.onclick = () => openReservationDetails(reservation.id);
        
        reservationElement.innerHTML = `
            <div class="reservation-header">
                <span class="reservation-time">${reservation.time}</span>
                <span class="reservation-party">${reservation.party_size}p</span>
            </div>
            <div class="reservation-customer">${reservation.customer_name}</div>
            <div class="reservation-type">${reservation.reservation_type}</div>
        `;
        
        container.appendChild(reservationElement);
    });
}

function openTableReservation(tableData) {
    if (tableData.reservations && tableData.reservations.length > 0) {
        // Show reservation details
        const reservation = tableData.reservations[0];
        showReservationDetails(reservation);
    } else {
        // Show table assignment options
        showTableAssignmentModal(tableData);
    }
}

function showReservationDetails(reservation) {
    // Create and show modal with reservation details
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h4>Reservation Details</h4>
                <button class="close-btn" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <p><strong>Customer:</strong> ${reservation.customer_name}</p>
                <p><strong>Time:</strong> ${reservation.time}</p>
                <p><strong>Party Size:</strong> ${reservation.party_size}</p>
                <p><strong>Type:</strong> ${reservation.reservation_type}</p>
                <p><strong>Status:</strong> ${reservation.status}</p>
                ${reservation.notes ? `<p><strong>Notes:</strong> ${reservation.notes}</p>` : ''}
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.classList.remove('hidden');
}

function showTableAssignmentModal(tableData) {
    // Create modal for table assignment
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h4>Assign Reservation to ${tableData.table_name}</h4>
                <button class="close-btn" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <p>Select a reservation to assign to this table:</p>
                <div id="assignmentReservationsList">
                    <!-- Will be populated with available reservations -->
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.classList.remove('hidden');
    
    // Populate with available reservations
    populateAssignmentReservations(tableData);
}

function populateAssignmentReservations(tableData) {
    const container = document.getElementById('assignmentReservationsList');
    if (!container || !currentLayoutData) return;
    
    const availableReservations = currentLayoutData.reservations.filter(r => 
        !r.table_names || r.table_names.length === 0
    );
    
    if (availableReservations.length === 0) {
        container.innerHTML = '<p>No unassigned reservations available</p>';
        return;
    }
    
    availableReservations.forEach(reservation => {
        const element = document.createElement('div');
        element.className = 'reservation-option';
        element.onclick = () => assignReservationToTable(reservation.id, tableData.table_id);
        
        element.innerHTML = `
            <div class="reservation-info">
                <strong>${reservation.customer_name}</strong> - ${reservation.time} (${reservation.party_size}p)
            </div>
        `;
        
        container.appendChild(element);
    });
}

async function assignReservationToTable(reservationId, tableId) {
    try {
        // This would need to be implemented in the reservation service
        // For now, just show a message
        showMessage('Table assignment feature coming soon!', 'info');
        
        // Close modal
        document.querySelector('.modal').remove();
    } catch (error) {
        console.error('Error assigning reservation to table:', error);
        showMessage('Error assigning reservation to table', 'error');
    }
}

async function saveLayout() {
    if (!currentLayoutRoom) {
        showMessage('No room selected', 'warning');
        return;
    }
    
    showMessage('Layout saved automatically', 'success');
}

async function exportLayout() {
    if (!currentLayoutRoom) {
        showMessage('No room selected', 'warning');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/layout/export/${currentLayoutRoom}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Create download link
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `layout_${currentLayoutRoom}_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showMessage('Layout exported successfully', 'success');
        } else {
            throw new Error('Failed to export layout');
        }
    } catch (error) {
        console.error('Error exporting layout:', error);
        showMessage('Error exporting layout', 'error');
    }
}

function printLayout() {
    if (!currentLayoutRoom) {
        showMessage('No room selected', 'warning');
        return;
    }
    
    // Open print dialog
    window.print();
}

function clearLayoutCanvas() {
    const canvas = document.getElementById('layoutCanvas');
    canvas.innerHTML = `
        <div class="layout-placeholder">
            <i class="fas fa-map"></i>
            <p>Select a room to start designing the layout</p>
        </div>
    `;
    
    currentLayoutData = null;
    selectedTable = null;
    document.getElementById('tableProperties').style.display = 'none';
}

function handleCanvasClick(event) {
    // Deselect table if clicking on empty canvas
    if (event.target.id === 'layoutCanvas') {
        document.querySelectorAll('.layout-table.selected').forEach(table => {
            table.classList.remove('selected');
        });
        selectedTable = null;
        document.getElementById('tableProperties').style.display = 'none';
    }
}

// Initialize layout editor when settings tab is loaded
function initializeLayoutEditorOnLoad() {
    // This function is called when the settings tab is loaded
    console.log('Layout editor initialized');
}

// Room Management Functions
async function loadRoomsForSettings() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/settings/rooms`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const rooms = await response.json();
            updateRoomsDisplay(rooms);
        } else {
            throw new Error('Failed to load rooms');
        }
    } catch (error) {
        console.error('Error loading rooms for settings:', error);
        showMessage('Error loading rooms', 'error');
    }
}

function updateRoomsDisplay(rooms) {
    const container = document.getElementById('roomsContainer');
    
    if (rooms.length === 0) {
        container.innerHTML = `
            <div class="empty-rooms">
                <i class="fas fa-door-open"></i>
                <h4>No Rooms Yet</h4>
                <p>Create your first room to get started with table management.</p>
                <button class="btn btn-primary" onclick="showAddRoomModal()">
                    <i class="fas fa-plus"></i> Add Your First Room
                </button>
            </div>
        `;
        return;
    }

    container.innerHTML = rooms.map(room => `
        <div class="room-item ${!room.active ? 'inactive' : ''}">
            <div class="room-header">
                <h5 class="room-name">${room.name}</h5>
                <div class="room-status">
                    <span class="room-status-badge ${room.active ? 'room-status-active' : 'room-status-inactive'}">
                        ${room.active ? 'Active' : 'Inactive'}
                    </span>
                </div>
            </div>
            <div class="room-description">
                ${room.description || 'No description provided'}
            </div>
            <div class="room-stats">
                <div class="room-stat">
                    <div class="room-stat-value">${room.tables ? room.tables.length : 0}</div>
                    <div class="room-stat-label">Tables</div>
                </div>
                <div class="room-stat">
                    <div class="room-stat-value">${room.reservations ? room.reservations.length : 0}</div>
                    <div class="room-stat-label">Reservations</div>
                </div>
                <div class="room-stat">
                    <div class="room-stat-value">${room.created_at ? new Date(room.created_at).toLocaleDateString() : 'N/A'}</div>
                    <div class="room-stat-label">Created</div>
                </div>
            </div>
            <div class="room-actions">
                <button class="btn btn-sm btn-secondary" onclick="editRoom('${room.id}')">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteRoom('${room.id}', '${room.name}')">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </div>
        </div>
    `).join('');
}

function showAddRoomModal() {
    document.getElementById('addRoomModal').classList.remove('hidden');
    document.getElementById('addRoomForm').reset();
}

function hideAddRoomModal() {
    document.getElementById('addRoomModal').classList.add('hidden');
}

function showEditRoomModal() {
    document.getElementById('editRoomModal').classList.remove('hidden');
}

function hideEditRoomModal() {
    document.getElementById('editRoomModal').classList.add('hidden');
}

async function handleAddRoom(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const roomData = {
        name: formData.get('name'),
        description: formData.get('description') || null
    };

    try {
        const response = await fetch(`${API_BASE_URL}/api/settings/rooms`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(roomData)
        });

        if (response.ok) {
            const room = await response.json();
            showMessage('Room created successfully', 'success');
            hideAddRoomModal();
            loadRoomsForSettings(); // Reload rooms list
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create room');
        }
    } catch (error) {
        console.error('Error creating room:', error);
        showMessage('Error creating room: ' + error.message, 'error');
    }
}

async function editRoom(roomId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/settings/rooms/${roomId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            const room = await response.json();
            
            // Populate edit form
            document.getElementById('editRoomId').value = room.id;
            document.getElementById('editRoomName').value = room.name;
            document.getElementById('editRoomDescription').value = room.description || '';
            document.getElementById('editRoomActive').checked = room.active;
            
            showEditRoomModal();
        } else {
            throw new Error('Failed to load room data');
        }
    } catch (error) {
        console.error('Error loading room data:', error);
        showMessage('Error loading room data', 'error');
    }
}

async function handleEditRoom(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const roomId = formData.get('roomId');
    const roomData = {
        name: formData.get('name'),
        description: formData.get('description') || null,
        active: formData.get('active') === 'on'
    };

    try {
        const response = await fetch(`${API_BASE_URL}/api/settings/rooms/${roomId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(roomData)
        });

        if (response.ok) {
            showMessage('Room updated successfully', 'success');
            hideEditRoomModal();
            loadRoomsForSettings(); // Reload rooms list
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to update room');
        }
    } catch (error) {
        console.error('Error updating room:', error);
        showMessage('Error updating room: ' + error.message, 'error');
    }
}

async function deleteRoom(roomId, roomName) {
    if (!confirm(`Are you sure you want to delete the room "${roomName}"? This action cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/api/settings/rooms/${roomId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });

        if (response.ok) {
            showMessage('Room deleted successfully', 'success');
            loadRoomsForSettings(); // Reload rooms list
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to delete room');
        }
    } catch (error) {
        console.error('Error deleting room:', error);
        showMessage('Error deleting room: ' + error.message, 'error');
    }
}

// Settings Tab Management
function showSettingsTab(tabName) {
    // Hide all settings tab contents
    const tabContents = document.querySelectorAll('.settings-tab-content');
    tabContents.forEach(content => content.classList.remove('active'));
    
    // Remove active class from all settings tab buttons
    const tabButtons = document.querySelectorAll('.settings-tab-btn');
    tabButtons.forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab content
    const selectedTab = document.getElementById(tabName + 'SettingsTab');
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // Add active class to selected tab button
    const selectedButton = document.querySelector(`[onclick="showSettingsTab('${tabName}')"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
    
    // Load specific data for each tab
    if (tabName === 'rooms') {
        loadRoomsForSettings();
    } else if (tabName === 'hours') {
        loadWorkingHours();
    } else if (tabName === 'layout') {
        initializeLayoutEditor();
    }
}