// Copyright (c) 2024, Mr Linh Vu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Student', {
	refresh: function(frm) {
		// Add custom button to view enrollments
		if (frm.doc.name) {
			frm.add_custom_button(__('View Enrollments'), function() {
				frappe.route_options = {
					"student": frm.doc.name
				};
				frappe.set_route("List", "Student Enrollment");
			}, __("View"));
		}
	},
	
	student_id: function(frm) {
		// Auto-generate student ID if empty
		if (!frm.doc.student_id) {
			frm.call('generate_student_id').then(r => {
				if (r.message) {
					frm.set_value('student_id', r.message);
				}
			});
		}
	},
	
	first_name: function(frm) {
		// Update full name when first name changes
		if (frm.doc.first_name && frm.doc.last_name) {
			frm.set_value('full_name', frm.doc.first_name + ' ' + frm.doc.last_name);
		}
	},
	
	last_name: function(frm) {
		// Update full name when last name changes
		if (frm.doc.first_name && frm.doc.last_name) {
			frm.set_value('full_name', frm.doc.first_name + ' ' + frm.doc.last_name);
		}
	}
});

