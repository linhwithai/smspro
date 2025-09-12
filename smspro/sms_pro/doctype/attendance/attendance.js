// Copyright (c) 2024, Mr Linh Vu and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance', {
	refresh: function(frm) {
		// Add custom buttons
		if (frm.doc.name) {
			frm.add_custom_button(__('View Attendance Summary'), function() {
				frm.call('get_attendance_summary').then(r => {
					if (r.message) {
						const summary = r.message;
						const message = `
							<strong>Attendance Summary for ${frm.doc.student_name}:</strong><br><br>
							Total Sessions: ${summary.total_sessions}<br>
							Present: ${summary.attended_sessions}<br>
							Absent: ${summary.absent_sessions}<br>
							Late: ${summary.late_sessions}<br>
							Attendance Rate: ${summary.attendance_rate}%
						`;
						frappe.msgprint({
							title: __('Attendance Summary'),
							message: message
						});
					}
				});
			}, __("Analytics"));
		}
		
		// Add batch attendance button
		if (frm.doc.batch && frm.doc.attendance_date) {
			frm.add_custom_button(__('Mark Batch Attendance'), function() {
				frm.call('mark_batch_attendance', {
					batch: frm.doc.batch,
					attendance_date: frm.doc.attendance_date,
					attendance_list: []
				}).then(r => {
					frappe.msgprint(__('Batch attendance marked successfully'));
				});
			}, __("Batch"));
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
	
	batch: function(frm) {
		// Update batch and course information when batch is selected
		if (frm.doc.batch) {
			frappe.db.get_value('Batch', frm.doc.batch, ['batch_name', 'course', 'class_time'], (r) => {
				if (r) {
					if (r.batch_name) {
						frm.set_value('batch_name', r.batch_name);
					}
					if (r.course) {
						frm.set_value('course', r.course);
						// Get course name
						frappe.db.get_value('Course', r.course, 'course_name', (course_r) => {
							if (course_r && course_r.course_name) {
								frm.set_value('course_name', course_r.course_name);
							}
						});
					}
					if (r.class_time && !frm.doc.class_time) {
						frm.set_value('class_time', r.class_time);
					}
				}
			});
		}
	},
	
	attendance_date: function(frm) {
		// Validate attendance date
		if (frm.doc.attendance_date) {
			const today = new Date();
			const attendance_date = new Date(frm.doc.attendance_date);
			
			if (attendance_date > today) {
				frappe.msgprint(__('Attendance date cannot be in the future'));
				frm.set_value('attendance_date', '');
			}
		}
		
		// Check if attendance already exists
		if (frm.doc.student && frm.doc.batch && frm.doc.attendance_date) {
			frappe.db.exists('Attendance', {
				student: frm.doc.student,
				batch: frm.doc.batch,
				attendance_date: frm.doc.attendance_date,
				name: ['!=', frm.doc.name || '']
			}).then(exists => {
				if (exists) {
					frappe.msgprint(__('Attendance already marked for this student on this date'));
				}
			});
		}
	},
	
	status: function(frm) {
		// Add status-specific notes
		if (frm.doc.status === 'Absent') {
			if (!frm.doc.notes) {
				frm.set_value('notes', 'Absent');
			}
		} else if (frm.doc.status === 'Late') {
			if (!frm.doc.notes) {
				frm.set_value('notes', 'Late arrival');
			}
		} else if (frm.doc.status === 'Excused') {
			if (!frm.doc.notes) {
				frm.set_value('notes', 'Excused absence');
			}
		}
	}
});
