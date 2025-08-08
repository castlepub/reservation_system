// API Configuration
const API_BASE_URL = window.location.origin;
let authToken = localStorage.getItem('authToken');
let dashboardStats = null;
let chartInstance = null;
let smartAvailabilityData = null;

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
        // Route to section if hash present
        updateSectionFromHash();
        window.addEventListener('hashchange', updateSectionFromHash);
        
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

function updateSectionFromHash() {
    const hash = window.location.hash || '#home';
    if (hash === '#home') {
        showSection('home');
    } else if (hash === '#reservations') {
        showSection('reservations');
    } else if (hash === '#admin') {
        showSection('admin');
    } else {
        showSection('home');
    }
}

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

    // Settings save buttons
    const saveGeneralSettingsBtn = document.getElementById('saveGeneralSettings');
    if (saveGeneralSettingsBtn) {
        saveGeneralSettingsBtn.addEventListener('click', saveAllSettings);
    }
    
    const saveWorkingHoursBtn = document.getElementById('saveWorkingHours');
    if (saveWorkingHoursBtn) {
        saveWorkingHoursBtn.addEventListener('click', saveWorkingHours);
    }
    
    const addSpecialDayBtn = document.getElementById('addSpecialDay');
    if (addSpecialDayBtn) {
        addSpecialDayBtn.addEventListener('click', addSpecialDay);
    }

    // Top navigation links (Home, Make Reservation, Admin)
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const href = link.getAttribute('href') || '#home';
            if (href) {
                history.pushState(null, '', href);
                updateSectionFromHash();
            }
        });
    });
    
    // Edit room form
    const editRoomForm = document.getElementById('editRoomForm');
    if (editRoomForm) {
        editRoomForm.addEventListener('submit', handleEditRoom);
    }
    
    // Add room form
    const addRoomForm = document.getElementById('addRoomForm');
    if (addRoomForm) {
        addRoomForm.addEventListener('submit', handleAddRoom);
    }
    
    // Fallback checkbox interactions
    const roomIsFallback = document.getElementById('roomIsFallback');
    if (roomIsFallback) {
        roomIsFallback.addEventListener('change', function() {
            toggleFallbackGroup('roomIsFallback', 'fallbackForGroup');
        });
    }
    
    const editRoomIsFallback = document.getElementById('editRoomIsFallback');
    if (editRoomIsFallback) {
        editRoomIsFallback.addEventListener('change', function() {
            toggleFallbackGroup('editRoomIsFallback', 'editFallbackForGroup');
        });
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
            loadTodayReservations(),
            loadUpcomingReservations()
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
    const margin = 50;
    const chartWidth = canvas.width - margin * 2;
    const chartHeight = canvas.height - margin * 2;
    const barGroupWidth = chartWidth / data.length;
    const barWidth = Math.min(40, Math.floor(barGroupWidth / 3));
    
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
        const groupX = margin + (index * barGroupWidth) + (barGroupWidth / 2);
        const reservationHeight = (day.reservations / maxValue) * chartHeight;
        const guestHeight = (day.guests / maxValue) * chartHeight;
        
        // Reservations bar
        ctx.fillStyle = '#667eea';
        ctx.fillRect(groupX - barWidth - 4, margin + chartHeight - reservationHeight, barWidth, reservationHeight);
        
        // Guests bar
        ctx.fillStyle = '#764ba2';
        ctx.fillRect(groupX + 4, margin + chartHeight - guestHeight, barWidth, guestHeight);
        
        // Day label
        ctx.fillStyle = '#4a5568';
        ctx.font = '14px Inter';
        ctx.textAlign = 'center';
        const dayName = day.day_name.substring(0, 3);
        ctx.fillText(dayName, groupX, margin + chartHeight + 24);
    });
    
    // Legend
    ctx.fillStyle = '#667eea';
    ctx.fillRect(margin, 10, 15, 15);
    ctx.fillStyle = '#4a5568';
    ctx.font = '12px Inter';
    ctx.textAlign = 'left';
    ctx.fillText('Reservations', margin + 20, 22);
    
    ctx.fillStyle = '#764ba2';
    ctx.fillRect(margin + 140, 10, 15, 15);
    ctx.fillText('Guests', margin + 160, 22);

    // Hover tooltip
    const tooltip = document.createElement('div');
    tooltip.style.position = 'absolute';
    tooltip.style.pointerEvents = 'none';
    tooltip.style.background = 'rgba(0,0,0,0.8)';
    tooltip.style.color = '#fff';
    tooltip.style.padding = '6px 8px';
    tooltip.style.borderRadius = '4px';
    tooltip.style.fontSize = '12px';
    tooltip.style.transform = 'translate(-50%, -120%)';
    tooltip.style.display = 'none';
    canvas.parentElement.style.position = 'relative';
    canvas.parentElement.appendChild(tooltip);

    const barRects = [];
    data.forEach((day, index) => {
        const groupX = margin + (index * barGroupWidth) + (barGroupWidth / 2);
        const resHeight = (day.reservations / maxValue) * chartHeight;
        const gueHeight = (day.guests / maxValue) * chartHeight;
        barRects.push(
            { x: groupX - barWidth - 4, y: margin + chartHeight - resHeight, w: barWidth, h: resHeight, type: 'Reservations', value: day.reservations, day: day.day_name },
            { x: groupX + 4, y: margin + chartHeight - gueHeight, w: barWidth, h: gueHeight, type: 'Guests', value: day.guests, day: day.day_name }
        );
    });

    canvas.onmousemove = (e) => {
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        const hit = barRects.find(r => mx >= r.x && mx <= r.x + r.w && my >= r.y && my <= r.y + r.h);
        if (hit) {
            tooltip.textContent = `${hit.day} • ${hit.type}: ${hit.value}`;
            tooltip.style.left = `${e.clientX - rect.left}px`;
            tooltip.style.top = `${e.clientY - rect.top}px`;
            tooltip.style.display = 'block';
        } else {
            tooltip.style.display = 'none';
        }
    };
}

