// Copyright (c) 2024, Mr Linh Vu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Fee Invoice', {
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.name) {
			frm.add_custom_button(__('View Payments'), function() {
				frm.call('get_payment_history').then(r => {
					if (r.message && r.message.length > 0) {
						let message = __('Payment History:<br>');
						r.message.forEach(payment => {
							message += `${payment.posting_date}: ${format_currency(payment.paid_amount)} (${payment.mode_of_payment || 'N/A'})<br>`;
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
			
			if (frm.doc.status !== 'Paid' && frm.doc.status !== 'Cancelled') {
				frm.add_custom_button(__('Send Reminder'), function() {
					frappe.confirm(
						__('Send payment reminder to student?'),
						function() {
							frm.call('send_reminder').then(r => {
								frappe.msgprint(__('Reminder sent successfully'));
							});
						}
					);
				}, __("Actions"));
				
				frm.add_custom_button(__('Mark as Paid'), function() {
					frappe.confirm(
						__('Mark this invoice as paid?'),
						function() {
							frm.call('mark_as_paid').then(r => {
								frappe.msgprint(__('Invoice marked as paid'));
								frm.reload_doc();
							});
						}
					);
				}, __("Actions"));
			}
		}
	},
	
	student_enrollment: function(frm) {
		// Load enrollment details when enrollment is selected
		if (frm.doc.student_enrollment) {
			frappe.db.get_value('Student Enrollment', frm.doc.student_enrollment, [
				'student', 'student_name', 'course', 'course_name', 
				'batch', 'batch_name', 'course_fee', 'discount_amount'
			], (r) => {
				if (r) {
					frm.set_value('student', r.student);
					frm.set_value('student_name', r.student_name);
					frm.set_value('course', r.course);
					frm.set_value('course_name', r.course_name);
					frm.set_value('batch', r.batch);
					frm.set_value('batch_name', r.batch_name);
					
					if (!frm.doc.course_fee) {
						frm.set_value('course_fee', r.course_fee);
					}
					if (!frm.doc.discount_amount) {
						frm.set_value('discount_amount', r.discount_amount);
					}
					
					// Set default due date (30 days from invoice date)
					if (!frm.doc.due_date) {
						const invoice_date = frm.doc.invoice_date || new Date();
						const due_date = new Date(invoice_date);
						due_date.setDate(due_date.getDate() + 30);
						frm.set_value('due_date', due_date);
					}
				}
			});
		}
	},
	
	invoice_date: function(frm) {
		// Set default due date when invoice date changes
		if (frm.doc.invoice_date && !frm.doc.due_date) {
			const due_date = new Date(frm.doc.invoice_date);
			due_date.setDate(due_date.getDate() + 30);
			frm.set_value('due_date', due_date);
		}
		
		// Validate due date
		if (frm.doc.invoice_date && frm.doc.due_date) {
			if (frm.doc.due_date < frm.doc.invoice_date) {
				frappe.msgprint(__('Due date cannot be before invoice date'));
				frm.set_value('due_date', '');
			}
		}
	},
	
	due_date: function(frm) {
		// Validate due date
		if (frm.doc.invoice_date && frm.doc.due_date) {
			if (frm.doc.due_date < frm.doc.invoice_date) {
				frappe.msgprint(__('Due date cannot be before invoice date'));
				frm.set_value('due_date', '');
			}
		}
		
		// Check if overdue
		if (frm.doc.due_date) {
			const today = new Date();
			const due_date = new Date(frm.doc.due_date);
			
			if (due_date < today && frm.doc.status !== 'Paid') {
				frappe.msgprint(__('This invoice is overdue!'));
			}
		}
	},
	
	course_fee: function(frm) {
		// Recalculate amounts when course fee changes
		frm.trigger('calculate_amounts');
	},
	
	discount_amount: function(frm) {
		// Recalculate amounts when discount changes
		frm.trigger('calculate_amounts');
	},
	
	calculate_amounts: function(frm) {
		// Calculate total amount
		const course_fee = frm.doc.course_fee || 0;
		const discount = frm.doc.discount_amount || 0;
		const total_amount = course_fee - discount;
		
		frm.set_value('total_amount', total_amount);
		
		// Calculate outstanding amount
		const paid_amount = frm.doc.paid_amount || 0;
		const outstanding = Math.max(0, total_amount - paid_amount);
		frm.set_value('outstanding_amount', outstanding);
		
		// Update payment status
		if (paid_amount === 0) {
			frm.set_value('payment_status', 'Unpaid');
		} else if (paid_amount >= total_amount) {
			frm.set_value('payment_status', 'Paid');
		} else {
			frm.set_value('payment_status', 'Partially Paid');
		}
	},
	
	status: function(frm) {
		// Show warning if changing to cancelled
		if (frm.doc.status === 'Cancelled') {
			frappe.confirm(
				__('Are you sure you want to cancel this invoice?'),
				function() {
					// User confirmed
				},
				function() {
					// User cancelled - revert status
					frm.set_value('status', 'Draft');
				}
			);
		}
	}
});
