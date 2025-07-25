// eSIM Admin Panel Custom JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('eSIM Custom JS loaded');
});

// Toast notification function
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// Enhanced toggle function with better UX
function togglePackageStatus(packageId, toggleUrl) {
    const button = event.target;
    const originalText = button.textContent;
    
    // Add loading state
    button.classList.add('loading');
    button.textContent = '';
    button.disabled = true;
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                     document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    
    fetch(`/admin/esim/esimpackage/toggle-active/${packageId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Update button appearance
            const newStatus = data.is_active;
            const newText = newStatus ? 'AKTİF' : 'PASİF';
            const newColor = newStatus ? '#28a745' : '#dc3545';
            const newClass = newStatus ? 'active' : 'inactive';
            
            // Remove old class and add new one
            button.classList.remove('active', 'inactive');
            button.classList.add(newClass);
            button.style.backgroundColor = newColor;
            button.textContent = newText;
            
            // Show success toast
            showToast(data.message, 'success');
        } else {
            // Show error toast
            showToast(data.message || 'Bir hata oluştu!', 'error');
            button.textContent = originalText;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Bağlantı hatası! Lütfen tekrar deneyin.', 'error');
        button.textContent = originalText;
    })
    .finally(() => {
        // Remove loading state
        button.classList.remove('loading');
        button.disabled = false;
    });
}

// Keyboard shortcuts for admin
document.addEventListener('keydown', function(e) {
    // Ctrl + S to save (prevent default browser save)
    if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        const saveButton = document.querySelector('input[name="_save"]');
        if (saveButton) {
            saveButton.click();
            showToast('Kaydetme işlemi başlatıldı...', 'success');
        }
    }
    
    // Ctrl + Alt + A to toggle all active states
    if (e.ctrlKey && e.altKey && e.key === 'a') {
        e.preventDefault();
        const toggleButtons = document.querySelectorAll('.toggle-btn');
        if (toggleButtons.length > 0) {
            if (confirm(`${toggleButtons.length} paketin durumunu değiştirmek istediğinize emin misiniz?`)) {
                toggleButtons.forEach((button, index) => {
                    setTimeout(() => {
                        button.click();
                    }, index * 100); // Stagger the clicks
                });
            }
        }
    }
});

// Enhanced table interactions
document.addEventListener('DOMContentLoaded', function() {
    // Add hover effects to table rows
    const tableRows = document.querySelectorAll('#result_list tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });
    
    // Add click to select functionality
    const checkboxes = document.querySelectorAll('input[name="_selected_action"]');
    tableRows.forEach((row, index) => {
        if (checkboxes[index]) {
            row.addEventListener('click', function(e) {
                // Don't trigger if clicking on a button or link
                if (!e.target.matches('button, a, input, select, textarea')) {
                    checkboxes[index].checked = !checkboxes[index].checked;
                    this.classList.toggle('selected', checkboxes[index].checked);
                }
            });
        }
    });
});

// Auto-refresh functionality (optional)
function enableAutoRefresh(intervalMinutes = 5) {
    if (window.location.pathname.includes('app/esim/admin/esim/esimpackage/')) {
        setInterval(() => {
            if (document.visibilityState === 'visible') {
                console.log('Auto-refreshing eSIM packages...');
                window.location.reload();
            }
        }, intervalMinutes * 60 * 1000);
    }
}

// Uncomment to enable auto-refresh every 5 minutes
// enableAutoRefresh(5);