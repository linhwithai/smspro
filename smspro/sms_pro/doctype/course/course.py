# Copyright (c) 2024, Mr Linh Vu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Course(Document):
	def validate(self):
		# Auto-generate Course Code if not provided
		if not self.course_code:
			self.course_code = self.generate_course_code()
		
		# Validate course fee
		if self.course_fee and self.course_fee <= 0:
			frappe.throw("Course fee must be greater than 0")
		
		# Validate duration
		if self.duration_months and self.duration_months <= 0:
			frappe.throw("Duration must be greater than 0 months")
		
		# Validate sessions per week
		if self.sessions_per_week and self.sessions_per_week <= 0:
			frappe.throw("Sessions per week must be greater than 0")
	
	def generate_course_code(self):
		"""Generate unique course code"""
		import random
		import string
		
		# Generate random 4-digit number
		course_code = ''.join(random.choices(string.digits, k=4))
		
		# Check if code already exists
		while frappe.db.exists("Course", {"course_code": course_code}):
			course_code = ''.join(random.choices(string.digits, k=4))
		
		return f"CRS{course_code}"
	
	def on_update(self):
		# Update course name if course code changes
		if self.course_code and not self.course_name:
			self.course_name = f"Course {self.course_code}"
	
	@frappe.whitelist()
	def get_enrollments(self):
		"""Get all enrollments for this course"""
		enrollments = frappe.get_all(
			"Student Enrollment",
			filters={"course": self.name},
			fields=["name", "student", "batch", "enrollment_date", "status"]
		)
		return enrollments
	
	@frappe.whitelist()
	def get_total_enrollments(self):
		"""Get total number of enrollments"""
		return frappe.db.count("Student Enrollment", {"course": self.name, "status": "Active"})
	
	@frappe.whitelist()
	def get_revenue(self):
		"""Calculate total revenue from this course"""
		enrollments = frappe.get_all(
			"Student Enrollment",
			filters={"course": self.name, "status": "Active"},
			fields=["name"]
		)
		
		total_revenue = 0
		for enrollment in enrollments:
			# Get fee invoices for this enrollment
			invoices = frappe.get_all(
				"Fee Invoice",
				filters={"student_enrollment": enrollment.name, "status": "Paid"},
				fields=["total_amount"]
			)
			
			for invoice in invoices:
				total_revenue += invoice.total_amount or 0
		
		return total_revenue