async function loadUpcomingReservations() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/dashboard/upcoming?days_ahead=7`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) return;
        const items = await response.json();
        renderUpcomingReservations(items);
    } catch (e) {
        console.warn('Upcoming reservations failed to load:', e);
    }
}

function renderUpcomingReservations(items) {
    const container = document.getElementById('upcomingReservations');
    if (!container) return;
    if (!items || items.length === 0) {
        container.innerHTML = '<p class="text-center text-gray-500">No upcoming reservations</p>';
        return;
    }
    // Group by date
    const byDate = items.reduce((acc, r) => {
        const key = r.date;
        if (!acc[key]) acc[key] = [];
        acc[key].push(r);
        return acc;
    }, {});

    const html = Object.keys(byDate).sort().map(d => {
        const dayItems = byDate[d];
        const totalGuests = dayItems.reduce((sum, r) => sum + (r.party_size || 0), 0);
        return `
        <div class="note-item">
            <div class="note-header">
                <span class="note-title">${formatDate(d)} • ${dayItems.length} reservations • ${totalGuests} guests</span>
            </div>
            <div class="note-content">
                ${dayItems.map(r => `
                    <div class="flex-between" style="display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px dashed #eee;cursor:pointer;" onclick="openReservationById('${r.id}')">
                        <span><strong>${r.time.substring(0,5)}</strong> • ${r.customer_name} (${r.party_size}) ${r.room_name ? '• ' + r.room_name : ''}</span>
                        <span>${(r.table_names||[]).join(', ')}</span>
                    </div>
                `).join('')}
            </div>
        </div>`;
    }).join('');

    container.innerHTML = html;
}

async function openReservationById(reservationId) {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/reservations/${reservationId}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        if (!response.ok) throw new Error('Failed to load reservation');
        const reservation = await response.json();
        showReservationDetails(reservation);
    } catch (e) {
        console.error('Open reservation error:', e);
        showMessage('Failed to open reservation', 'error');
    }
}

function updateGuestNotes() {
    if (!dashboardStats || !dashboardStats.guest_notes) return;

    const container = document.getElementById('guestNotes');
    if (!container) {
        // Guest notes panel not present in the current layout
        return;
    }
    
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

    container.innerHTML = reservations.map(reservation => {
        const tableNames = Array.isArray(reservation.table_names) && reservation.table_names.length > 0
            ? reservation.table_names
            : ['TBD'];
        const timeStr = typeof reservation.time === 'string' ? reservation.time : '';
        return `
        <div class="today-reservation-card">
            <div class="reservation-header">
                <div class="customer-info">
                    <h4>${reservation.customer_name}</h4>
                    <span class="reservation-type-badge type-${reservation.reservation_type}">
                        ${reservation.reservation_type}
                    </span>
                </div>
                <div class="reservation-time">${formatTime(timeStr)}</div>
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
                            ${tableNames.map(table => `<span class="table-tag">${table}</span>`).join('')}
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
        </div>`;
    }).join('');
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

function formatDateForApi(dateObj) {
    const year = dateObj.getFullYear();
    const month = String(dateObj.getMonth() + 1).padStart(2, '0');
    const day = String(dateObj.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// PDF Generation Functions
async function generateDailyPDF() {
    try {
        const today = formatDateForApi(new Date());
        // Use admin router path (mounted without /api prefix)
        const response = await fetch(`${API_BASE_URL}/admin/pdf/daily/${today}`, {
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
            a.download = `daily_report_${today}.pdf`;
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
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => content.style.display = 'none');
    
    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => btn.classList.remove('active'));
    
    // Show selected tab content
    const selectedTab = document.getElementById(tabName + 'Tab');
    if (selectedTab) {
        selectedTab.style.display = 'block';
    }
    
    // Add active class to selected tab button
    const selectedButton = document.querySelector(`[onclick="showTab('${tabName}')"]`);
    if (selectedButton) {
        selectedButton.classList.add('active');
    }
    
    // Load data for specific tabs
    if (tabName === 'dashboard') {
        loadDashboardData();
    } else if (tabName === 'customers') {
        loadCustomers();
    } else if (tabName === 'today') {
        loadTodayReservations();
    } else if (tabName === 'reservations') {
        loadAllReservations();
    } else if (tabName === 'tables') {
        loadTablesData();
    } else if (tabName === 'settings') {
        loadSettingsData();
    } else if (tabName === 'daily') {
        loadDailyView();
    }
}

function showSettingsTab(tabName) {
    // Hide all settings tab contents
    const settingsTabContents = document.querySelectorAll('.settings-tab-content');
    settingsTabContents.forEach(content => content.classList.remove('active'));
    
    // Remove active class from all settings tab buttons
    const settingsTabButtons = document.querySelectorAll('.settings-tab-btn');
    settingsTabButtons.forEach(btn => btn.classList.remove('active'));
    
    // Show selected settings tab content
    const selectedSettingsTab = document.getElementById(tabName + 'SettingsTab');
    if (selectedSettingsTab) {
        selectedSettingsTab.classList.add('active');
    }
    
    // Add active class to selected settings tab button
    const selectedSettingsButton = document.querySelector(`[onclick="showSettingsTab('${tabName}')"]`);
    if (selectedSettingsButton) {
        selectedSettingsButton.classList.add('active');
    }
    
    // Load specific data for settings tabs
    if (tabName === 'rooms') {
        loadRoomsForSettings();
    } else if (tabName === 'hours') {
        loadWorkingHours();
    } else if (tabName === 'layout') {
        initializeLayoutEditor();
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
    console.log('=== populateTimeSlots START ===', { selectId });
    
    const timeSelect = document.getElementById(selectId);
    console.log('Time select element:', timeSelect);
    
    if (!timeSelect) {
        console.error('Time select element not found for ID:', selectId);
        return;
    }
    
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
    
    console.log('Added time slots, total options:', timeSelect.options.length);
    console.log('=== populateTimeSlots END ===');
}

async function updateTimeSlotsForDate(dateInput, timeSelectId) {
    const selectedDate = new Date(dateInput.value);
    if (!selectedDate || isNaN(selectedDate)) return;
    
    // Format date as YYYY-MM-DD
    const dateString = selectedDate.toISOString().split('T')[0];
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/working-hours/${dateString}`);
        if (response.ok) {
            const data = await response.json();
            const timeSelect = document.getElementById(timeSelectId);
            
            // Clear existing options except the first
            while (timeSelect.options.length > 1) {
                timeSelect.removeChild(timeSelect.lastChild);
            }
            
            if (data.summary.is_open && data.available_time_slots && data.available_time_slots.length > 0) {
                data.available_time_slots.forEach(timeSlot => {
                    const option = document.createElement('option');
                    option.value = timeSlot;
                    option.textContent = timeSlot;
                    timeSelect.appendChild(option);
                });
            } else {
                // Restaurant is closed
                const option = document.createElement('option');
                option.value = '';
                option.textContent = data.summary.message || 'Restaurant is closed';
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
    const dateInput = document.getElementById('date');
    const timeInput = document.getElementById('time');
    const partySizeInput = document.getElementById('partySize');
    const roomInput = document.getElementById('room');
    
    if (!dateInput.value || !timeInput.value || !partySizeInput.value) {
        showMessage('Please fill in all required fields', 'error');
        return;
    }
    
    showLoading();
    
    try {
        // Smart availability temporarily disabled
        // await updateSmartAvailability();
        
        // Then check traditional availability
        const response = await fetch(`${API_BASE_URL}/api/availability`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                date: dateInput.value,
                time: timeInput.value,
                party_size: parseInt(partySizeInput.value),
                room_id: roomInput.value || null
            })
        });
        
        if (response.ok) {
            const availability = await response.json();
            
            if (availability.available) {
                showMessage(`✅ Available! ${availability.message}`, 'success');
                
                // Show additional smart recommendations if available
                if (smartAvailabilityData) {
                    showSmartRecommendations(smartAvailabilityData, availability);
                }
            } else {
                showMessage(`❌ Not available: ${availability.message}`, 'error');
                
                // Show alternative suggestions
                showAlternativeSuggestions(availability);
            }
        } else {
            showMessage('Error checking availability', 'error');
        }
    } catch (error) {
        console.error('Error checking availability:', error);
        showMessage('Error checking availability', 'error');
    } finally {
        hideLoading();
    }
}

function showSmartRecommendations(availabilityData, traditionalAvailability) {
    const recommendationsHtml = `
        <div class="smart-recommendations">
            <h4>🎯 Smart Recommendations</h4>
            <div class="recommendation-item">
                <span class="icon">📍</span>
                <span>Recommended area: ${availabilityData.recommended_area_type}</span>
            </div>
            <div class="recommendation-item">
                <span class="icon">🎉</span>
                <span>Reservation type: ${availabilityData.reservation_type}</span>
            </div>
            ${availabilityData.rooms.length > 0 ? `
                <div class="recommendation-item">
                    <span class="icon">🏠</span>
                    <span>${availabilityData.rooms.length} rooms available</span>
                </div>
            ` : ''}
        </div>
    `;
    
    // Add recommendations to the message or create a separate display area
    const recommendationsContainer = document.getElementById('smartRecommendations');
    if (recommendationsContainer) {
        recommendationsContainer.innerHTML = recommendationsHtml;
    }
}

