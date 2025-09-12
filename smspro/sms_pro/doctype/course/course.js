// Copyright (c) 2024, Mr Linh Vu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Course', {
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.name) {
			frm.add_custom_button(__('View Enrollments'), function() {
				frappe.route_options = {
					"course": frm.doc.name
				};
				frappe.set_route("List", "Student Enrollment");
			}, __("View"));
			
			frm.add_custom_button(__('View Revenue'), function() {
				frm.call('get_revenue').then(r => {
					if (r.message) {
						frappe.msgprint({
							title: __('Course Revenue'),
							message: __('Total Revenue: {0}', [format_currency(r.message, frm.doc.currency || 'VND')])
						});
					}
				});
			}, __("Analytics"));
		}
	},
	
	course_code: function(frm) {
		// Auto-generate course code if empty
		if (!frm.doc.course_code) {
			frm.call('generate_course_code').then(r => {
				if (r.message) {
					frm.set_value('course_code', r.message);
				}
			});
		}
	},
	
	course_fee: function(frm) {
		// Validate course fee
		if (frm.doc.course_fee && frm.doc.course_fee <= 0) {
			frappe.msgprint(__('Course fee must be greater than 0'));
			frm.set_value('course_fee', '');
		}
	},
	
	duration_months: function(frm) {
		// Validate duration
		if (frm.doc.duration_months && frm.doc.duration_months <= 0) {
			frappe.msgprint(__('Duration must be greater than 0 months'));
			frm.set_value('duration_months', '');
		}
	},
	
	sessions_per_week: function(frm) {
		// Validate sessions per week
		if (frm.doc.sessions_per_week && frm.doc.sessions_per_week <= 0) {
			frappe.msgprint(__('Sessions per week must be greater than 0'));
			frm.set_value('sessions_per_week', '');
		}
	}
});
