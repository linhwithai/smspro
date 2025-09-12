# Copyright (c) 2024, Mr Linh Vu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class StudentEnrollment(Document):
	def validate(self):
		# Check if student is already enrolled in the same batch
		existing_enrollment = frappe.db.exists(
			"Student Enrollment",
			{
				"student": self.student,
				"batch": self.batch,
				"status": "Active",
				"name": ["!=", self.name]
			}
		)
		
		if existing_enrollment:
			frappe.throw(f"Student is already enrolled in this batch")
		
		# Check if batch has available capacity
		if not self.is_batch_available():
			frappe.throw(f"Batch is full. No available slots.")
		
		# Validate enrollment date
		if self.enrollment_date and self.course:
			self.validate_enrollment_date()
		
		# Calculate fees
		self.calculate_fees()
		
		# Update payment status
		self.update_payment_status()
	
	def is_batch_available(self):
		"""Check if batch has available capacity"""
		if not self.batch:
			return True
		
		batch_capacity = frappe.get_value("Batch", self.batch, "capacity")
		current_enrollment = frappe.get_value("Batch", self.batch, "current_enrollment")
		
		if not batch_capacity:
			return True
		
		return (current_enrollment or 0) < batch_capacity
	
	def validate_enrollment_date(self):
		"""Validate enrollment date against course and batch dates"""
		if not self.batch:
			return
		
		batch_start = frappe.get_value("Batch", self.batch, "start_date")
		batch_end = frappe.get_value("Batch", self.batch, "end_date")
		
		if batch_start and self.enrollment_date < batch_start:
			frappe.throw("Enrollment date cannot be before batch start date")
		
		if batch_end and self.enrollment_date > batch_end:
			frappe.throw("Enrollment date cannot be after batch end date")
	
	def calculate_fees(self):
		"""Calculate total fees"""
		if not self.course:
			return
		
		# Get course fee
		course_fee = frappe.get_value("Course", self.course, "course_fee") or 0
		self.course_fee = course_fee
		
		# Calculate total fee
		discount = self.discount_amount or 0
		self.total_fee = course_fee - discount
		
		# Calculate outstanding amount
		paid_amount = self.paid_amount or 0
		self.outstanding_amount = max(0, self.total_fee - paid_amount)
	
	def update_payment_status(self):
		"""Update payment status based on paid amount"""
		if not self.total_fee:
			self.payment_status = "Unpaid"
			return
		
		paid_amount = self.paid_amount or 0
		
		if paid_amount == 0:
			self.payment_status = "Unpaid"
		elif paid_amount >= self.total_fee:
			self.payment_status = "Paid"
		else:
			self.payment_status = "Partially Paid"
	
	def on_update(self):
		# Update student and course names
		self.update_names()
		
		# Update batch enrollment count
		self.update_batch_enrollment()
		
		# Create fee invoice if needed
		if self.status == "Active" and self.payment_status == "Unpaid":
			self.create_fee_invoice()
	
	def update_names(self):
		"""Update student, course, and batch names"""
		if self.student:
			student_name = frappe.get_value("Student", self.student, "first_name")
			student_last = frappe.get_value("Student", self.student, "last_name")
			if student_name and student_last:
				self.student_name = f"{student_name} {student_last}"
		
		if self.course:
			course_name = frappe.get_value("Course", self.course, "course_name")
			if course_name:
				self.course_name = course_name
		
		if self.batch:
			batch_name = frappe.get_value("Batch", self.batch, "batch_name")
			if batch_name:
				self.batch_name = batch_name
	
	def update_batch_enrollment(self):
		"""Update batch enrollment count"""
		if not self.batch:
			return
		
		# Count active enrollments for this batch
		count = frappe.db.count(
			"Student Enrollment",
			{
				"batch": self.batch,
				"status": "Active"
			}
		)
		
		# Update batch
		frappe.db.set_value("Batch", self.batch, "current_enrollment", count)
	
	def create_fee_invoice(self):
		"""Create fee invoice for this enrollment"""
		if not self.total_fee or self.total_fee <= 0:
			return
		
		# Check if invoice already exists
		existing_invoice = frappe.db.exists(
			"Fee Invoice",
			{"student_enrollment": self.name, "status": ["!=", "Cancelled"]}
		)
		
		if existing_invoice:
			return
		
		# Create new invoice
		invoice = frappe.new_doc("Fee Invoice")
		invoice.student_enrollment = self.name
		invoice.student = self.student
		invoice.course = self.course
		invoice.batch = self.batch
		invoice.invoice_date = self.enrollment_date
		invoice.due_date = self.enrollment_date
		invoice.total_amount = self.total_fee
		invoice.outstanding_amount = self.total_fee
		invoice.status = "Draft"
		invoice.insert()
	
	@frappe.whitelist()
	def get_payment_history(self):
		"""Get payment history for this enrollment"""
		payments = frappe.get_all(
			"Payment Entry",
			filters={
				"reference_name": self.name,
				"reference_doctype": "Student Enrollment"
			},
			fields=["name", "posting_date", "paid_amount", "reference_no"]
		)
		return payments
	
	@frappe.whitelist()
	def get_attendance_summary(self):
		"""Get attendance summary for this enrollment"""
		# This will be implemented when Attendance DocType is created
		return {
			"total_sessions": 0,
			"attended_sessions": 0,
			"attendance_rate": 0
		}