function showAlternativeSuggestions(availability) {
    const suggestionsHtml = `
        <div class="alternative-suggestions">
            <h4>💡 Alternative Suggestions</h4>
            <div class="suggestion-item">
                <span class="icon">🕐</span>
                <span>Try different times</span>
            </div>
            <div class="suggestion-item">
                <span class="icon">🏠</span>
                <span>Check other rooms</span>
            </div>
            <div class="suggestion-item">
                <span class="icon">📅</span>
                <span>Try different dates</span>
            </div>
        </div>
    `;
    
    const suggestionsContainer = document.getElementById('alternativeSuggestions');
    if (suggestionsContainer) {
        suggestionsContainer.innerHTML = suggestionsHtml;
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
            loadWorkingHours(),
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
        let successCount = 0;
        
        for (const day of days) {
            const dayElement = document.querySelector(`.working-hours-day:has(#${day}-open)`);
            const isOpenCheckbox = dayElement?.querySelector('input[type="checkbox"]');
            const openTimeInput = document.getElementById(`${day}-open`);
            const closeTimeInput = document.getElementById(`${day}-close`);
            
            const workingHoursData = {
                is_open: isOpenCheckbox?.checked || false,
                open_time: openTimeInput?.value || '11:00',
                close_time: closeTimeInput?.value || '23:00'
            };

            // Update each day individually using the correct API endpoint
            const response = await fetch(`${API_BASE_URL}/api/settings/working-hours/${day}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${authToken}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(workingHoursData)
            });

            if (response.ok) {
                successCount++;
            } else {
                console.error(`Failed to save ${day} working hours`);
            }
        }

        if (successCount === days.length) {
            showMessage('Working hours saved successfully', 'success');
        } else {
            showMessage(`Saved ${successCount} out of ${days.length} days`, 'warning');
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

async function loadRoomsForSettings() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/rooms`, {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const rooms = await response.json();
            updateRoomsSettingsDisplay(rooms);
        } else {
            throw new Error('Failed to load rooms');
        }
    } catch (error) {
        console.error('Error loading rooms for settings:', error);
        showMessage('Error loading rooms', 'error');
    }
}

function updateRoomsSettingsDisplay(rooms) {
    const container = document.getElementById('roomsContainer');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (rooms.length === 0) {
        container.innerHTML = '<div class="loading-text">No rooms configured</div>';
        return;
    }
    
    // Sort rooms by display_order, then by priority
    rooms.sort((a, b) => {
        if (a.display_order !== b.display_order) {
            return a.display_order - b.display_order;
        }
        return a.priority - b.priority;
    });
    
    rooms.forEach(room => {
        const roomElement = document.createElement('div');
        roomElement.className = 'room-item';
        
        // Get area type badge
        const areaTypeBadge = getAreaTypeBadge(room.area_type);
        
        // Get priority badge
        const priorityBadge = getPriorityBadge(room.priority);
        
        // Get fallback info
        const fallbackInfo = room.is_fallback_area && room.fallback_for ? 
            `<div class="room-fallback"><i class="fas fa-shield-alt"></i> Fallback for ${room.fallback_for}</div>` : '';
        
        // Get status badge
        const statusBadge = room.active ? 
            '<span class="badge badge-success">Active</span>' : 
            '<span class="badge badge-warning">Inactive</span>';
        
        roomElement.innerHTML = `
            <div class="room-info">
                <div class="room-header">
                    <div class="room-name">${room.name}</div>
                    <div class="room-badges">
                        ${areaTypeBadge}
                        ${priorityBadge}
                        ${statusBadge}
                    </div>
                </div>
                <div class="room-description">${room.description || 'No description'}</div>
                <div class="room-details">
                    <span class="room-detail"><i class="fas fa-sort-numeric-up"></i> Priority: ${room.priority}</span>
                    <span class="room-detail"><i class="fas fa-list-ol"></i> Order: ${room.display_order}</span>
                    ${fallbackInfo}
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
        `;
        container.appendChild(roomElement);
    });
}

function getAreaTypeBadge(areaType) {
    const badges = {
        'indoor': '<span class="badge badge-primary"><i class="fas fa-home"></i> Indoor</span>',
        'outdoor': '<span class="badge badge-success"><i class="fas fa-umbrella-beach"></i> Outdoor</span>',
        'shared': '<span class="badge badge-info"><i class="fas fa-users"></i> Shared</span>'
    };
    return badges[areaType] || '<span class="badge badge-secondary">Unknown</span>';
}

function getPriorityBadge(priority) {
    if (priority <= 2) {
        return '<span class="badge badge-danger"><i class="fas fa-star"></i> High</span>';
    } else if (priority <= 5) {
        return '<span class="badge badge-warning"><i class="fas fa-star"></i> Medium</span>';
    } else {
        return '<span class="badge badge-secondary"><i class="fas fa-star"></i> Low</span>';
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
            
            // Populate the edit form
            document.getElementById('editRoomId').value = room.id;
            document.getElementById('editRoomName').value = room.name;
            document.getElementById('editRoomDescription').value = room.description || '';
            document.getElementById('editRoomActive').checked = room.active;
            
            // Populate area management fields
            document.getElementById('editRoomAreaType').value = room.area_type || 'indoor';
            document.getElementById('editRoomPriority').value = room.priority || 1;
            document.getElementById('editRoomDisplayOrder').value = room.display_order || 0;
            document.getElementById('editRoomIsFallback').checked = room.is_fallback_area || false;
            document.getElementById('editRoomFallbackFor').value = room.fallback_for || '';
            
            // Show/hide fallback group based on checkbox
            const fallbackGroup = document.getElementById('editFallbackForGroup');
            if (fallbackGroup) {
                fallbackGroup.style.display = room.is_fallback_area ? 'block' : 'none';
            }
            
            // Show the modal
            document.getElementById('editRoomModal').classList.remove('hidden');
        } else {
            throw new Error('Failed to load room details');
        }
    } catch (error) {
        console.error('Error loading room details:', error);
        showMessage('Error loading room details', 'error');
    }
}

function hideEditRoomModal() {
    document.getElementById('editRoomModal').classList.add('hidden');
}

// Add Room Modal Functions
function showAddRoomModal() {
    document.getElementById('addRoomModal').classList.remove('hidden');
}

function hideAddRoomModal() {
    document.getElementById('addRoomModal').classList.add('hidden');
}

async function handleAddRoom(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    
    const roomData = {
        name: formData.get('name'),
        description: formData.get('description'),
        active: formData.get('active') === 'on',
        area_type: formData.get('area_type'),
        priority: parseInt(formData.get('priority')) || 1,
        display_order: parseInt(formData.get('display_order')) || 0,
        is_fallback_area: formData.get('is_fallback_area') === 'on',
        fallback_for: formData.get('is_fallback_area') === 'on' ? formData.get('fallback_for') : null
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
            showMessage('Room created successfully', 'success');
            hideAddRoomModal();
            loadRoomsForSettings(); // Refresh the rooms list
        } else {
            throw new Error('Failed to create room');
        }
    } catch (error) {
        console.error('Error creating room:', error);
        showMessage('Error creating room', 'error');
    }
}

// Fallback checkbox interaction functions
function toggleFallbackGroup(checkboxId, groupId) {
    const checkbox = document.getElementById(checkboxId);
    const group = document.getElementById(groupId);
    
    if (checkbox && group) {
        group.style.display = checkbox.checked ? 'block' : 'none';
    }
}

async function handleEditRoom(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const roomId = formData.get('roomId');
    
    const roomData = {
        name: formData.get('name'),
        description: formData.get('description'),
        active: formData.get('active') === 'on',
        area_type: formData.get('area_type'),
        priority: parseInt(formData.get('priority')) || 1,
        display_order: parseInt(formData.get('display_order')) || 0,
        is_fallback_area: formData.get('is_fallback_area') === 'on',
        fallback_for: formData.get('is_fallback_area') === 'on' ? formData.get('fallback_for') : null
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
            loadRoomsForSettings(); // Refresh the rooms list
        } else {
            throw new Error('Failed to update room');
        }
    } catch (error) {
        console.error('Error updating room:', error);
        showMessage('Error updating room', 'error');
    }
}

async function deleteRoom(roomId, roomName) {
    if (!confirm(`Are you sure you want to delete the room "${roomName}"?`)) {
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
            loadRoomsForSettings(); // Refresh the rooms list
        } else {
            throw new Error('Failed to delete room');
        }
    } catch (error) {
        console.error('Error deleting room:', error);
        showMessage('Error deleting room', 'error');
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
    
    // Debug: Log form data
    console.log('Form data debug:');
    for (let [key, value] of formData.entries()) {
        console.log(`${key}: ${value}`);
    }
    
    const reservationData = {
        customer_name: formData.get('customerName'),
        email: formData.get('email'),
        phone: formData.get('phone'),
        party_size: parseInt(formData.get('partySize')),
        date: formData.get('date'),
        time: timeValue,
        duration_hours: parseInt(formData.get('duration')) || 2,
        room_id: formData.get('room') || null,
        reservation_type: formData.get('reservationType'),
        notes: formData.get('notes') || null,
        admin_notes: formData.get('adminNotes') || null
    };
    
    console.log('Reservation data:', reservationData);
    
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
            loadDashboardStats(); // Refresh dashboard stats
            loadTodayReservations(); // Refresh today's reservations
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

async function markArrived(reservationId) {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/reservations/${reservationId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: 'confirmed' })
        });
        if (response.ok) {
            showMessage('Marked as arrived', 'success');
            document.querySelectorAll('.modal').forEach(m => m.remove());
            loadTodayReservations();
            if (typeof loadDailyView === 'function') loadDailyView();
        } else {
            throw new Error('Failed to mark arrived');
        }
    } catch (e) {
        showMessage(e.message, 'error');
    }
}

