document.addEventListener('DOMContentLoaded', function() {
    // API Endpoints
    const API_BASE_URL = 'http://localhost:8000/api';
    const API_LOGIN_URL = `${API_BASE_URL}/token/`;
    const API_OTP_REQUEST = `${API_BASE_URL}/otp/`;
    const API_OTP_VERIFY = `${API_BASE_URL}/verify-otp/`;
    const API_USERS_ME = `${API_BASE_URL}/users/me/`;
    const API_TEAM_CONNECT = `${API_BASE_URL}/users/team-connect/`;
    const API_INDUSTRY_DATA = `${API_BASE_URL}/users/industry-data/`;
    const API_DASHBOARD_COUNTS = `${API_BASE_URL}/users/dashboard-counts/`;
    
    // Resource API Endpoints
    const API_BOOKINGS = `${API_BASE_URL}/bookings/`;
    const API_VENDORS = `${API_BASE_URL}/vendors/`;
    const API_ORDERS = `${API_BASE_URL}/orders/`;
    const API_STOCK = `${API_BASE_URL}/stock/`;
    
    // DOM Elements
    const loginSection = document.getElementById('login-section');
    const dashboardSection = document.getElementById('dashboard-section');
    const tasksSection = document.getElementById('tasks-section');
    const usersSection = document.getElementById('users-section');
    const equipmentSection = document.getElementById('equipment-section');
    const bookingsSection = document.getElementById('bookings-section');
    const vendorsSection = document.getElementById('vendors-section');
    const ordersSection = document.getElementById('orders-section');
    const stockSection = document.getElementById('stock-section');
    
    const emailForm = document.getElementById('email-form');
    const otpForm = document.getElementById('otp-form');
    const sendOtpBtn = document.getElementById('send-otp-btn');
    const verifyOtpBtn = document.getElementById('verify-otp-btn');
    const backBtn = document.getElementById('back-btn');
    const logoutBtn = document.getElementById('logout-btn');
    
    const usernameInput = document.getElementById('username-input');
    const passwordInput = document.getElementById('password-input');
    const otpInput = document.getElementById('otp');
    const usernameDisplay = document.getElementById('username');
    const userGreeting = document.getElementById('user-greeting');
    
    // User credentials
    let currentUsername = '';
    let userEmail = '';
    let tempToken = '';
    let currentUserData = null;
    let teamConnectData = null;
    
    // Navigation links
    const navLinks = document.querySelectorAll('nav ul li a');
    
    // Check if user is already logged in
    const token = localStorage.getItem('access_token');
    if (token) {
        // Fetch user data and show app
        fetchUserProfile(token);
    } else {
        showLogin();
    }
    
    // Event Listeners
    sendOtpBtn.addEventListener('click', function() {
        const username = usernameInput.value.trim();
        const password = passwordInput.value.trim();
        
        console.log('Attempting login with username:', username);
        
        if (!username || !password) {
            alert('Please enter both username and password');
            return;
        }
        
        // Show loading state
        sendOtpBtn.disabled = true;
        sendOtpBtn.textContent = 'Authenticating...';
        
        console.log('Sending authentication request to:', API_LOGIN_URL);
        
        // First authenticate with username and password
        fetch(API_LOGIN_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                username: username,
                password: password
            })
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    console.error('Authentication error details:', errorData);
                    if (response.status === 401) {
                        throw new Error('Invalid username or password');
                    }
                    throw new Error(`Authentication failed: ${errorData.detail || errorData.error || 'Unknown error'}`);
                }).catch(e => {
                    if (e.message === 'Invalid username or password') {
                        throw e;
                    }
                    if (response.status === 401) {
                        throw new Error('Invalid username or password');
                    }
                    throw new Error(`Authentication failed. Status: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            // Store username and token
            currentUsername = username;
            tempToken = data.access;
            console.log('Authentication successful, token received');
            
            // Fetch user profile to get email
            return fetch(API_USERS_ME, {
                headers: {
                    'Authorization': `Bearer ${tempToken}`
                }
            });
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to get user details. Status: ${response.status}`);
            }
            return response.json();
        })
        .then(userData => {
            // Store user email
            userEmail = userData.email;
            console.log('User profile retrieved, email:', userEmail);
            
            if (!userEmail) {
                throw new Error('No email address found for this user. Please contact administrator.');
            }
            
            // Now request OTP
            sendOtpBtn.textContent = 'Sending OTP...';
            
            return fetch(API_OTP_REQUEST, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email: userEmail })
            });
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`OTP request failed. Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Show OTP input form
            emailForm.style.display = 'none';
            otpForm.style.display = 'block';
            console.log('OTP requested successfully and sent to registered email: ' + userEmail);
        })
        .catch(error => {
            console.error('Error in authentication process:', error);
            if (error.message.includes('Invalid username or password')) {
                alert('Invalid username or password. Please try again.');
            } else if (error.message.includes('No email address found')) {
                alert('No email address registered for this account. Please contact your administrator.');
            } else if (error.message.includes('OTP request failed')) {
                alert('Failed to send OTP. Please try again later.');
            } else {
                alert('Authentication failed: ' + error.message);
            }
        })
        .finally(() => {
            // Reset button state
            sendOtpBtn.disabled = false;
            sendOtpBtn.textContent = 'Send OTP';
        });
    });
    
    backBtn.addEventListener('click', function() {
        emailForm.style.display = 'block';
        otpForm.style.display = 'none';
        
        // Clear credentials
        currentUsername = '';
        userEmail = '';
        tempToken = '';
    });
    
    verifyOtpBtn.addEventListener('click', function() {
        const otp = otpInput.value.trim();
        
        if (!otp) {
            alert('Please enter the OTP');
            return;
        }
        
        if (!userEmail) {
            alert('Session expired. Please try logging in again.');
            showLogin();
            return;
        }
        
        // Show loading state
        verifyOtpBtn.disabled = true;
        verifyOtpBtn.textContent = 'Verifying...';
        
        console.log('Verifying OTP:', otp, 'for email:', userEmail);
        
        // Verify OTP with API
        fetch(API_OTP_VERIFY, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                email: userEmail,
                otp: otp
            })
        })
        .then(response => {
            console.log('OTP verification response status:', response.status);
            
            if (!response.ok) {
                return response.json().then(errorData => {
                    console.error('OTP verification error details:', errorData);
                    throw new Error(errorData.detail || 'OTP verification failed');
                }).catch(e => {
                    if (e.message) {
                        throw e;
                    }
                    throw new Error(`OTP verification failed. Status: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('OTP verification successful, tokens received');
            
            // Store tokens
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh);
            
            // Show app with current username
            showApp(currentUsername);
        })
        .catch(error => {
            console.error('Error verifying OTP:', error);
            if (error.message.includes('Invalid OTP')) {
                alert('Invalid OTP. Please check and try again.');
            } else if (error.message.includes('OTP has expired')) {
                alert('Your OTP has expired. Please request a new one.');
            } else if (error.message.includes('No OTP found')) {
                alert('No valid OTP found. Please request a new one.');
            } else {
                alert('OTP verification failed: ' + error.message);
            }
        })
        .finally(() => {
            // Reset button state
            verifyOtpBtn.disabled = false;
            verifyOtpBtn.textContent = 'Verify OTP';
        });
    });
    
    logoutBtn.addEventListener('click', function() {
        // Clear tokens and credentials
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        currentUsername = '';
        userEmail = '';
        tempToken = '';
        
        showLogin();
    });
    
    // Navigation handling
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Hide all sections
            hideAllSections();
            
            // Show the appropriate section based on the href
            const href = this.getAttribute('href');
            if (href === '#' || href === '#dashboard') {
                dashboardSection.classList.remove('hidden');
            } else if (href === '#tasks') {
                tasksSection.classList.remove('hidden');
            } else if (href === '#users') {
                usersSection.classList.remove('hidden');
            } else if (href === '#equipment') {
                equipmentSection.classList.remove('hidden');
            } else if (href === '#bookings') {
                bookingsSection.classList.remove('hidden');
                loadBookings();
            } else if (href === '#vendors') {
                vendorsSection.classList.remove('hidden');
                loadVendors();
            } else if (href === '#orders') {
                ordersSection.classList.remove('hidden');
                loadOrders();
            } else if (href === '#stock') {
                stockSection.classList.remove('hidden');
                loadStockItems();
            } else if (href === '#farms') {
                // Redirect to the farms page
                window.location.href = 'farms/index.html';
            }
        });
    });
    
    // Initialize search functionality
    initializeSearch('task-search', 'tasks-section');
    initializeSearch('user-search', 'users-section');
    initializeSearch('equipment-search', 'equipment-section');
    initializeSearch('booking-search', 'bookings-section');
    initializeSearch('vendor-search', 'vendors-section');
    initializeSearch('order-search', 'orders-section');
    initializeSearch('stock-search', 'stock-section');
    
    // Add event listeners for add/create buttons
    document.getElementById('create-task-btn').addEventListener('click', function() {
        hideAllSections();
        tasksSection.classList.remove('hidden');
        navLinks.forEach(l => l.classList.remove('active'));
        document.querySelector('a[href="#tasks"]').classList.add('active');
    });
    
    document.getElementById('create-booking-btn').addEventListener('click', function() {
        hideAllSections();
        bookingsSection.classList.remove('hidden');
        navLinks.forEach(l => l.classList.remove('active'));
        document.querySelector('a[href="#bookings"]').classList.add('active');
    });
    
    // Booking form modal handlers
    const bookingModal = document.getElementById('booking-modal');
    const bookingForm = document.getElementById('booking-form');
    const addBookingBtn = document.getElementById('add-booking-btn');
    const closeBookingModal = document.getElementById('close-booking-modal');
    const cancelBookingBtn = document.getElementById('cancel-booking-btn');
    const bookingError = document.getElementById('booking-error');
    
    if (addBookingBtn) {
        addBookingBtn.addEventListener('click', function() {
            bookingModal.classList.remove('hidden');
            loadRolesForBooking();
        });
    }
    
    if (closeBookingModal) {
        closeBookingModal.addEventListener('click', function() {
            bookingModal.classList.add('hidden');
            bookingForm.reset();
            bookingError.classList.add('hidden');
        });
    }
    
    if (cancelBookingBtn) {
        cancelBookingBtn.addEventListener('click', function() {
            bookingModal.classList.add('hidden');
            bookingForm.reset();
            bookingError.classList.add('hidden');
        });
    }
    
    // Vendor form modal handlers
    const vendorModal = document.getElementById('vendor-modal');
    const vendorForm = document.getElementById('vendor-form');
    const addVendorBtn = document.getElementById('add-vendor-btn');
    const closeVendorModal = document.getElementById('close-vendor-modal');
    const cancelVendorBtn = document.getElementById('cancel-vendor-btn');
    const vendorError = document.getElementById('vendor-error');
    
    if (addVendorBtn) {
        addVendorBtn.addEventListener('click', function() {
            vendorModal.classList.remove('hidden');
            loadIndianStates();
            // Reset form to add mode
            vendorForm.dataset.vendorId = '';
            document.querySelector('#vendor-modal h2').textContent = 'Add Vendor';
            document.querySelector('#vendor-modal .btn.primary-btn').textContent = 'Add Vendor';
        });
    }
    
    if (closeVendorModal) {
        closeVendorModal.addEventListener('click', function() {
            vendorModal.classList.add('hidden');
            vendorForm.reset();
            vendorError.classList.add('hidden');
        });
    }
    
    if (cancelVendorBtn) {
        cancelVendorBtn.addEventListener('click', function() {
            vendorModal.classList.add('hidden');
            vendorForm.reset();
            vendorError.classList.add('hidden');
        });
    }
    
    // Load Indian States for dropdown
    function loadIndianStates() {
        const stateSelect = document.getElementById('vendor-state');
        if (!stateSelect) return;
        
        const states = [
            'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
            'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
            'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
            'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
            'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
            'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
            'Andaman and Nicobar Islands', 'Chandigarh',
            'Dadra and Nagar Haveli and Daman and Diu', 'Delhi',
            'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
        ];
        
        stateSelect.innerHTML = '<option value="">Select State</option>';
        states.forEach(state => {
            const option = document.createElement('option');
            option.value = state;
            option.textContent = state;
            stateSelect.appendChild(option);
        });
    }
    
    // Handle vendor form submission
    if (vendorForm) {
        vendorForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            vendorError.classList.add('hidden');
            
            const formData = new FormData(vendorForm);
            const vendorId = vendorForm.dataset.vendorId;
            
            // Get GSTIN value and handle empty strings
            const gstinValue = formData.get('gstin_number');
            // Process GSTIN: trim whitespace, convert empty to null
            let processedGstin = null;
            if (gstinValue && typeof gstinValue === 'string' && gstinValue.trim()) {
                processedGstin = gstinValue.trim();
            }
            
            // Build vendor data object - always include gstin_number (even if null)
            const vendorData = {
                vendor_name: formData.get('vendor_name'),
                contact_person: formData.get('contact_person') || '',
                email: formData.get('email'),
                phone: formData.get('phone'),
                gstin_number: processedGstin,  // Always include, can be null or string
                state: formData.get('state') || null,
                city: formData.get('city') || '',
                address: formData.get('address'),
                website: formData.get('website') || '',
                rating: formData.get('rating') ? parseInt(formData.get('rating')) : null,
                notes: formData.get('notes') || ''
            };
            
            // Debug logging
            console.log('=== VENDOR FORM SUBMISSION DEBUG ===');
            console.log('Raw GSTIN from form:', gstinValue);
            console.log('Processed GSTIN:', processedGstin);
            console.log('GSTIN type:', typeof processedGstin);
            console.log('Full vendor data being sent:', JSON.stringify(vendorData, null, 2));
            console.log('===================================');
            
            try {
                let response;
                if (vendorId) {
                    // Update existing vendor
                    console.log('Updating vendor:', vendorId);
                    response = await apiCall(`${API_VENDORS}${vendorId}/`, {
                        method: 'PATCH',
                        body: JSON.stringify(vendorData)
                    });
                } else {
                    // Create new vendor
                    console.log('Creating new vendor');
                    response = await apiCall(API_VENDORS, {
                        method: 'POST',
                        body: JSON.stringify(vendorData)
                    });
                }
                
                console.log('Vendor response:', response);
                
                // Verify GSTIN was saved
                if (response.gstin_number !== undefined) {
                    console.log('GSTIN in response:', response.gstin_number);
                } else {
                    console.warn('GSTIN not found in response!');
                }
                
                // Success - close modal and reload vendors
                vendorModal.classList.add('hidden');
                vendorForm.reset();
                vendorForm.dataset.vendorId = '';
                loadVendors();
                alert(vendorId ? 'Vendor updated successfully!' : 'Vendor created successfully!');
            } catch (error) {
                // Show error message with more details
                let errorMessage = 'Error: ';
                if (error.message) {
                    errorMessage += error.message;
                } else {
                    errorMessage += 'Unknown error';
                }
                
                // Try to parse error details if available
                if (error.response) {
                    try {
                        const errorData = await error.response.json();
                        console.error('Error details:', errorData);
                        if (errorData.gstin_number) {
                            errorMessage += '\nGSTIN Error: ' + errorData.gstin_number.join(', ');
                        }
                    } catch (e) {
                        console.error('Could not parse error response');
                    }
                }
                
                vendorError.textContent = errorMessage;
                vendorError.classList.remove('hidden');
                console.error('Vendor creation/update error:', error);
                console.error('Vendor data that was sent:', vendorData);
            }
        });
    }
    
    // Load roles for booking form (optional - if endpoint exists)
    async function loadRolesForBooking() {
        const roleSelect = document.getElementById('booking-user-role');
        if (!roleSelect) return;
        
        try {
            // Try to fetch roles from team-connect data if available
            if (currentUserData && currentUserData.roles) {
                roleSelect.innerHTML = '<option value="">Select Role</option>';
                currentUserData.roles.forEach(role => {
                    const option = document.createElement('option');
                    option.value = role.id;
                    option.textContent = role.display_name || role.name;
                    roleSelect.appendChild(option);
                });
            } else {
                // Try API endpoint (may not exist)
                try {
                    const roles = await apiCall(`${API_BASE_URL}/users/roles/`);
                    if (roles) {
                        roleSelect.innerHTML = '<option value="">Select Role</option>';
                        const rolesArray = Array.isArray(roles) ? roles : (roles.results || []);
                        rolesArray.forEach(role => {
                            const option = document.createElement('option');
                            option.value = role.id;
                            option.textContent = role.display_name || role.name;
                            roleSelect.appendChild(option);
                        });
                    }
                } catch (apiError) {
                    // Roles endpoint doesn't exist - that's okay, user_role is optional
                    console.log('Roles endpoint not available - user_role field will be optional');
                }
            }
        } catch (error) {
            console.error('Error loading roles:', error);
            // Role is optional, so we can continue without it
        }
    }
    
    // Handle booking form submission
    if (bookingForm) {
        bookingForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            bookingError.classList.add('hidden');
            
            const formData = new FormData(bookingForm);
            const bookingData = {
                title: formData.get('title'),
                item_name: formData.get('item_name'),
                description: formData.get('description') || '',
                booking_type: formData.get('booking_type') || null,
                status: formData.get('status') || 'pending',
                start_date: formData.get('start_date'),
                end_date: formData.get('end_date'),
            };
            
            // Add user_role_id if selected
            const userRoleId = formData.get('user_role_id');
            if (userRoleId) {
                bookingData.user_role_id = parseInt(userRoleId);
            }
            
            // Convert date strings to ISO format if needed
            if (bookingData.start_date) {
                const startDate = new Date(bookingData.start_date);
                bookingData.start_date = startDate.toISOString();
            }
            if (bookingData.end_date) {
                const endDate = new Date(bookingData.end_date);
                bookingData.end_date = endDate.toISOString();
            }
            
            try {
                const response = await apiCall(API_BOOKINGS, {
                    method: 'POST',
                    body: JSON.stringify(bookingData)
                });
                
                // Success - close modal and reload bookings
                bookingModal.classList.add('hidden');
                bookingForm.reset();
                loadBookings();
                alert('Booking created successfully!');
            } catch (error) {
                // Show error message
                bookingError.textContent = `Error: ${error.message}`;
                bookingError.classList.remove('hidden');
                console.error('Booking creation error:', error);
            }
        });
    }
    
    // Order form modal handlers
    const orderModal = document.getElementById('order-modal');
    const orderForm = document.getElementById('order-form');
    const addOrderBtn = document.getElementById('add-order-btn');
    const closeOrderModal = document.getElementById('close-order-modal');
    const cancelOrderBtn = document.getElementById('cancel-order-btn');
    const orderError = document.getElementById('order-error');
    const addOrderItemBtn = document.getElementById('add-order-item-btn');
    const orderItemsContainer = document.getElementById('order-items-container');
    let orderItemIndex = 1;
    
    if (addOrderBtn) {
        addOrderBtn.addEventListener('click', function() {
            orderModal.classList.remove('hidden');
            loadVendorsForOrder();
            loadStatesForOrder();
        });
    }
    
    if (closeOrderModal) {
        closeOrderModal.addEventListener('click', function() {
            orderModal.classList.add('hidden');
            orderForm.reset();
            orderError.classList.add('hidden');
            resetOrderItems();
        });
    }
    
    if (cancelOrderBtn) {
        cancelOrderBtn.addEventListener('click', function() {
            orderModal.classList.add('hidden');
            orderForm.reset();
            orderError.classList.add('hidden');
            resetOrderItems();
        });
    }
    
    // Load vendors for order form
    async function loadVendorsForOrder() {
        const vendorSelect = document.getElementById('order-vendor');
        if (!vendorSelect) return;
        
        try {
            const data = await apiCall(API_VENDORS);
            const vendors = data.results || data;
            
            vendorSelect.innerHTML = '<option value="">Select Vendor</option>';
            vendors.forEach(vendor => {
                const option = document.createElement('option');
                option.value = vendor.id;
                option.textContent = vendor.vendor_name || `Vendor #${vendor.id}`;
                vendorSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading vendors for order:', error);
            vendorSelect.innerHTML = '<option value="">Error loading vendors</option>';
        }
    }
    
    // Load states for order form
    function loadStatesForOrder() {
        const stateSelect = document.getElementById('order-state');
        if (!stateSelect) return;
        
        const states = [
            'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
            'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
            'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
            'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
            'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
            'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
            'Andaman and Nicobar Islands', 'Chandigarh',
            'Dadra and Nagar Haveli and Daman and Diu', 'Delhi',
            'Jammu and Kashmir', 'Ladakh', 'Lakshadweep', 'Puducherry'
        ];
        
        stateSelect.innerHTML = '<option value="">Select State</option>';
        states.forEach(state => {
            const option = document.createElement('option');
            option.value = state;
            option.textContent = state;
            stateSelect.appendChild(option);
        });
    }
    
    // Reset order items to initial state
    function resetOrderItems() {
        orderItemIndex = 1;
        orderItemsContainer.innerHTML = `
            <div class="order-item-row" data-item-index="0">
                <div class="form-row">
                    <div class="form-group" style="flex: 2;">
                        <input type="text" name="items[0][item_name]" placeholder="Item Name *" required>
                    </div>
                    <div class="form-group" style="flex: 1;">
                        <input type="text" name="items[0][year_of_make]" placeholder="Year of Make">
                    </div>
                    <div class="form-group" style="flex: 1;">
                        <input type="number" step="0.01" name="items[0][estimate_cost]" placeholder="Estimate Cost">
                    </div>
                    <div class="form-group" style="flex: 1;">
                        <button type="button" class="btn secondary-btn remove-item-btn" style="display: none;">Remove</button>
                    </div>
                </div>
                <div class="form-group">
                    <textarea name="items[0][remark]" placeholder="Remark" rows="2"></textarea>
                </div>
            </div>
        `;
        updateRemoveButtons();
    }
    
    // Add new order item
    if (addOrderItemBtn) {
        addOrderItemBtn.addEventListener('click', function() {
            const newItem = document.createElement('div');
            newItem.className = 'order-item-row';
            newItem.setAttribute('data-item-index', orderItemIndex);
            newItem.innerHTML = `
                <div class="form-row">
                    <div class="form-group" style="flex: 2;">
                        <input type="text" name="items[${orderItemIndex}][item_name]" placeholder="Item Name *" required>
                    </div>
                    <div class="form-group" style="flex: 1;">
                        <input type="text" name="items[${orderItemIndex}][year_of_make]" placeholder="Year of Make">
                    </div>
                    <div class="form-group" style="flex: 1;">
                        <input type="number" step="0.01" name="items[${orderItemIndex}][estimate_cost]" placeholder="Estimate Cost">
                    </div>
                    <div class="form-group" style="flex: 1;">
                        <button type="button" class="btn secondary-btn remove-item-btn">Remove</button>
                    </div>
                </div>
                <div class="form-group">
                    <textarea name="items[${orderItemIndex}][remark]" placeholder="Remark" rows="2"></textarea>
                </div>
            `;
            orderItemsContainer.appendChild(newItem);
            orderItemIndex++;
            updateRemoveButtons();
        });
    }
    
    // Update remove buttons visibility
    function updateRemoveButtons() {
        const itemRows = orderItemsContainer.querySelectorAll('.order-item-row');
        itemRows.forEach((row, index) => {
            const removeBtn = row.querySelector('.remove-item-btn');
            if (removeBtn) {
                removeBtn.style.display = itemRows.length > 1 ? 'block' : 'none';
            }
        });
    }
    
    // Handle remove item button clicks
    orderItemsContainer.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-item-btn')) {
            const itemRow = e.target.closest('.order-item-row');
            if (itemRow && orderItemsContainer.querySelectorAll('.order-item-row').length > 1) {
                itemRow.remove();
                updateRemoveButtons();
            }
        }
    });
    
    // Handle order form submission
    if (orderForm) {
        orderForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            orderError.classList.add('hidden');
            
            const formData = new FormData(orderForm);
            
            // Build order data
            const orderData = {
                vendor: parseInt(formData.get('vendor')),
                invoice_number: formData.get('invoice_number'),
                invoice_date: formData.get('invoice_date'),
                state: formData.get('state'),
                items: []
            };
            
            // Collect all order items
            const itemRows = orderItemsContainer.querySelectorAll('.order-item-row');
            itemRows.forEach(row => {
                const itemName = row.querySelector('input[name*="[item_name]"]').value;
                if (itemName && itemName.trim()) {
                    const item = {
                        item_name: itemName.trim(),
                        year_of_make: row.querySelector('input[name*="[year_of_make]"]').value || null,
                        estimate_cost: row.querySelector('input[name*="[estimate_cost]"]').value || null,
                        remark: row.querySelector('textarea[name*="[remark]"]').value || ''
                    };
                    
                    // Convert estimate_cost to number if provided
                    if (item.estimate_cost) {
                        item.estimate_cost = parseFloat(item.estimate_cost);
                    }
                    
                    orderData.items.push(item);
                }
            });
            
            // Validate that at least one item is provided
            if (orderData.items.length === 0) {
                orderError.textContent = 'Error: At least one order item is required';
                orderError.classList.remove('hidden');
                return;
            }
            
            try {
                const response = await apiCall(API_ORDERS, {
                    method: 'POST',
                    body: JSON.stringify(orderData)
                });
                
                // Success - close modal and reload orders
                orderModal.classList.add('hidden');
                orderForm.reset();
                resetOrderItems();
                loadOrders();
                alert('Order created successfully!');
            } catch (error) {
                // Show error message
                let errorMessage = `Error: ${error.message}`;
                if (error.errorData) {
                    // Try to extract detailed error messages
                    const errorDetails = [];
                    for (const field in error.errorData) {
                        if (Array.isArray(error.errorData[field])) {
                            errorDetails.push(`${field}: ${error.errorData[field].join(', ')}`);
                        } else {
                            errorDetails.push(`${field}: ${error.errorData[field]}`);
                        }
                    }
                    if (errorDetails.length > 0) {
                        errorMessage += '\n' + errorDetails.join('\n');
                    }
                }
                orderError.textContent = errorMessage;
                orderError.classList.remove('hidden');
                console.error('Order creation error:', error);
                console.error('Order data that was sent:', orderData);
            }
        });
    }
    
    document.getElementById('manage-equipment-btn').addEventListener('click', function() {
        hideAllSections();
        equipmentSection.classList.remove('hidden');
        navLinks.forEach(l => l.classList.remove('active'));
        document.querySelector('a[href="#equipment"]').classList.add('active');
    });
    
    // Utility Functions
    function fetchUserProfile(token) {
        fetch(API_USERS_ME, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(userData => {
            const username = userData.username || userData.email.split('@')[0];
            currentUsername = username;
            userEmail = userData.email;
            showApp(username);
        })
        .catch(error => {
            console.error('Error fetching user profile:', error);
            // Token might be invalid, clear it and show login
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            currentUsername = '';
            userEmail = '';
            showLogin();
        });
    }
    
    function showLogin() {
        loginSection.classList.remove('hidden');
        dashboardSection.classList.add('hidden');
        document.querySelector('header').style.display = 'none';
        document.querySelector('footer').style.display = 'none';
        
        emailForm.style.display = 'block';
        otpForm.style.display = 'none';
        usernameInput.value = '';
        passwordInput.value = '';
        otpInput.value = '';
    }
    
    function showApp(username) {
        loginSection.classList.add('hidden');
        dashboardSection.classList.remove('hidden');
        document.querySelector('header').style.display = 'block';
        document.querySelector('footer').style.display = 'block';
        
        // Update username displays
        usernameDisplay.textContent = username;
        userGreeting.textContent = username;
        
        // Fetch user profile data and load team connect
        fetchUserProfileForTeamConnect();
        
        // Load dashboard counts
        loadDashboardCounts();
    }
    
    function hideAllSections() {
        dashboardSection.classList.add('hidden');
        tasksSection.classList.add('hidden');
        usersSection.classList.add('hidden');
        equipmentSection.classList.add('hidden');
        bookingsSection.classList.add('hidden');
    }
    
    function initializeSearch(inputId, sectionId) {
        const searchInput = document.getElementById(inputId);
        if (!searchInput) return;
        
        searchInput.addEventListener('keyup', function() {
            const searchValue = this.value.toLowerCase();
            const section = document.getElementById(sectionId);
            const rows = section.querySelectorAll('table tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchValue)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Add event listeners for edit and delete buttons
    document.querySelectorAll('.edit-btn').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.closest('tr').cells[0].textContent;
            alert('Edit item with ID: ' + id + '\nThis would open an edit form in a real application.');
        });
    });
    
    document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', function() {
            const id = this.closest('tr').cells[0].textContent;
            if (confirm('Are you sure you want to delete this item?')) {
                alert('Item with ID: ' + id + ' would be deleted in a real application.');
                // In a real app, this would make an API call and then remove the row
            }
        });
    });
    
    // Team Connect functionality
    function fetchUserProfileForTeamConnect() {
        const token = localStorage.getItem('access_token');
        if (!token) return;
        
        fetch(API_USERS_ME, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => response.json())
        .then(userData => {
            currentUserData = userData;
            // Get industry_id from user data or use default
            const industryId = userData.industry?.id;
            if (industryId) {
                loadTeamConnectData(industryId);
            } else {
                console.warn('User has no industry assigned');
                showTeamConnectError('No industry assigned. Please contact administrator.');
            }
        })
        .catch(error => {
            console.error('Error fetching user profile:', error);
        });
    }
    
    function loadTeamConnectData(industryId) {
        const token = localStorage.getItem('access_token');
        if (!token) return;
        
        // Show loading state for all tables
        showTeamConnectLoading();
        
        fetch(`${API_TEAM_CONNECT}?industry_id=${industryId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            teamConnectData = data;
            renderAllTeamConnectTables();
            initializeTeamConnectSearch();
        })
        .catch(error => {
            console.error('Error loading team connect data:', error);
            showTeamConnectError('Error loading team data. Please try again.');
        });
    }
    
    function showTeamConnectLoading() {
        const loadingHtml = '<tr><td colspan="6" style="padding: 20px; text-align: center; color: #757575;">Loading...</td></tr>';
        const loadingHtmlSingle = '<tr><td colspan="1" style="padding: 20px; text-align: center; color: #757575;">Loading...</td></tr>';
        document.getElementById('field-officer-tbody').innerHTML = loadingHtml;
        document.getElementById('owner-tbody').innerHTML = loadingHtml;
        document.getElementById('manager-tbody').innerHTML = loadingHtml;
        document.getElementById('farmer-tbody').innerHTML = loadingHtml;
        document.getElementById('booking-tbody').innerHTML = loadingHtmlSingle;
        document.getElementById('order-tbody').innerHTML = loadingHtmlSingle;
        document.getElementById('stock-item-tbody').innerHTML = loadingHtmlSingle;
        document.getElementById('vendor-tbody').innerHTML = loadingHtmlSingle;
    }
    
    function showTeamConnectError(message) {
        const errorHtml = `<tr><td colspan="6" style="padding: 20px; text-align: center; color: #f44336;">${message}</td></tr>`;
        const errorHtmlSingle = `<tr><td colspan="1" style="padding: 20px; text-align: center; color: #f44336;">${message}</td></tr>`;
        document.getElementById('field-officer-tbody').innerHTML = errorHtml;
        document.getElementById('owner-tbody').innerHTML = errorHtml;
        document.getElementById('manager-tbody').innerHTML = errorHtml;
        document.getElementById('farmer-tbody').innerHTML = errorHtml;
        document.getElementById('booking-tbody').innerHTML = errorHtmlSingle;
        document.getElementById('order-tbody').innerHTML = errorHtmlSingle;
        document.getElementById('stock-item-tbody').innerHTML = errorHtmlSingle;
        document.getElementById('vendor-tbody').innerHTML = errorHtmlSingle;
    }
    
    function renderAllTeamConnectTables() {
        if (!teamConnectData || !teamConnectData.users_by_role) {
            return;
        }
        
        // Update counts
        if (teamConnectData.counts) {
            const fieldOfficerCountEl = document.getElementById('field-officer-count');
            const ownerCountEl = document.getElementById('owner-count');
            const managerCountEl = document.getElementById('manager-count');
            const farmerCountEl = document.getElementById('farmer-count');
            const bookingCountEl = document.getElementById('booking-count');
            const orderCountEl = document.getElementById('order-count');
            const stockItemCountEl = document.getElementById('stock-item-count');
            const vendorCountEl = document.getElementById('vendor-count');
            
            if (fieldOfficerCountEl) fieldOfficerCountEl.textContent = `(${teamConnectData.counts.field_officers_count || 0})`;
            if (ownerCountEl) ownerCountEl.textContent = `(${teamConnectData.counts.owners_count || 0})`;
            if (managerCountEl) managerCountEl.textContent = `(${teamConnectData.counts.managers_count || 0})`;
            if (farmerCountEl) farmerCountEl.textContent = `(${teamConnectData.counts.farmers_count || 0})`;
            if (bookingCountEl) bookingCountEl.textContent = `(${teamConnectData.counts.bookings_count || 0})`;
            if (orderCountEl) orderCountEl.textContent = `(${teamConnectData.counts.orders_count || 0})`;
            if (stockItemCountEl) stockItemCountEl.textContent = `(${teamConnectData.counts.stock_items_count || 0})`;
            if (vendorCountEl) vendorCountEl.textContent = `(${teamConnectData.counts.vendors_count || 0})`;
        }
        
        // Render each table separately
        renderTeamConnectTable('field_officers', 'field-officer-tbody', teamConnectData.users_by_role.field_officers || []);
        renderTeamConnectTable('owners', 'owner-tbody', teamConnectData.users_by_role.owners || []);
        renderTeamConnectTable('managers', 'manager-tbody', teamConnectData.users_by_role.managers || []);
        renderTeamConnectTable('farmers', 'farmer-tbody', teamConnectData.users_by_role.farmers || []);
        
        // Render count tables for Booking, Orders, Stock Items, and Vendors
        renderCountTable('booking-tbody', teamConnectData.counts?.bookings_count || 0);
        renderCountTable('order-tbody', teamConnectData.counts?.orders_count || 0);
        renderCountTable('stock-item-tbody', teamConnectData.counts?.stock_items_count || 0);
        renderCountTable('vendor-tbody', teamConnectData.counts?.vendors_count || 0);
    }
    
    function renderTeamConnectTable(roleType, tbodyId, users) {
        const tbody = document.getElementById(tbodyId);
        if (!tbody) return;
        
        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="padding: 20px; text-align: center; color: #757575;">No users found for this role.</td></tr>';
            return;
        }
        
        // Render table rows
        tbody.innerHTML = users.map(user => {
            const roleDisplayName = user.role?.display_name || user.role?.name || 'N/A';
            const phoneNumber = user.phone_number || '-';
            const email = user.email || '-';
            
            return `
                <tr class="team-connect-row" data-role="${roleType}">
                    <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">${user.username || '-'}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">${phoneNumber}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">${email}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">
                        <span style="padding: 4px 12px; background-color: #2196f3; color: white; border-radius: 4px; font-size: 0.9rem;">
                            ${roleDisplayName}
                        </span>
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-family: monospace;">••••••••</span>
                            <button class="password-toggle-btn" style="background: none; border: none; cursor: pointer; color: #2196f3;" data-user-id="${user.id}">
                                <span style="font-size: 1.2rem;">👁️</span>
                            </button>
                        </div>
                    </td>
                    <td style="padding: 12px; border-bottom: 1px solid #e0e0e0;">
                        <button class="icon-btn edit-btn" data-user-id="${user.id}" style="margin-right: 8px; background: none; border: none; cursor: pointer; color: #2196f3; font-size: 1.2rem;">✏️</button>
                        <button class="icon-btn download-btn" data-user-id="${user.id}" style="margin-right: 8px; background: none; border: none; cursor: pointer; color: #2196f3; font-size: 1.2rem;">📥</button>
                        <button class="icon-btn delete-btn" data-user-id="${user.id}" style="background: none; border: none; cursor: pointer; color: #f44336; font-size: 1.2rem;">🗑️</button>
                    </td>
                </tr>
            `;
        }).join('');
    }
    
    function renderCountTable(tbodyId, count) {
        const tbody = document.getElementById(tbodyId);
        if (!tbody) return;
        
        tbody.innerHTML = `
            <tr>
                <td style="padding: 20px; text-align: center; font-size: 1.2rem; font-weight: bold; color: #2196f3;">
                    ${count}
                </td>
            </tr>
        `;
    }
    
    // Team Connect search functionality - searches across all tables
    function initializeTeamConnectSearch() {
        const searchInput = document.getElementById('team-connect-search');
        if (!searchInput) return;
        
        // Remove existing event listeners by cloning the input
        const newSearchInput = searchInput.cloneNode(true);
        searchInput.parentNode.replaceChild(newSearchInput, searchInput);
        
        newSearchInput.addEventListener('keyup', function() {
            const searchValue = this.value.toLowerCase();
            
            // Search across all three tables
            const allRows = document.querySelectorAll('.team-connect-row');
            
            allRows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchValue)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
    
    // Initialize team connect search on page load
    initializeTeamConnectSearch();
    
    // Dashboard Counts functionality
    function loadDashboardCounts() {
        const token = localStorage.getItem('access_token');
        if (!token) return;
        
        // First get user profile to get industry_id
        fetch(API_USERS_ME, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(userData => {
            const industryId = userData.industry?.id;
            if (!industryId) {
                console.warn('User has no industry assigned');
                return;
            }
            
            // Fetch dashboard counts
            return fetch(`${API_DASHBOARD_COUNTS}?industry_id=${industryId}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        })
        .then(response => {
            if (!response) return;
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(counts => {
            if (counts) {
                // Update the counts in the DOM
                updateDashboardCounts(counts);
            }
        })
        .catch(error => {
            console.error('Error loading dashboard counts:', error);
        });
    }
    
    // Update dashboard counts in the UI
    function updateDashboardCounts(counts) {
        // Update each count element
        const bookingsCountEl = document.getElementById('bookings-count');
        const vendorsCountEl = document.getElementById('vendors-count');
        const stockItemsCountEl = document.getElementById('stock-items-count');
        const ordersCountEl = document.getElementById('orders-count');
        
        if (bookingsCountEl && counts.bookings_count !== undefined) {
            bookingsCountEl.textContent = counts.bookings_count;
        }
        
        if (vendorsCountEl && counts.vendors_count !== undefined) {
            vendorsCountEl.textContent = counts.vendors_count;
        }
        
        if (stockItemsCountEl && counts.stock_items_count !== undefined) {
            stockItemsCountEl.textContent = counts.stock_items_count;
        }
        
        if (ordersCountEl && counts.orders_count !== undefined) {
            ordersCountEl.textContent = counts.orders_count;
        }
    }
    
    // Helper function to get auth headers
    function getAuthHeaders() {
        const token = localStorage.getItem('access_token');
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }
    
    // Helper function for API calls with error handling
    async function apiCall(url, options = {}) {
        const token = localStorage.getItem('access_token');
        if (!token) {
            throw new Error('Not authenticated. Please login again.');
        }
        
        const defaultOptions = {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        try {
            const response = await fetch(url, defaultOptions);
            
            // Handle 401 Unauthorized - token expired
            if (response.status === 401) {
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                showLogin();
                throw new Error('Session expired. Please login again.');
            }
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Request failed' }));
                const errorObj = new Error(error.detail || error.message || `HTTP ${response.status}`);
                errorObj.response = response;
                errorObj.errorData = error;
                throw errorObj;
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
    
    // BOOKINGS API Functions
    async function loadBookings() {
        const tbody = document.getElementById('bookings-tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '<tr><td colspan="7" style="padding: 20px; text-align: center; color: #757575;">Loading...</td></tr>';
        
        try {
            const data = await apiCall(API_BOOKINGS);
            const bookings = data.results || data;
            displayBookings(bookings);
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="7" style="padding: 20px; text-align: center; color: #f44336;">Error: ${error.message}</td></tr>`;
        }
    }
    
    function displayBookings(bookings) {
        const tbody = document.getElementById('bookings-tbody');
        if (!tbody) return;
        
        if (bookings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="padding: 20px; text-align: center; color: #757575;">No bookings found.</td></tr>';
            return;
        }
        
        tbody.innerHTML = bookings.map(booking => {
            const startDate = new Date(booking.start_date);
            const endDate = new Date(booking.end_date);
            const statusClass = booking.status === 'approved' ? 'status-approved' : 
                              booking.status === 'pending' ? 'status-pending' : 
                              booking.status === 'completed' ? 'status-completed' : 'status-pending';
            
            return `
                <tr>
                    <td>${booking.id}</td>
                    <td>${booking.title || 'N/A'}</td>
                    <td>${booking.booking_type || 'N/A'}</td>
                    <td><span class="tag ${statusClass}">${booking.status || 'N/A'}</span></td>
                    <td>${startDate.toLocaleString()}</td>
                    <td>${endDate.toLocaleString()}</td>
                    <td>
                        <button class="icon-btn edit-btn" onclick="editBooking(${booking.id})">Edit</button>
                        <button class="icon-btn delete-btn" onclick="deleteBooking(${booking.id})">Delete</button>
                    </td>
                </tr>
            `;
        }).join('');
    }
    
    // VENDORS API Functions
    async function loadVendors() {
        const tbody = document.getElementById('vendors-tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '<tr><td colspan="8" style="padding: 20px; text-align: center; color: #757575;">Loading...</td></tr>';
        
        try {
            const data = await apiCall(API_VENDORS);
            const vendors = data.results || data;
            displayVendors(vendors);
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="8" style="padding: 20px; text-align: center; color: #f44336;">Error: ${error.message}</td></tr>`;
        }
    }
    
    function displayVendors(vendors) {
        const tbody = document.getElementById('vendors-tbody');
        if (!tbody) return;
        
        if (vendors.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="padding: 20px; text-align: center; color: #757575;">No vendors found.</td></tr>';
            return;
        }
        
        tbody.innerHTML = vendors.map(vendor => {
            const ratingStars = vendor.rating ? '⭐'.repeat(vendor.rating) : 'N/A';
            return `
                <tr>
                    <td>${vendor.id}</td>
                    <td>${vendor.vendor_name || 'N/A'}</td>
                    <td>${vendor.contact_person || 'N/A'}</td>
                    <td>${vendor.email || 'N/A'}</td>
                    <td>${vendor.phone || 'N/A'}</td>
                    <td>${vendor.gstin_number || 'N/A'}</td>
                    <td>${ratingStars}</td>
                    <td>
                        <button class="icon-btn edit-btn" onclick="editVendor(${vendor.id})">Edit</button>
                        <button class="icon-btn delete-btn" onclick="deleteVendor(${vendor.id})">Delete</button>
                    </td>
                </tr>
            `;
        }).join('');
    }
    
    // ORDERS API Functions
    async function loadOrders() {
        const tbody = document.getElementById('orders-tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '<tr><td colspan="7" style="padding: 20px; text-align: center; color: #757575;">Loading...</td></tr>';
        
        try {
            const data = await apiCall(API_ORDERS);
            const orders = data.results || data;
            displayOrders(orders);
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="7" style="padding: 20px; text-align: center; color: #f44336;">Error: ${error.message}</td></tr>`;
        }
    }
    
    function displayOrders(orders) {
        const tbody = document.getElementById('orders-tbody');
        if (!tbody) return;
        
        if (orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="padding: 20px; text-align: center; color: #757575;">No orders found.</td></tr>';
            return;
        }
        
        tbody.innerHTML = orders.map(order => {
            const invoiceDate = new Date(order.invoice_date);
            const itemsCount = order.items ? order.items.length : 0;
            
            return `
                <tr>
                    <td>${order.id}</td>
                    <td>${order.invoice_number || 'N/A'}</td>
                    <td>${order.vendor_name || 'N/A'}</td>
                    <td>${invoiceDate.toLocaleDateString()}</td>
                    <td>${order.state || 'N/A'}</td>
                    <td>${itemsCount}</td>
                    <td>
                        <button class="icon-btn edit-btn" onclick="viewOrder(${order.id})">View</button>
                        <button class="icon-btn delete-btn" onclick="deleteOrder(${order.id})">Delete</button>
                    </td>
                </tr>
            `;
        }).join('');
    }
    
    // STOCK ITEMS API Functions
    async function loadStockItems() {
        const tbody = document.getElementById('stock-tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '<tr><td colspan="8" style="padding: 20px; text-align: center; color: #757575;">Loading...</td></tr>';
        
        try {
            const data = await apiCall(API_STOCK);
            const stockItems = data.results || data;
            displayStockItems(stockItems);
        } catch (error) {
            tbody.innerHTML = `<tr><td colspan="8" style="padding: 20px; text-align: center; color: #f44336;">Error: ${error.message}</td></tr>`;
        }
    }
    
    function displayStockItems(stockItems) {
        const tbody = document.getElementById('stock-tbody');
        if (!tbody) return;
        
        if (stockItems.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="padding: 20px; text-align: center; color: #757575;">No stock items found.</td></tr>';
            return;
        }
        
        tbody.innerHTML = stockItems.map(item => {
            const statusClass = item.status === 'working' ? 'status-completed' : 
                              item.status === 'maintenance' ? 'status-pending' : 
                              item.status === 'damaged' ? 'status-cancelled' : 'status-pending';
            
            return `
                <tr>
                    <td>${item.id}</td>
                    <td>${item.item_name || 'N/A'}</td>
                    <td>${item.item_type_display || item.item_type || 'N/A'}</td>
                    <td>${item.make || 'N/A'}</td>
                    <td>${item.year_of_make || 'N/A'}</td>
                    <td><span class="tag ${statusClass}">${item.status_display || item.status || 'N/A'}</span></td>
                    <td>₹${item.estimate_cost || '0.00'}</td>
                    <td>
                        <button class="icon-btn edit-btn" onclick="editStock(${item.id})">Edit</button>
                        <button class="icon-btn delete-btn" onclick="deleteStock(${item.id})">Delete</button>
                    </td>
                </tr>
            `;
        }).join('');
    }
    
    // Debounce helper function
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Search functionality for new sections
    const vendorSearchInput = document.getElementById('vendor-search');
    if (vendorSearchInput) {
        vendorSearchInput.addEventListener('keyup', debounce(async function() {
            const searchValue = this.value;
            if (searchValue.length > 2 || searchValue.length === 0) {
                try {
                    const url = searchValue ? `${API_VENDORS}?search=${encodeURIComponent(searchValue)}` : API_VENDORS;
                    const data = await apiCall(url);
                    displayVendors(data.results || data);
                } catch (error) {
                    console.error('Search error:', error);
                }
            }
        }, 500));
    }
    
    const orderSearchInput = document.getElementById('order-search');
    if (orderSearchInput) {
        orderSearchInput.addEventListener('keyup', debounce(async function() {
            const searchValue = this.value;
            if (searchValue.length > 2 || searchValue.length === 0) {
                try {
                    const url = searchValue ? `${API_ORDERS}?search=${encodeURIComponent(searchValue)}` : API_ORDERS;
                    const data = await apiCall(url);
                    displayOrders(data.results || data);
                } catch (error) {
                    console.error('Search error:', error);
                }
            }
        }, 500));
    }
    
    const stockSearchInput = document.getElementById('stock-search');
    if (stockSearchInput) {
        stockSearchInput.addEventListener('keyup', debounce(async function() {
            const searchValue = this.value;
            if (searchValue.length > 2 || searchValue.length === 0) {
                try {
                    const url = searchValue ? `${API_STOCK}?search=${encodeURIComponent(searchValue)}` : API_STOCK;
                    const data = await apiCall(url);
                    displayStockItems(data.results || data);
                } catch (error) {
                    console.error('Search error:', error);
                }
            }
        }, 500));
    }
    
    // Placeholder functions for edit/delete operations
    window.editBooking = function(id) {
        alert(`Edit booking ${id} - Feature coming soon!`);
    };
    
    window.deleteBooking = async function(id) {
        if (!confirm('Are you sure you want to delete this booking?')) return;
        try {
            await apiCall(`${API_BOOKINGS}${id}/`, { method: 'DELETE' });
            loadBookings();
        } catch (error) {
            alert('Error deleting booking: ' + error.message);
        }
    };
    
    window.editVendor = async function(id) {
        try {
            // Fetch vendor data
            const vendor = await apiCall(`${API_VENDORS}${id}/`);
            
            // Populate form with vendor data
            document.getElementById('vendor-name').value = vendor.vendor_name || '';
            document.getElementById('vendor-contact-person').value = vendor.contact_person || '';
            document.getElementById('vendor-email').value = vendor.email || '';
            document.getElementById('vendor-phone').value = vendor.phone || '';
            document.getElementById('vendor-gstin').value = vendor.gstin_number || '';  // IMPORTANT: Include GSTIN
            document.getElementById('vendor-city').value = vendor.city || '';
            document.getElementById('vendor-address').value = vendor.address || '';
            document.getElementById('vendor-website').value = vendor.website || '';
            document.getElementById('vendor-rating').value = vendor.rating || '';
            document.getElementById('vendor-notes').value = vendor.notes || '';
            
            // Load states if not already loaded
            loadIndianStates();
            // Set state after loading
            setTimeout(() => {
                document.getElementById('vendor-state').value = vendor.state || '';
            }, 100);
            
            // Change form to update mode
            vendorForm.dataset.vendorId = id;
            document.querySelector('#vendor-modal h2').textContent = 'Edit Vendor';
            document.querySelector('#vendor-modal .btn.primary-btn').textContent = 'Update Vendor';
            
            vendorModal.classList.remove('hidden');
        } catch (error) {
            alert('Error loading vendor: ' + error.message);
        }
    };
    
    window.deleteVendor = async function(id) {
        if (!confirm('Are you sure you want to delete this vendor?')) return;
        try {
            await apiCall(`${API_VENDORS}${id}/`, { method: 'DELETE' });
            loadVendors();
        } catch (error) {
            alert('Error deleting vendor: ' + error.message);
        }
    };
    
    window.viewOrder = function(id) {
        alert(`View order ${id} - Feature coming soon!`);
    };
    
    window.deleteOrder = async function(id) {
        if (!confirm('Are you sure you want to delete this order?')) return;
        try {
            await apiCall(`${API_ORDERS}${id}/`, { method: 'DELETE' });
            loadOrders();
        } catch (error) {
            alert('Error deleting order: ' + error.message);
        }
    };
    
    window.editStock = function(id) {
        alert(`Edit stock item ${id} - Feature coming soon!`);
    };
    
    window.deleteStock = async function(id) {
        if (!confirm('Are you sure you want to delete this stock item?')) return;
        try {
            await apiCall(`${API_STOCK}${id}/`, { method: 'DELETE' });
            loadStockItems();
        } catch (error) {
            alert('Error deleting stock item: ' + error.message);
        }
    };
}); 