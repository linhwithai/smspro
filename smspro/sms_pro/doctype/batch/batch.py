# Copyright (c) 2024, Mr Linh Vu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Batch(Document):
	def validate(self):
		# Validate dates
		if self.start_date and self.end_date and self.start_date > self.end_date:
			frappe.throw("End date cannot be before start date")
		
		# Validate capacity
		if self.capacity and self.capacity <= 0:
			frappe.throw("Capacity must be greater than 0")
		
		# Validate current enrollment doesn't exceed capacity
		if self.current_enrollment and self.capacity and self.current_enrollment > self.capacity:
			frappe.throw("Current enrollment cannot exceed capacity")
		
		# Auto-generate batch name if not provided
		if not self.batch_name and self.course:
			self.batch_name = self.generate_batch_name()
	
	def generate_batch_name(self):
		"""Generate batch name from course and date"""
		if not self.course or not self.start_date:
			return ""
		
		course_name = frappe.get_value("Course", self.course, "course_name") or self.course
		start_month = self.start_date.strftime("%b")
		start_year = self.start_date.year
		
		return f"{course_name} - {start_month} {start_year}"
	
	def on_update(self):
		# Update current enrollment count
		self.update_enrollment_count()
	
	def update_enrollment_count(self):
		"""Update the current enrollment count"""
		count = frappe.db.count(
			"Student Enrollment",
			{
				"batch": self.name,
				"status": "Active"
			}
		)
		self.current_enrollment = count
	
	@frappe.whitelist()
	def get_enrollments(self):
		"""Get all enrollments for this batch"""
		enrollments = frappe.get_all(
			"Student Enrollment",
			filters={"batch": self.name},
			fields=["name", "student", "student_name", "enrollment_date", "status"]
		)
		return enrollments
	
	@frappe.whitelist()
	def get_attendance_summary(self):
		"""Get attendance summary for this batch"""
		# This will be implemented when Attendance DocType is created
		return {
			"total_sessions": 0,
			"attended_sessions": 0,
			"attendance_rate": 0
		}
	
	@frappe.whitelist()
	def get_available_slots(self):
		"""Get number of available slots in this batch"""
		if not self.capacity:
			return 0
		
		available = self.capacity - (self.current_enrollment or 0)
		return max(0, available)
	
	@frappe.whitelist()
	def is_full(self):
		"""Check if batch is full"""
		return self.get_available_slots() == 0