async function markNoShow(reservationId) {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/reservations/${reservationId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: 'cancelled' })
        });
        if (response.ok) {
            showMessage('Marked as no-show', 'success');
            document.querySelectorAll('.modal').forEach(m => m.remove());
            loadTodayReservations();
            if (typeof loadDailyView === 'function') loadDailyView();
        } else {
            throw new Error('Failed to mark no-show');
        }
    } catch (e) {
        showMessage(e.message, 'error');
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

async function loadDailyView() {
    try {
        const dateStr = formatDateForApi(currentViewDate);
        const response = await fetch(`${API_BASE_URL}/api/layout/daily/${dateStr}`, {
            headers: { 'Authorization': `Bearer ${authToken}` }
        });
        
        if (response.ok) {
            dailyViewData = await response.json();
            updateDateDisplay();

            // Ensure a default room is selected and stays selected
            if (dailyViewData.rooms && dailyViewData.rooms.length > 0) {
                const roomIds = dailyViewData.rooms.map(r => r.id);
                if (!currentRoomId || !roomIds.includes(currentRoomId)) {
                    currentRoomId = dailyViewData.rooms[0].id;
                }
            } else {
                currentRoomId = null;
            }

            renderRoomTabs();
            renderReservationsList();
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
        dateDisplay.textContent = currentViewDate.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
}

function getReservationTableInfo(reservation) {
    // Check if reservation has table assignments
    if (reservation.tables && Array.isArray(reservation.tables) && reservation.tables.length > 0) {
        const tableNames = reservation.tables.map(t => t.table_name || t.name || 'Unknown').join(', ');
        return `Tables: ${tableNames}`;
    }
    
    // Check legacy table_id field
    if (reservation.table_id) {
        return `Table: ${getTableNameById(reservation.table_id)}`;
    }
    
    // Check if table is assigned in layout but not showing correctly
    if (dailyViewData && dailyViewData.rooms) {
        for (const room of dailyViewData.rooms) {
            if (room.tables && Array.isArray(room.tables)) {
                for (const table of room.tables) {
                    if (table.reservations && Array.isArray(table.reservations) && 
                        table.reservations.some(r => r && r.id === reservation.id)) {
                        return `Table: ${table.table_name || 'Unknown'}`;
                    }
                }
            }
        }
    }
    
    return 'No table assigned';
}

function renderReservationsList() {
    const container = document.getElementById('dailyReservationsList');
    if (!container || !dailyViewData) return;
    
    let allReservations = [];
    if (dailyViewData.rooms && Array.isArray(dailyViewData.rooms)) {
        dailyViewData.rooms.forEach(room => {
            if (room.reservations && Array.isArray(room.reservations)) {
                allReservations = allReservations.concat(room.reservations);
            }
        });
    }
    
    if (allReservations.length === 0) {
        container.innerHTML = '<div class="no-reservations">No reservations for this date</div>';
        return;
    }
    
    const reservationsHtml = allReservations.map(reservation => {
        // Ensure reservation has required properties
        if (!reservation || !reservation.id) {
            console.warn('Invalid reservation data:', reservation);
            return '';
        }
        
        return `
            <div class="reservation-item" onclick="openReservationById('${reservation.id}')">
                <div class="reservation-time">${formatTime(reservation.time || '')}</div>
                <div class="reservation-details">
                    <div class="customer-name">${reservation.customer_name || 'Unknown'}</div>
                    <div class="party-size">${reservation.party_size || 0} guests</div>
                    <div class="reservation-status ${(reservation.status || 'confirmed').toLowerCase()}">${reservation.status || 'confirmed'}</div>
                </div>
                <div class="table-info">
                    ${getReservationTableInfo(reservation)}
                </div>
            </div>
        `;
    }).filter(html => html !== '').join('');
    
    container.innerHTML = reservationsHtml;
}

function renderRoomTabs() {
    const container = document.getElementById('roomTabs');
    if (!container || !dailyViewData) return;
    
    if (!dailyViewData.rooms || !Array.isArray(dailyViewData.rooms)) {
        container.innerHTML = '<div class="no-rooms">No rooms available</div>';
        return;
    }
    
    const roomTabsHtml = dailyViewData.rooms.map(room => `
        <button class="room-tab ${room.id === currentRoomId ? 'active' : ''}" 
                onclick="switchRoom('${room.id}')">
            ${room.name || 'Unknown Room'}
        </button>
    `).join('');
    
    container.innerHTML = roomTabsHtml;
}

function renderTableLayout() {
    const container = document.getElementById('tableLayout');
    if (!container || !dailyViewData || !currentRoomId) return;
    
    const currentRoom = dailyViewData.rooms.find(room => room.id === currentRoomId);
    if (!currentRoom) return;
    
    // Clear container
    container.innerHTML = '';
    
    // Set container dimensions
    if (currentRoom.layout) {
        container.style.width = `${currentRoom.layout.width || 800}px`;
        container.style.height = `${currentRoom.layout.height || 600}px`;
        container.style.backgroundColor = currentRoom.layout.background_color || '#f5f5f5';
    } else {
        container.style.width = '800px';
        container.style.height = '600px';
        container.style.backgroundColor = '#f5f5f5';
    }
    container.style.position = 'relative';
    
    // Add tables
    if (currentRoom.tables && Array.isArray(currentRoom.tables)) {
        currentRoom.tables.forEach(table => {
            if (!table) return;
            
            const tableElement = document.createElement('div');
            tableElement.className = `table-element ${table.shape || 'rectangular'}`;
            tableElement.style.left = `${table.x_position || 0}px`;
            tableElement.style.top = `${table.y_position || 0}px`;
            tableElement.style.width = `${table.width || 120}px`;
            tableElement.style.height = `${table.height || 80}px`;
            tableElement.style.backgroundColor = table.color || '#ffffff';
            tableElement.style.borderColor = table.border_color || '#333333';
            tableElement.style.color = table.text_color || '#000000';
            tableElement.style.fontSize = `${table.font_size || 12}px`;
            tableElement.style.zIndex = table.z_index || 0;
            tableElement.style.position = 'absolute';
            tableElement.style.border = '2px solid';
            tableElement.style.borderRadius = table.shape === 'circle' ? '50%' : '0';
            tableElement.style.display = 'flex';
            tableElement.style.flexDirection = 'column';
            tableElement.style.justifyContent = 'center';
            tableElement.style.alignItems = 'center';
            tableElement.style.cursor = 'pointer';
            
            // Add table content
            let tableContent = '';
            if (table.show_name !== false) {
                tableContent += `<div class="table-name">${table.table_name || 'Table'}</div>`;
            }
            if (table.show_capacity !== false) {
                tableContent += `<div class="table-capacity">${table.capacity || 0}p</div>`;
            }
            
            // Add reservation info if table has reservations
            if (table.reservations && Array.isArray(table.reservations) && table.reservations.length > 0) {
                const reservation = table.reservations[0]; // Show first reservation
                if (reservation && reservation.customer_name) {
                    tableContent += `<div class="table-reservation">${reservation.customer_name}<br>${formatTime(reservation.time || '')}</div>`;
                }
            }
            
            tableElement.innerHTML = tableContent;
            
            // Add click handler
            tableElement.onclick = () => showTableDetails(table.table_id);
            
            container.appendChild(tableElement);
        });
    } else {
        container.innerHTML = '<div class="no-tables">No tables configured for this room</div>';
    }
}

function getTableNameById(tableId) {
    if (!dailyViewData) return 'Unknown';
    
    for (const room of dailyViewData.rooms) {
        const table = room.tables.find(t => t.table_id === tableId);
        if (table) {
            return table.table_name;
        }
    }
    return 'Unknown';
}

function switchRoom(roomId) {
    currentRoomId = roomId;
    renderRoomTabs();
    renderTableLayout();
}

function selectReservation(reservationId) {
    // Remove previous selection
    document.querySelectorAll('.reservation-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Add selection to clicked item
    const selectedItem = document.querySelector(`[onclick="selectReservation('${reservationId}')"]`);
    if (selectedItem) {
        selectedItem.classList.add('selected');
    }
    
    // Highlight associated tables
    highlightReservationTables(reservationId);
}

function highlightReservationTables(reservationId) {
    // Remove previous highlights
    document.querySelectorAll('.table-element').forEach(table => {
        table.style.boxShadow = '';
    });
    
    if (!dailyViewData) return;
    
    // Find reservation and highlight its table
    for (const room of dailyViewData.rooms) {
        const reservation = room.reservations.find(r => r.id === reservationId);
        if (reservation && reservation.table_id) {
            const tableElement = document.querySelector(`[onclick*="${reservation.table_id}"]`);
            if (tableElement) {
                tableElement.style.boxShadow = '0 0 10px rgba(255, 255, 0, 0.8)';
            }
        }
    }
}

function showTableDetails(tableId) {
    if (!dailyViewData) return;
    
    // Find table data
    let tableData = null;
    for (const room of dailyViewData.rooms) {
        tableData = room.tables.find(t => t.table_id === tableId);
        if (tableData) break;
    }
    
    if (!tableData) return;
    
    // Show table details in a modal or tooltip
    const details = `
        Table: ${tableData.table_name}
        Capacity: ${tableData.capacity} people
        Status: ${tableData.status}
        ${tableData.reservations && tableData.reservations.length > 0 ? 
            `Reservations: ${tableData.reservations.map(r => `${r.customer_name} (${formatTime(r.time)})`).join(', ')}` : 
            'No reservations'}
    `;
    
    showMessage(details, 'info');
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
    document.querySelectorAll('.filter-buttons .btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Filter reservations based on status
    const container = document.getElementById('dailyReservationsList');
    const reservationItems = container.querySelectorAll('.reservation-item');
    
    reservationItems.forEach(item => {
        const statusElement = item.querySelector('.reservation-status');
        const status = statusElement ? statusElement.textContent.toLowerCase() : '';
        
        if (filter === 'all' || status === filter) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
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

async function assignReservationToTable(reservationId, tableId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/reservations/${reservationId}/assign-table/${tableId}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            showMessage(`Reservation assigned to table ${result.table_name} successfully`, 'success');
            
            // Refresh daily view to show updated assignments
            if (currentViewDate) {
                loadDailyView();
            }
            
            return true;
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to assign reservation to table');
        }
    } catch (error) {
        console.error('Error assigning reservation to table:', error);
        showMessage('Error assigning reservation to table: ' + error.message, 'error');
        return false;
    }
}

async function showTableAssignmentModal(reservationId) {
    try {
        // Get available tables for the current room
        if (!currentRoomId) {
            showMessage('Please select a room first', 'error');
            return;
        }
        
        const response = await fetch(`${API_BASE_URL}/api/rooms/${currentRoomId}/tables`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch tables');
        }
        
        const tables = await response.json();
        
        // Create modal content
        let modalContent = `
            <div class="modal-header">
                <h3>Assign Reservation to Table</h3>
                <button type="button" class="close" onclick="hideTableAssignmentModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="table-selection">
                    <h4>Available Tables:</h4>
                    <div class="table-grid">
        `;
        
        tables.forEach(table => {
            const isAvailable = table.status === 'available';
            modalContent += `
                <div class="table-option ${isAvailable ? 'available' : 'reserved'}" 
                     onclick="${isAvailable ? `assignReservationToTable('${reservationId}', '${table.id}')` : ''}">
                    <div class="table-name">${table.name}</div>
                    <div class="table-capacity">${table.capacity} seats</div>
                    <div class="table-status">${table.status}</div>
                </div>
            `;
        });
        
        modalContent += `
                    </div>
                </div>
            </div>
        `;
        
        // Show modal
        const modal = document.getElementById('tableAssignmentModal');
        modal.querySelector('.modal-content').innerHTML = modalContent;
        modal.classList.remove('hidden');
        
    } catch (error) {
        console.error('Error showing table assignment modal:', error);
        showMessage('Error loading tables: ' + error.message, 'error');
    }
}

function hideTableAssignmentModal() {
    document.getElementById('tableAssignmentModal').classList.add('hidden');
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
            console.log('=== LAYOUT EDITOR ROOMS LOADED ===');
            console.log('Total rooms:', rooms.length);
            console.log('Raw rooms data:', JSON.stringify(rooms, null, 2));
            rooms.forEach(room => {
                console.log(`Room: ${room.name} (ID: ${room.id})`);
            });
            
            // Clear any existing options first
            const roomSelect = document.getElementById('layoutRoomSelect');
            if (!roomSelect) {
                console.error('ERROR: layoutRoomSelect element not found!');
                return;
            }
            
            console.log('Found roomSelect element:', roomSelect);
            roomSelect.innerHTML = '<option value="">Choose a room...</option>';
            
            console.log('Adding room options...');
            rooms.forEach(room => {
                console.log(`Adding option for room: ${room.name} (${room.id})`);
                const option = document.createElement('option');
                option.value = room.id;
                option.textContent = room.name;
                roomSelect.appendChild(option);
            });
            
            console.log('Final roomSelect options:');
            Array.from(roomSelect.options).forEach((option, index) => {
                console.log(`  Option ${index}: ${option.textContent} (value: ${option.value})`);
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
    console.log('=== ROOM SELECTION HANDLER ===');
    console.log('Selected room ID:', roomId);
    console.log('Event target:', event.target);
    console.log('Available options:');
    Array.from(event.target.options).forEach(option => {
        if (option.value) {
            console.log(`  Option: ${option.textContent} (ID: ${option.value})`);
        }
    });
    
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
    console.log('=== renderLayoutCanvas START ===');
    const canvas = document.getElementById('layoutCanvas');
    console.log('Original canvas:', canvas);
    canvas.innerHTML = '';
    
    if (!currentLayoutData) {
        console.log('No currentLayoutData, returning early');
        return;
    }
    
    console.log('Current layout data:', currentLayoutData);
    
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
    
    console.log('Canvas configured, about to clone');
    
    // Add click handler for canvas only once
    // Remove any existing listeners first
    const newCanvas = canvas.cloneNode(true);
    console.log('New canvas created:', newCanvas);
    canvas.parentNode.replaceChild(newCanvas, canvas);
    newCanvas.id = 'layoutCanvas';
    
    console.log('Canvas replaced, re-adding room features');
    
    // Re-add room features to the new canvas
    if (roomLayout.show_entrance) {
        const entrance = document.createElement('div');
        entrance.className = 'room-entrance';
        entrance.textContent = 'ENTRANCE';
        newCanvas.appendChild(entrance);
        console.log('Added entrance to new canvas');
    }
    
    if (roomLayout.show_bar) {
        const bar = document.createElement('div');
        bar.className = 'room-bar';
        bar.textContent = 'BAR';
        newCanvas.appendChild(bar);
        console.log('Added bar to new canvas');
    }
    
    console.log('About to render tables, count:', currentLayoutData.tables.length);
    
    // Re-render tables on the new canvas
    currentLayoutData.tables.forEach((table, index) => {
        console.log(`Rendering table ${index}:`, table);
        const tableElement = createTableElement(table);
        newCanvas.appendChild(tableElement);
        console.log(`Table ${index} added to canvas`);
    });
    
    console.log('All tables rendered, adding click handler');
    
    // Add the click handler
    newCanvas.addEventListener('click', handleCanvasClick);
    
    console.log('=== renderLayoutCanvas END ===');
}

function createTableElement(table) {
    console.log('=== createTableElement START ===', table);
    
    const tableElement = document.createElement('div');
    tableElement.className = 'layout-table';
    tableElement.setAttribute('data-layout-id', table.layout_id || table.table_id);
    tableElement.setAttribute('data-table-id', table.table_id);
    tableElement.setAttribute('data-table-name', table.table_name);
    tableElement.setAttribute('title', `${table.table_name} (${table.shape}) - ${table.capacity} seats`);
    
    // Set position
    tableElement.style.left = `${table.x_position}px`;
    tableElement.style.top = `${table.y_position}px`;
    tableElement.style.width = `${table.width}px`;
    tableElement.style.height = `${table.height}px`;
    
    // Set shape
    if (table.shape === 'round') {
        tableElement.style.borderRadius = '50%';
        tableElement.classList.add('round');
    } else if (table.shape === 'square') {
        tableElement.style.borderRadius = '0';
        tableElement.classList.add('square');
    } else if (table.shape === 'rectangular') {
        tableElement.style.borderRadius = '0';
        tableElement.classList.add('rectangular');
    } else if (table.shape === 'bar_stool') {
        tableElement.style.borderRadius = '50%';
        tableElement.classList.add('bar_stool');
    } else {
        tableElement.style.borderRadius = '0';
        tableElement.classList.add('rectangular'); // Default to rectangular
    }
    
    // Set colors
    tableElement.style.backgroundColor = table.color || '#4CAF50';
    tableElement.style.borderColor = table.border_color || '#2E7D32';
    tableElement.style.color = table.text_color || '#FFFFFF';
    
    // Set text content based on shape and settings
    let textContent = '';
    if (table.show_name) {
        textContent += table.table_name;
    }
    if (table.show_capacity && table.show_name) {
        textContent += '\n';
    }
    if (table.show_capacity) {
        textContent += `${table.capacity}`;
    }
    
    tableElement.textContent = textContent;
    tableElement.style.fontSize = `${table.font_size || 12}px`;
    tableElement.style.zIndex = table.z_index || 1;
    tableElement.style.cursor = 'pointer';
    
    console.log('Table element created:', tableElement);
    console.log('Table element attributes:', {
        layoutId: tableElement.getAttribute('data-layout-id'),
        tableId: tableElement.getAttribute('data-table-id'),
        tableName: tableElement.getAttribute('data-table-name'),
        position: { left: tableElement.style.left, top: tableElement.style.top },
        size: { width: tableElement.style.width, height: tableElement.style.height },
        shape: table.shape,
        color: tableElement.style.backgroundColor
    });
    
    // Make draggable
    makeTableDraggable(tableElement);
    
    console.log('=== createTableElement END ===');
    return tableElement;
}

// Zoom support for layout editor
function setLayoutZoom(value) {
    const canvas = document.getElementById('layoutCanvas');
    const zoom = parseFloat(value) || 1;
    canvas.style.transformOrigin = '0 0';
    canvas.style.transform = `scale(${zoom})`;
    const label = document.getElementById('layoutZoomValue');
    if (label) label.textContent = `${Math.round(zoom * 100)}%`;
}

function getTableStatus(tableData) {
    if (tableData.reservations && tableData.reservations.length > 0) {
        return 'reserved';
    }
    return 'available';
}

function selectTable(tableElement) {
    console.log('=== selectTable START ===', tableElement);
    
    // Clear previous selection
    document.querySelectorAll('.layout-table.selected').forEach(table => {
        table.classList.remove('selected');
        console.log('Removed selection from table:', table);
    });
    
    // Select new table
    tableElement.classList.add('selected');
    selectedTable = tableElement.getAttribute('data-layout-id');
    
    console.log('Selected table:', tableElement);
    console.log('Selected table attributes:', {
        layoutId: tableElement.getAttribute('data-layout-id'),
        tableId: tableElement.getAttribute('data-table-id'),
        tableName: tableElement.getAttribute('data-table-name')
    });
    
    // Show table properties
    showTableProperties(tableElement);
    
    // Note: Removed excessive "Selected Table" message to reduce popup spam
    
    console.log('=== selectTable END ===');
}

        function showTableProperties(tableElement) {
            console.log('=== showTableProperties START ===', tableElement);
            
            const layoutId = tableElement.getAttribute('data-layout-id');
            const tableData = currentLayoutData.tables.find(t => t.layout_id === layoutId);
            if (!tableData) {
                console.error('Table data not found for layoutId:', layoutId);
                console.log('Available tables:', currentLayoutData.tables);
                return;
            }
    
    console.log('Found table data:', tableData);
    
    // Populate properties form
    document.getElementById('layoutTableName').value = tableData.table_name;
    document.getElementById('tableCapacity').value = tableData.capacity;
    document.getElementById('tableShape').value = tableData.shape;
    // Size preset auto-detect
    const preset = (function(w, h) {
        if (w >= 140 || h >= 110) return 'large';
        if (w <= 70 || h <= 55) return 'small';
        return 'medium';
    })(parseFloat(tableData.width), parseFloat(tableData.height));
    const sizeSelect = document.getElementById('tableSizePreset');
    if (sizeSelect) sizeSelect.value = preset;
    
    // Handle color select - find the closest match or default to green
    const colorSelect = document.getElementById('tableColor');
    const colors = ['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336'];
    const closestColor = colors.find(color => color === tableData.color) || '#4CAF50';
    colorSelect.value = closestColor;
    
    console.log('Color handling:', { originalColor: tableData.color, closestColor, colors });
    
    document.getElementById('tableShowName').checked = tableData.show_name;
    document.getElementById('tableShowCapacity').checked = tableData.show_capacity;
    
    // Show properties panel
    document.getElementById('tableProperties').style.display = 'block';
    
    console.log('=== showTableProperties END ===');
}

function makeTableDraggable(tableElement) {
    console.log('=== makeTableDraggable START ===', tableElement);
    
    let isDragging = false;
    let startX, startY, startLeft, startTop;
    
    tableElement.addEventListener('mousedown', function(e) {
        console.log('Mouse down on table:', tableElement);
        console.log('Event:', e);
        
        if (e.target === tableElement) {
            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;
            startLeft = parseInt(tableElement.style.left) || 0;
            startTop = parseInt(tableElement.style.top) || 0;
            
            tableElement.style.zIndex = '1000';
            tableElement.classList.add('dragging');
            console.log('Started dragging, initial position:', { startLeft, startTop });
            
            // Add document-level event listeners for dragging
            document.addEventListener('mousemove', handleMouseMove);
            document.addEventListener('mouseup', handleMouseUp);
            
            e.preventDefault();
        }
    });
    
    function handleMouseMove(e) {
        if (isDragging) {
            const deltaX = e.clientX - startX;
            const deltaY = e.clientY - startY;
            
            let newLeft = startLeft + deltaX;
            let newTop = startTop + deltaY;
            
            // Boundary checking - prevent tables from going outside canvas
            const canvas = document.getElementById('layoutCanvas');
            const canvasRect = canvas.getBoundingClientRect();
            const tableWidth = parseInt(tableElement.style.width) || 100;
            const tableHeight = parseInt(tableElement.style.height) || 80;
            
            // Keep table within canvas bounds
            newLeft = Math.max(0, Math.min(newLeft, canvasRect.width - tableWidth));
            newTop = Math.max(0, Math.min(newTop, canvasRect.height - tableHeight));
            
            tableElement.style.left = `${newLeft}px`;
            tableElement.style.top = `${newTop}px`;
            
            console.log('Dragging, new position:', { newLeft, newTop });
        }
    }
    
    function handleMouseUp(e) {
        if (isDragging) {
            console.log('=== handleMouseUp START ===');
            console.log('Mouse up, stopping drag');
            isDragging = false;
            tableElement.style.zIndex = '1';
            tableElement.classList.remove('dragging');
            
            // Remove document-level event listeners
            document.removeEventListener('mousemove', handleMouseMove);
            document.removeEventListener('mouseup', handleMouseUp);
            
            // Update position in database
            const layoutId = tableElement.getAttribute('data-layout-id');
            const newLeft = parseInt(tableElement.style.left);
            const newTop = parseInt(tableElement.style.top);
            
            console.log('Table element attributes:', {
                'data-layout-id': tableElement.getAttribute('data-layout-id'),
                'data-table-id': tableElement.getAttribute('data-table-id'),
                style_left: tableElement.style.left,
                style_top: tableElement.style.top
            });
            
            console.log('Updating table position in DB:', { layoutId, newLeft, newTop });
            
            if (layoutId) {
                updateTablePosition(layoutId, newLeft, newTop);
            } else {
                console.error('No layout ID found for table element');
                showMessage('Error: No layout ID found for table', 'error');
            }
            
            // Prevent the canvas click handler from clearing selection
            e.stopPropagation();
            
            // Ensure the table stays selected and properties panel is visible
            setTimeout(() => {
                selectTable(tableElement);
            }, 10);
            
            console.log('=== handleMouseUp END ===');
        }
    }
    
    tableElement.addEventListener('click', function(e) {
        console.log('Table clicked:', tableElement);
        console.log('Click event:', e);
        
        if (!isDragging) {
            e.stopPropagation();
            selectTable(tableElement);
        } else {
            // If we were dragging, prevent the canvas click handler from clearing selection
            e.stopPropagation();
        }
    });
    
    console.log('=== makeTableDraggable END ===');
}

async function updateTablePosition(layoutId, x, y) {
    console.log('=== updateTablePosition START ===', { layoutId, x, y });
    
    // Check if this is a temporary ID (not saved yet)
    if (layoutId.startsWith('temp_')) {
        console.log('Table not saved yet, updating local data only');
        // Update local data only for temporary tables
        const tableData = currentLayoutData.tables.find(t => t.layout_id === layoutId);
        if (tableData) {
            tableData.x_position = x;
            tableData.y_position = y;
            console.log('Updated local data for temporary table:', tableData);
            showMessage('Table position updated (will be saved when layout is saved)', 'info');
        } else {
            console.warn('Table data not found in currentLayoutData for layoutId:', layoutId);
        }
        return;
    }
    
    try {
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
        
        console.log('PUT response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('PUT response error:', errorText);
            throw new Error(`Failed to update table position: ${response.status} ${errorText}`);
        }
        
        const responseData = await response.json();
        console.log('PUT response data:', responseData);
        
        // Update local data
        const tableData = currentLayoutData.tables.find(t => t.layout_id === layoutId);
        if (tableData) {
            tableData.x_position = x;
            tableData.y_position = y;
            console.log('Updated local data for table:', tableData);
        } else {
            console.warn('Table data not found in currentLayoutData for layoutId:', layoutId);
        }
        
        console.log('=== updateTablePosition SUCCESS ===');
        
        // Show success message
        showMessage('Table position updated successfully', 'success');
        
    } catch (error) {
        console.error('Error updating table position:', error);
        showMessage('Error updating table position: ' + error.message, 'error');
    }
}

function addTableToLayout(shape) {
    console.log('=== addTableToLayout START ===', shape);
    
    if (!currentLayoutRoom) {
        showMessage('Please select a room first', 'warning');
        return;
    }
    
    console.log('Current layout room:', currentLayoutRoom);
    
    const canvas = document.getElementById('layoutCanvas');
    const rect = canvas.getBoundingClientRect();
    
    console.log('Canvas rect:', rect);
    
    // Calculate position to avoid stacking - place tables in a grid pattern
    const tableWidth = shape === 'bar_stool' ? 40 : 100;
    const tableHeight = shape === 'bar_stool' ? 40 : 80;
    const spacing = 20;
    const tablesPerRow = Math.floor((rect.width - 50) / (tableWidth + spacing));
    
    const existingTables = currentLayoutData.tables.length;
    const row = Math.floor(existingTables / tablesPerRow);
    const col = existingTables % tablesPerRow;
    
    const x = 25 + col * (tableWidth + spacing);
    const y = 25 + row * (tableHeight + spacing);
    
    console.log('Calculated position:', { x, y, row, col, existingTables });
    
    // Create new table data
    const newTable = {
        layout_id: `temp_${Date.now()}`,
        table_id: `temp_${Date.now()}`,
        room_id: currentLayoutRoom,
        x_position: x,
        y_position: y,
        width: shape === 'bar_stool' ? 40 : 100,
        height: shape === 'bar_stool' ? 40 : 80,
        shape: shape,
        color: '#4CAF50',
        border_color: '#2E7D32',
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
    
    console.log('New table data created:', newTable);
    
    // Add to local data
    currentLayoutData.tables.push(newTable);
    console.log('Added to currentLayoutData.tables, new count:', currentLayoutData.tables.length);
    
    // Create and add table element
    const tableElement = createTableElement(newTable);
    console.log('Table element created:', tableElement);
    
    canvas.appendChild(tableElement);
    console.log('Table element appended to canvas');
    
    // Select the new table
    selectTable(tableElement);
    console.log('New table selected');
    
    // Save to backend
    saveNewTable(newTable);
    
    console.log('=== addTableToLayout END ===');
}

async function saveNewTable(tableData) {
    try {
        console.log('Saving new table:', tableData);
        
        const response = await fetch(`${API_BASE_URL}/api/layout/tables`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                table_name: tableData.table_name,
                capacity: tableData.capacity,
                combinable: true,
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
            console.log('Table saved successfully:', savedTable);
            
            // Update the temporary ID with the real one
            const existingTableData = currentLayoutData.tables.find(t => t.layout_id === tableData.layout_id);
            if (existingTableData) {
                existingTableData.layout_id = savedTable.id;
                existingTableData.table_id = savedTable.table_id;
                console.log('Updated table with real IDs:', existingTableData);
                showMessage('Table saved successfully', 'success');
            } else {
                console.warn('Could not find table data to update with real IDs');
            }
        } else {
            const errorText = await response.text();
            console.error('Failed to save table:', errorText);
            throw new Error(`Failed to save new table: ${errorText}`);
        }
    } catch (error) {
        console.error('Error saving new table:', error);
        showMessage('Error saving new table: ' + error.message, 'error');
    }
}

async function updateTableProperties() {
    if (!selectedTable) {
        console.error('No table selected for property update');
        return;
    }
    
    console.log('=== updateTableProperties START ===', { selectedTable });
    
    const formData = {
        table_name: document.getElementById('layoutTableName').value,
        capacity: parseInt(document.getElementById('tableCapacity').value),
        shape: document.getElementById('tableShape').value,
        color: document.getElementById('tableColor').value,
        show_name: document.getElementById('tableShowName').checked,
        show_capacity: document.getElementById('tableShowCapacity').checked
    };

    // Apply size preset to width/height if provided
    const sizePreset = document.getElementById('tableSizePreset')?.value;
    if (sizePreset === 'small') {
        formData.width = 70;
        formData.height = 55;
    } else if (sizePreset === 'medium') {
        formData.width = 100;
        formData.height = 80;
    } else if (sizePreset === 'large') {
        formData.width = 140;
        formData.height = 110;
    }
    
    console.log('Form data to send:', formData);
    
    // Check if this is a temporary ID (not saved yet)
    if (selectedTable.startsWith('temp_')) {
        console.log('Table not saved yet, updating local data only');
        // Update local data only for temporary tables
        const tableData = currentLayoutData.tables.find(t => t.layout_id === selectedTable);
        if (tableData) {
            Object.assign(tableData, formData);
            console.log('Updated local table data:', tableData);
            // Re-render canvas
            renderLayoutCanvas();
            showMessage('Table properties updated (will be saved when layout is saved)', 'info');
        } else {
            console.warn('Table data not found in currentLayoutData for layoutId:', selectedTable);
        }
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/layout/tables/${selectedTable}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        console.log('PUT response status:', response.status);
        
        if (response.ok) {
            const responseData = await response.json();
            console.log('PUT response data:', responseData);
            
            // Update local data
            const tableData = currentLayoutData.tables.find(t => t.layout_id === selectedTable);
            if (tableData) {
                Object.assign(tableData, formData);
                console.log('Updated local table data:', tableData);
            } else {
                console.warn('Table data not found in currentLayoutData for layoutId:', selectedTable);
            }
            
            // Re-render canvas
            renderLayoutCanvas();
            showMessage('Table properties updated successfully', 'success');
        } else {
            const errorText = await response.text();
            console.error('PUT response error:', errorText);
            throw new Error(`Failed to update table properties: ${response.status} ${errorText}`);
        }
    } catch (error) {
        console.error('Error updating table properties:', error);
        showMessage('Error updating table properties: ' + error.message, 'error');
    }
    
    console.log('=== updateTableProperties END ===');
}

async function deleteSelectedTable() {
    if (!selectedTable) return;
    
    if (!confirm('Are you sure you want to delete this table?')) {
        return;
    }
    
    // Check if this is a temporary ID (not saved yet)
    if (selectedTable.startsWith('temp_')) {
        console.log('Deleting temporary table from local data only');
        // Remove from local data only for temporary tables
        currentLayoutData.tables = currentLayoutData.tables.filter(t => t.layout_id !== selectedTable);
        
        // Re-render canvas
        renderLayoutCanvas();
        
        // Hide properties panel
        document.getElementById('tableProperties').style.display = 'none';
        selectedTable = null;
        
        showMessage('Table deleted (was not saved yet)', 'info');
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
                <div class="modal-actions">
                    <button class="btn btn-secondary" onclick="markArrived('${reservation.id}')">Arrived</button>
                    <button class="btn btn-secondary" onclick="markNoShow('${reservation.id}')">No-Show</button>
                    <button class="btn btn-secondary" onclick="cancelReservation('${reservation.id}')">Cancel</button>
                </div>
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
    console.log('=== saveLayout START ===');
    
    if (!currentLayoutRoom) {
        showMessage('No room selected', 'warning');
        return;
    }
    
    try {
        // Find all temporary tables that need to be saved
        const temporaryTables = currentLayoutData.tables.filter(t => t.layout_id.startsWith('temp_'));
        console.log('Found temporary tables to save:', temporaryTables);
        
        // Save each temporary table
        for (const tableData of temporaryTables) {
            await saveNewTable(tableData);
        }
        
        showMessage('Layout saved successfully', 'success');
        console.log('=== saveLayout SUCCESS ===');
    } catch (error) {
        console.error('Error saving layout:', error);
        showMessage('Error saving layout: ' + error.message, 'error');
    }
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

function handleCanvasClick(e) {
    console.log('=== handleCanvasClick START ===', e);
    console.log('Click target:', e.target);
    console.log('Click target classList:', e.target.classList);
    
    // Only handle clicks directly on the canvas, not on tables or other elements
    if (e.target.id === 'layoutCanvas') {
        console.log('Clicked on empty canvas, clearing selection');
        selectedTable = null;
        document.querySelectorAll('.layout-table.selected').forEach(table => {
            table.classList.remove('selected');
            console.log('Removed selection from table:', table);
        });
        document.getElementById('tableProperties').style.display = 'none';
        showMessage('Selection cleared', 'info');
    }
    // Don't handle table clicks here - they have their own handlers
    
    console.log('=== handleCanvasClick END ===');
}

// Initialize layout editor when settings tab is loaded
function initializeLayoutEditorOnLoad() {
    if (document.getElementById('layoutRoomSelect')) {
        initializeLayoutEditor();
    }
}

// Smart Availability Functions

async function loadSmartAvailability(date, partySize, preferredAreaType = null, reservationType = 'dinner') {
    // Temporarily disabled to prevent 500 errors
    console.log('Smart availability temporarily disabled');
    return null;
}

async function loadAreaRecommendations(partySize, reservationType = 'dinner') {
    // Temporarily disabled to prevent 500 errors
    console.log('Area recommendations temporarily disabled');
    return null;
}

function displayAreaRecommendations(recommendations) {
    const recommendationsContainer = document.getElementById('areaRecommendations');
    if (!recommendationsContainer || !recommendations) return;
    
    const recommendationsHtml = `
        <div class="area-recommendations-card">
            <div class="recommendations-header">
                <h3>📍 Area Recommendations</h3>
                <div class="party-info">
                    <span>Party of ${recommendations.party_size} people</span>
                    <span>•</span>
                    <span>${recommendations.reservation_type} reservation</span>
                </div>
            </div>
            <div class="recommendations-content">
                <div class="preferred-area">
                    <h4>🎯 Preferred Area Type</h4>
                    <div class="area-type ${recommendations.preferred_area_type}">
                        ${recommendations.preferred_area_type.toUpperCase()}
                    </div>
                </div>
                
                <div class="suitable-areas">
                    <h4>✅ Suitable Areas (${recommendations.suitable_areas.length})</h4>
                    ${recommendations.suitable_areas.length > 0 ? 
                        recommendations.suitable_areas.map(area => `
                            <div class="area-item">
                                <div class="area-name">${area.name}</div>
                                <div class="area-details">
                                    <span class="badge badge-${area.area_type}">${area.area_type}</span>
                                    <span class="capacity">${area.capacity} seats</span>
                                    <span class="priority">Priority: ${area.priority}</span>
                                </div>
                            </div>
                        `).join('') : 
                        '<p class="no-areas">No suitable areas found</p>'
                    }
                </div>
                
                <div class="alternative-areas">
                    <h4>🔄 Alternative Areas (${recommendations.alternative_areas.length})</h4>
                    ${recommendations.alternative_areas.length > 0 ? 
                        recommendations.alternative_areas.map(area => `
                            <div class="area-item alternative">
                                <div class="area-name">${area.name}</div>
                                <div class="area-details">
                                    <span class="badge badge-${area.area_type}">${area.area_type}</span>
                                    <span class="capacity">${area.capacity} seats</span>
                                    <span class="priority">Priority: ${area.priority}</span>
                                </div>
                            </div>
                        `).join('') : 
                        '<p class="no-areas">No alternative areas found</p>'
                    }
                </div>
                
                ${recommendations.fallback_areas.length > 0 ? `
                    <div class="fallback-areas">
                        <h4>🛡️ Fallback Areas (${recommendations.fallback_areas.length})</h4>
                        ${recommendations.fallback_areas.map(area => `
                            <div class="area-item fallback">
                                <div class="area-name">${area.name}</div>
                                <div class="area-details">
                                    <span class="badge badge-${area.area_type}">${area.area_type}</span>
                                    <span class="capacity">${area.capacity} seats</span>
                                    <span class="fallback-for">Fallback for: ${area.fallback_for || 'General'}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    
    recommendationsContainer.innerHTML = recommendationsHtml;
}

function displaySmartAvailability(availabilityData) {
    const availabilityContainer = document.getElementById('smartAvailability');
    if (!availabilityContainer || !availabilityData) return;
    
    const roomsHtml = availabilityData.rooms.map(room => `
        <div class="room-availability ${room.area_type}">
            <div class="room-header">
                <h4>${room.room_name}</h4>
                <div class="room-badges">
                    ${getAreaTypeBadge(room.area_type)}
                    ${getPriorityBadge(room.priority)}
                    ${room.is_fallback_area ? '<span class="badge badge-info">Fallback</span>' : ''}
                </div>
            </div>
            <div class="room-details">
                <div class="capacity">Capacity: ${room.total_capacity} people</div>
                <div class="time-slots">
                    <h5>Available Times:</h5>
                    <div class="time-grid">
                        ${room.available_time_slots.map(slot => `
                            <div class="time-slot">
                                <span class="time">${slot.time}</span>
                                <span class="capacity">${slot.total_capacity} seats</span>
                                <span class="tables">${slot.table_count} tables</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `).join('');
    
    const availabilityHtml = `
        <div class="smart-availability-card">
            <div class="availability-header">
                <h3>🎯 Smart Availability for ${formatDate(availabilityData.date)}</h3>
                <div class="reservation-info">
                    <span class="reservation-type">${availabilityData.reservation_type}</span>
                    <span>•</span>
                    <span>Recommended: ${availabilityData.recommended_area_type}</span>
                </div>
            </div>
            <div class="rooms-container">
                ${roomsHtml}
            </div>
        </div>
    `;
    
    availabilityContainer.innerHTML = availabilityHtml;
}



async function updateSmartAvailability() {
    // Temporarily disabled to prevent 500 errors
    console.log('Smart availability update temporarily disabled');
}