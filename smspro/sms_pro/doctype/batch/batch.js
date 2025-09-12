// Copyright (c) 2024, Mr Linh Vu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Batch', {
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.name) {
			frm.add_custom_button(__('View Enrollments'), function() {
				frappe.route_options = {
					"batch": frm.doc.name
				};
				frappe.set_route("List", "Student Enrollment");
			}, __("View"));
			
			frm.add_custom_button(__('View Attendance'), function() {
				frappe.route_options = {
					"batch": frm.doc.name
				};
				frappe.set_route("List", "Attendance");
			}, __("Attendance"));
			
			frm.add_custom_button(__('Available Slots'), function() {
				frm.call('get_available_slots').then(r => {
					if (r.message !== undefined) {
						frappe.msgprint({
							title: __('Available Slots'),
							message: __('Available slots: {0}', [r.message])
						});
					}
				});
			}, __("Info"));
		}
	},
	
	course: function(frm) {
		// Auto-generate batch name when course is selected
		if (frm.doc.course && frm.doc.start_date) {
			frm.call('generate_batch_name').then(r => {
				if (r.message) {
					frm.set_value('batch_name', r.message);
				}
			});
		}
		
		// Set course fee if available
		if (frm.doc.course) {
			frappe.db.get_value('Course', frm.doc.course, 'course_fee', (r) => {
				if (r && r.course_fee) {
					frm.set_df_property('course_fee', 'read_only', 0);
					frm.set_value('course_fee', r.course_fee);
				}
			});
		}
	},
	
	start_date: function(frm) {
		// Auto-generate batch name when start date is set
		if (frm.doc.course && frm.doc.start_date) {
			frm.call('generate_batch_name').then(r => {
				if (r.message) {
					frm.set_value('batch_name', r.message);
				}
			});
		}
	},
	
	end_date: function(frm) {
		// Validate end date
		if (frm.doc.start_date && frm.doc.end_date) {
			if (frm.doc.end_date < frm.doc.start_date) {
				frappe.msgprint(__('End date cannot be before start date'));
				frm.set_value('end_date', '');
			}
		}
	},
	
	capacity: function(frm) {
		// Validate capacity
		if (frm.doc.capacity && frm.doc.capacity <= 0) {
			frappe.msgprint(__('Capacity must be greater than 0'));
			frm.set_value('capacity', '');
		}
		
		// Check if current enrollment exceeds capacity
		if (frm.doc.capacity && frm.doc.current_enrollment && frm.doc.current_enrollment > frm.doc.capacity) {
			frappe.msgprint(__('Current enrollment exceeds capacity'));
		}
	},
	
	current_enrollment: function(frm) {
		// Check if current enrollment exceeds capacity
		if (frm.doc.capacity && frm.doc.current_enrollment && frm.doc.current_enrollment > frm.doc.capacity) {
			frappe.msgprint(__('Current enrollment exceeds capacity'));
		}
	}
});
