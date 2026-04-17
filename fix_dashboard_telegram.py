#!/usr/bin/env python3
"""
Fix dashboard to show Telegram verification status in real-time
"""

def fix_dashboard_telegram_display():
    """Add Telegram verification status to dashboard student details"""
    
    # Fix 1: Update student details endpoint to include Telegram info
    with open('app/blueprints/accounts.py', 'r', encoding='utf-8') as f:
        accounts_content = f.read()
    
    old_student_details = '''            return jsonify({
                'success': True,
                'student': {
                    'id': student.id,
                    'roll_number': student.roll_number,
                    'name': student.name,
                    'email': student.email,
                    'phone': student.phone,
                    'department': student.department,
                    'semester': student.semester,
                    'latest_fee': {
                        'total_amount': latest_fee.total_amount if latest_fee else 0,
                        'paid_amount': latest_fee.paid_amount if latest_fee else 0,
                        'balance': latest_fee.balance if latest_fee else 0,
                        'last_updated': latest_fee.last_updated.isoformat() if latest_fee else None
                    } if latest_fee else None
                }
            })'''
    
    new_student_details = '''            return jsonify({
                'success': True,
                'student': {
                    'id': student.id,
                    'roll_number': student.roll_number,
                    'name': student.name,
                    'email': student.email,
                    'phone': student.phone,
                    'department': student.department,
                    'semester': student.semester,
                    'telegram_user_id': student.telegram_user_id,
                    'telegram_verified': student.telegram_verified,
                    'telegram_info': student.get_telegram_info(),
                    'latest_fee': {
                        'total_amount': latest_fee.total_amount if latest_fee else 0,
                        'paid_amount': latest_fee.paid_amount if latest_fee else 0,
                        'balance': latest_fee.balance if latest_fee else 0,
                        'last_updated': latest_fee.last_updated.isoformat() if latest_fee else None
                    } if latest_fee else None
                }
            })'''
    
    accounts_content = accounts_content.replace(old_student_details, new_student_details)
    
    with open('app/blueprints/accounts.py', 'w', encoding='utf-8') as f:
        f.write(accounts_content)
    
    # Fix 2: Add Telegram status to students fees dashboard template
    with open('app/templates/students_fees_dashboard.html', 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Add Telegram status column to the table
    old_table_header = '''                        <th>Payment Status</th>
                        <th>Last Updated</th>
                        <th>Actions</th>'''
    
    new_table_header = '''                        <th>Payment Status</th>
                        <th>Telegram Status</th>
                        <th>Last Updated</th>
                        <th>Actions</th>'''
    
    template_content = template_content.replace(old_table_header, new_table_header)
    
    # Add Telegram status data to table rows
    old_payment_status_cell = '''                        <td>
                            {% if student.latest_fee %}
                                {% if student.latest_fee.balance <= 0 %}
                                    <span class="badge bg-success">Paid</span>
                                {% elif student.latest_fee.paid_amount > 0 %}
                                    <span class="badge bg-warning">Partial</span>
                                {% else %}
                                    <span class="badge bg-danger">Unpaid</span>
                                {% endif %}
                            {% else %}
                                <span class="badge bg-secondary">No Record</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if student.latest_fee %}
                                <small>{{ student.latest_fee.last_updated.strftime('%d %b %Y, %I:%M %p') if student.latest_fee.last_updated else 'Never' }}</small>
                            {% else %}
                                <span class="text-muted">Never</span>
                            {% endif %}
                        </td>'''
    
    new_payment_status_cell = '''                        <td>
                            {% if student.latest_fee %}
                                {% if student.latest_fee.balance <= 0 %}
                                    <span class="badge bg-success">Paid</span>
                                {% elif student.latest_fee.paid_amount > 0 %}
                                    <span class="badge bg-warning">Partial</span>
                                {% else %}
                                    <span class="badge bg-danger">Unpaid</span>
                                {% endif %}
                            {% else %}
                                <span class="badge bg-secondary">No Record</span>
                            {% endif %}
                        </td>
                        <td>
                            {% if student.telegram_verified %}
                                <span class="badge bg-success" title="Telegram ID: {{ student.telegram_user_id }}">
                                    <i class="bi bi-telegram"></i> Verified
                                </span>
                            {% elif student.telegram_user_id %}
                                <span class="badge bg-warning" title="Telegram ID: {{ student.telegram_user_id }}">
                                    <i class="bi bi-telegram"></i> Linked
                                </span>
                            {% else %}
                                <span class="badge bg-secondary">
                                    <i class="bi bi-telegram"></i> Not Linked
                                </span>
                            {% endif %}
                        </td>
                        <td>
                            {% if student.latest_fee %}
                                <small>{{ student.latest_fee.last_updated.strftime('%d %b %Y, %I:%M %p') if student.latest_fee.last_updated else 'Never' }}</small>
                            {% else %}
                                <span class="text-muted">Never</span>
                            {% endif %}
                        </td>'''
    
    template_content = template_content.replace(old_payment_status_cell, new_payment_status_cell)
    
    # Fix 3: Add Telegram info to student details modal
    old_modal_content = '''            <div class="modal-body" id="studentDetailsContent">
                <!-- Content loaded via JavaScript -->
            </div>'''
    
    new_modal_content = '''            <div class="modal-body" id="studentDetailsContent">
                <!-- Content loaded via JavaScript -->
            </div>
            
            <script>
            // Enhanced student details function to show Telegram info
            function viewStudentDetails(studentId) {
                fetch(`/accounts/student/${studentId}/details`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            const student = data.student;
                            const content = `
                                <div class="row">
                                    <div class="col-md-6">
                                        <h6>Basic Information</h6>
                                        <p><strong>Roll Number:</strong> ${student.roll_number}</p>
                                        <p><strong>Name:</strong> ${student.name}</p>
                                        <p><strong>Email:</strong> ${student.email || 'N/A'}</p>
                                        <p><strong>Phone:</strong> ${student.phone}</p>
                                        <p><strong>Department:</strong> ${student.department || 'N/A'}</p>
                                        <p><strong>Semester:</strong> ${student.semester || 'N/A'}</p>
                                    </div>
                                    <div class="col-md-6">
                                        <h6>Telegram Verification</h6>
                                        <p><strong>Status:</strong> 
                                            ${student.telegram_verified ? 
                                                '<span class="badge bg-success"><i class="bi bi-telegram"></i> Verified</span>' : 
                                                student.telegram_user_id ? 
                                                    '<span class="badge bg-warning"><i class="bi bi-telegram"></i> Linked</span>' :
                                                    '<span class="badge bg-secondary"><i class="bi bi-telegram"></i> Not Linked</span>'
                                            }
                                        </p>
                                        ${student.telegram_user_id ? `<p><strong>Telegram ID:</strong> ${student.telegram_user_id}</p>` : ''}
                                        ${student.telegram_info ? `<p><small>${student.telegram_info.message || ''}</small></p>` : ''}
                                    </div>
                                </div>
                                ${student.latest_fee ? `
                                    <hr>
                                    <h6>Latest Fee Record</h6>
                                    <div class="row">
                                        <div class="col-md-3">
                                            <p><strong>Total Amount:</strong> <br>Rs. ${student.latest_fee.total_amount.toFixed(2)}</p>
                                        </div>
                                        <div class="col-md-3">
                                            <p><strong>Paid Amount:</strong> <br>Rs. ${student.latest_fee.paid_amount.toFixed(2)}</p>
                                        </div>
                                        <div class="col-md-3">
                                            <p><strong>Balance:</strong> <br>Rs. ${student.latest_fee.balance.toFixed(2)}</p>
                                        </div>
                                        <div class="col-md-3">
                                            <p><strong>Last Updated:</strong> <br>${new Date(student.latest_fee.last_updated).toLocaleString()}</p>
                                        </div>
                                    </div>
                                ` : '<p class="text-muted">No fee records found</p>'}
                            `;
                            document.getElementById('studentDetailsContent').innerHTML = content;
                            
                            // Show modal
                            const modal = new bootstrap.Modal(document.getElementById('studentDetailsModal'));
                            modal.show();
                        } else {
                            alert('Error loading student details: ' + data.message);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Error loading student details');
                    });
            }
            
            // Auto-refresh Telegram status every 30 seconds
            setInterval(() => {
                const rows = document.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    const studentId = row.querySelector('button[onclick*="viewStudentDetails"]')?.getAttribute('onclick').match(/viewStudentDetails\('(\d+)'\)/)?.[1];
                    if (studentId) {
                        fetch(`/accounts/student/${studentId}/details`)
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    const student = data.student;
                                    const telegramCell = row.querySelector('td:nth-child(9)'); // Telegram status column
                                    if (telegramCell) {
                                        let statusHtml = '';
                                        if (student.telegram_verified) {
                                            statusHtml = `<span class="badge bg-success" title="Telegram ID: ${student.telegram_user_id}"><i class="bi bi-telegram"></i> Verified</span>`;
                                        } else if (student.telegram_user_id) {
                                            statusHtml = `<span class="badge bg-warning" title="Telegram ID: ${student.telegram_user_id}"><i class="bi bi-telegram"></i> Linked</span>`;
                                        } else {
                                            statusHtml = `<span class="badge bg-secondary"><i class="bi bi-telegram"></i> Not Linked</span>`;
                                        }
                                        telegramCell.innerHTML = statusHtml;
                                    }
                                }
                            })
                            .catch(error => console.log('Auto-refresh error:', error));
                    }
                });
            }, 30000);
            </script>'''
    
    template_content = template_content.replace(old_modal_content, new_modal_content)
    
    with open('app/templates/students_fees_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(template_content)
    
    print("Fixed dashboard Telegram verification display!")
    print("\nChanges made:")
    print("1. Added telegram_user_id and telegram_verified to student details API")
    print("2. Added Telegram status column to students dashboard table")
    print("3. Enhanced student details modal with Telegram information")
    print("4. Added auto-refresh for Telegram status every 30 seconds")
    print("\nThe dashboard will now show real-time Telegram verification status!")

if __name__ == "__main__":
    fix_dashboard_telegram_display()
