// Copyright (c) 2024, Mr Linh Vu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Student Enrollment', {
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.name) {
			frm.add_custom_button(__('View Payments'), function() {
				frm.call('get_payment_history').then(r => {
					if (r.message && r.message.length > 0) {
						let message = __('Payment History:<br>');
						r.message.forEach(payment => {
							message += `${payment.posting_date}: ${format_currency(payment.paid_amount)}<br>`;
						});
						frappe.msgprint({
							title: __('Payment History'),
							message: message
						});
					} else {
						frappe.msgprint(__('No payments found'));
					}
				});
			}, __("View"));
			
			frm.add_custom_button(__('View Attendance'), function() {
				frm.call('get_attendance_summary').then(r => {
					if (r.message) {
						frappe.msgprint({
							title: __('Attendance Summary'),
							message: __('Total Sessions: {0}<br>Attended: {1}<br>Rate: {2}%', [
								r.message.total_sessions,
								r.message.attended_sessions,
								r.message.attendance_rate
							])
						});
					}
				});
			}, __("Attendance"));
		}
	},
	
	student: function(frm) {
		// Update student name when student is selected
		if (frm.doc.student) {
			frappe.db.get_value('Student', frm.doc.student, ['first_name', 'last_name'], (r) => {
				if (r && r.first_name && r.last_name) {
					frm.set_value('student_name', r.first_name + ' ' + r.last_name);
				}
			});
		}
	},
	
	course: function(frm) {
		// Update course name and fee when course is selected
		if (frm.doc.course) {
			frappe.db.get_value('Course', frm.doc.course, ['course_name', 'course_fee'], (r) => {
				if (r) {
					if (r.course_name) {
						frm.set_value('course_name', r.course_name);
					}
					if (r.course_fee) {
						frm.set_value('course_fee', r.course_fee);
					}
				}
			});
		}
	},
	
	batch: function(frm) {
		// Update batch name when batch is selected
		if (frm.doc.batch) {
			frappe.db.get_value('Batch', frm.doc.batch, 'batch_name', (r) => {
				if (r && r.batch_name) {
					frm.set_value('batch_name', r.batch_name);
				}
			});
			
			// Check batch capacity
			frappe.db.get_value('Batch', frm.doc.batch, ['capacity', 'current_enrollment'], (r) => {
				if (r) {
					const available = (r.capacity || 0) - (r.current_enrollment || 0);
					if (available <= 0) {
						frappe.msgprint(__('Warning: This batch is full!'));
					} else {
						frappe.msgprint(__('Available slots: {0}', [available]));
					}
				}
			});
		}
	},
	
	enrollment_date: function(frm) {
		// Validate enrollment date against batch dates
		if (frm.doc.enrollment_date && frm.doc.batch) {
			frappe.db.get_value('Batch', frm.doc.batch, ['start_date', 'end_date'], (r) => {
				if (r) {
					if (r.start_date && frm.doc.enrollment_date < r.start_date) {
						frappe.msgprint(__('Enrollment date cannot be before batch start date'));
					}
					if (r.end_date && frm.doc.enrollment_date > r.end_date) {
						frappe.msgprint(__('Enrollment date cannot be after batch end date'));
					}
				}
			});
		}
	},
	
	discount_amount: function(frm) {
		// Recalculate total fee when discount changes
		frm.trigger('calculate_total_fee');
	},
	
	course_fee: function(frm) {
		// Recalculate total fee when course fee changes
		frm.trigger('calculate_total_fee');
	},
	
	calculate_total_fee: function(frm) {
		// Calculate total fee
		const course_fee = frm.doc.course_fee || 0;
		const discount = frm.doc.discount_amount || 0;
		const total_fee = course_fee - discount;
		
		frm.set_value('total_fee', total_fee);
		
		// Update outstanding amount
		const paid_amount = frm.doc.paid_amount || 0;
		const outstanding = Math.max(0, total_fee - paid_amount);
		frm.set_value('outstanding_amount', outstanding);
		
		// Update payment status
		if (paid_amount === 0) {
			frm.set_value('payment_status', 'Unpaid');
		} else if (paid_amount >= total_fee) {
			frm.set_value('payment_status', 'Paid');
		} else {
			frm.set_value('payment_status', 'Partially Paid');
		}
	},
	
	status: function(frm) {
		// Show warning if changing to cancelled
		if (frm.doc.status === 'Cancelled') {
			frappe.confirm(
				__('Are you sure you want to cancel this enrollment?'),
				function() {
					// User confirmed
				},
				function() {
					// User cancelled - revert status
					frm.set_value('status', 'Active');
				}
			);
		}
	}
});
