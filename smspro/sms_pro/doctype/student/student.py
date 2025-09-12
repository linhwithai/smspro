# Copyright (c) 2024, Mr Linh Vu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Student(Document):
	def validate(self):
		# Auto-generate Student ID if not provided
		if not self.student_id:
			self.student_id = self.generate_student_id()
		
		# Validate email format
		if self.email and "@" not in self.email:
			frappe.throw("Please enter a valid email address")
		
		# Validate phone number
		if self.phone_number and len(self.phone_number) < 10:
			frappe.throw("Please enter a valid phone number")
	
	def generate_student_id(self):
		"""Generate unique student ID"""
		import random
		import string
		
		# Generate random 6-digit number
		student_id = ''.join(random.choices(string.digits, k=6))
		
		# Check if ID already exists
		while frappe.db.exists("Student", {"student_id": student_id}):
			student_id = ''.join(random.choices(string.digits, k=6))
		
		return f"STU{student_id}"
	
	def on_update(self):
		# Update full name
		self.full_name = f"{self.first_name} {self.last_name}"
	
	@frappe.whitelist()
	def get_enrollments(self):
		"""Get all enrollments for this student"""
		enrollments = frappe.get_all(
			"Student Enrollment",
			filters={"student": self.name},
			fields=["name", "course", "batch", "enrollment_date", "status"]
		)
		return enrollments

