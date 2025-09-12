# Copyright (c) 2024, Mr Linh Vu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Attendance(Document):
	def validate(self):
		# Check if attendance already exists for this student, batch, and date
		existing_attendance = frappe.db.exists(
			"Attendance",
			{
				"student": self.student,
				"batch": self.batch,
				"attendance_date": self.attendance_date,
				"name": ["!=", self.name]
			}
		)
		
		if existing_attendance:
			frappe.throw(f"Attendance already marked for this student on {self.attendance_date}")
		
		# Validate attendance date is not in the future
		from datetime import date
		if self.attendance_date > date.today():
			frappe.throw("Attendance date cannot be in the future")
		
		# Update related information
		self.update_related_info()
	
	def update_related_info(self):
		"""Update student, batch, and course information"""
		# Update student name
		if self.student:
			student_name = frappe.get_value("Student", self.student, "first_name")
			student_last = frappe.get_value("Student", self.student, "last_name")
			if student_name and student_last:
				self.student_name = f"{student_name} {student_last}"
		
		# Update batch and course information
		if self.batch:
			batch_info = frappe.get_value("Batch", self.batch, ["batch_name", "course", "class_time"])
			if batch_info:
				if batch_info[0]:  # batch_name
					self.batch_name = batch_info[0]
				if batch_info[1]:  # course
					self.course = batch_info[1]
					# Get course name
					course_name = frappe.get_value("Course", batch_info[1], "course_name")
					if course_name:
						self.course_name = course_name
				if batch_info[2] and not self.class_time:  # class_time
					self.class_time = batch_info[2]
	
	def on_update(self):
		# Update enrollment attendance statistics
		self.update_enrollment_attendance()
	
	def update_enrollment_attendance(self):
		"""Update attendance statistics for student enrollment"""
		if not self.student or not self.batch:
			return
		
		# Find the enrollment for this student and batch
		enrollment = frappe.db.exists(
			"Student Enrollment",
			{
				"student": self.student,
				"batch": self.batch,
				"status": "Active"
			}
		)
		
		if not enrollment:
			return
		
		# Calculate attendance statistics
		total_sessions = frappe.db.count(
			"Attendance",
			{
				"student": self.student,
				"batch": self.batch,
				"attendance_date": ["<=", self.attendance_date]
			}
		)
		
		attended_sessions = frappe.db.count(
			"Attendance",
			{
				"student": self.student,
				"batch": self.batch,
				"attendance_date": ["<=", self.attendance_date],
				"status": "Present"
			}
		)
		
		attendance_rate = (attended_sessions / total_sessions * 100) if total_sessions > 0 else 0
		
		# Update enrollment with attendance statistics (if we add these fields later)
		# For now, we'll just log it
		frappe.logger().info(f"Student {self.student} attendance rate: {attendance_rate:.2f}%")
	
	@frappe.whitelist()
	def get_attendance_summary(self):
		"""Get attendance summary for this student in this batch"""
		if not self.student or not self.batch:
			return {}
		
		total_sessions = frappe.db.count(
			"Attendance",
			{
				"student": self.student,
				"batch": self.batch
			}
		)
		
		attended_sessions = frappe.db.count(
			"Attendance",
			{
				"student": self.student,
				"batch": self.batch,
				"status": "Present"
			}
		)
		
		absent_sessions = frappe.db.count(
			"Attendance",
			{
				"student": self.student,
				"batch": self.batch,
				"status": "Absent"
			}
		)
		
		late_sessions = frappe.db.count(
			"Attendance",
			{
				"student": self.student,
				"batch": self.batch,
				"status": "Late"
			}
		)
		
		attendance_rate = (attended_sessions / total_sessions * 100) if total_sessions > 0 else 0
		
		return {
			"total_sessions": total_sessions,
			"attended_sessions": attended_sessions,
			"absent_sessions": absent_sessions,
			"late_sessions": late_sessions,
			"attendance_rate": round(attendance_rate, 2)
		}
	
	@frappe.whitelist()
	def mark_batch_attendance(self, batch, attendance_date, attendance_list):
		"""Mark attendance for multiple students in a batch"""
		created_count = 0
		updated_count = 0
		
		for student_data in attendance_list:
			student = student_data.get("student")
			status = student_data.get("status", "Present")
			notes = student_data.get("notes", "")
			
			if not student:
				continue
			
			# Check if attendance already exists
			existing_attendance = frappe.db.exists(
				"Attendance",
				{
					"student": student,
					"batch": batch,
					"attendance_date": attendance_date
				}
			)
			
			if existing_attendance:
				# Update existing attendance
				attendance = frappe.get_doc("Attendance", existing_attendance)
				attendance.status = status
				attendance.notes = notes
				attendance.save()
				updated_count += 1
			else:
				# Create new attendance
				attendance = frappe.new_doc("Attendance")
				attendance.student = student
				attendance.batch = batch
				attendance.attendance_date = attendance_date
				attendance.status = status
				attendance.notes = notes
				attendance.insert()
				created_count += 1
		
		return {
			"created": created_count,
			"updated": updated_count,
			"total": created_count + updated_count
		}
