# Copyright (c) 2024, Mr Linh Vu and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta


class FeeInvoice(Document):
	def validate(self):
		# Validate dates
		if self.invoice_date and self.due_date and self.invoice_date > self.due_date:
			frappe.throw("Due date cannot be before invoice date")
		
		# Validate amounts
		if self.course_fee and self.course_fee <= 0:
			frappe.throw("Course fee must be greater than 0")
		
		if self.discount_amount and self.discount_amount < 0:
			frappe.throw("Discount amount cannot be negative")
		
		# Calculate amounts
		self.calculate_amounts()
		
		# Update payment status
		self.update_payment_status()
		
		# Update status based on payment
		self.update_status()
	
	def calculate_amounts(self):
		"""Calculate total and outstanding amounts"""
		# Calculate total amount
		course_fee = self.course_fee or 0
		discount = self.discount_amount or 0
		self.total_amount = course_fee - discount
		
		# Calculate outstanding amount
		paid_amount = self.paid_amount or 0
		self.outstanding_amount = max(0, self.total_amount - paid_amount)
	
	def update_payment_status(self):
		"""Update payment status based on paid amount"""
		if not self.total_amount or self.total_amount <= 0:
			self.payment_status = "Unpaid"
			return
		
		paid_amount = self.paid_amount or 0
		
		if paid_amount == 0:
			self.payment_status = "Unpaid"
		elif paid_amount >= self.total_amount:
			self.payment_status = "Paid"
		else:
			self.payment_status = "Partially Paid"
	
	def update_status(self):
		"""Update status based on payment and due date"""
		if self.payment_status == "Paid":
			self.status = "Paid"
		elif self.payment_status == "Unpaid":
			# Check if overdue
			if self.due_date and self.due_date < datetime.now().date():
				self.status = "Overdue"
			else:
				self.status = "Submitted"
		else:  # Partially Paid
			if self.due_date and self.due_date < datetime.now().date():
				self.status = "Overdue"
			else:
				self.status = "Submitted"
	
	def on_update(self):
		# Update enrollment details
		self.update_enrollment_details()
		
		# Update payment tracking
		self.update_payment_tracking()
	
	def update_enrollment_details(self):
		"""Update student, course, and batch details from enrollment"""
		if not self.student_enrollment:
			return
		
		enrollment = frappe.get_doc("Student Enrollment", self.student_enrollment)
		
		# Update fields from enrollment
		self.student = enrollment.student
		self.student_name = enrollment.student_name
		self.course = enrollment.course
		self.course_name = enrollment.course_name
		self.batch = enrollment.batch
		self.batch_name = enrollment.batch_name
		
		# Update fees from enrollment if not manually set
		if not self.course_fee:
			self.course_fee = enrollment.course_fee
		if not self.discount_amount:
			self.discount_amount = enrollment.discount_amount
	
	def update_payment_tracking(self):
		"""Update payment tracking information"""
		# Get latest payment date
		latest_payment = frappe.db.sql("""
			SELECT MAX(pe.posting_date) as last_payment_date,
				   SUM(pe.paid_amount) as total_paid
			FROM `tabPayment Entry` pe
			WHERE pe.reference_doctype = 'Fee Invoice'
			AND pe.reference_name = %s
			AND pe.docstatus = 1
		""", (self.name,), as_dict=True)
		
		if latest_payment and latest_payment[0].last_payment_date:
			self.last_payment_date = latest_payment[0].last_payment_date
			self.paid_amount = latest_payment[0].total_paid or 0
		
		# Recalculate outstanding amount
		self.outstanding_amount = max(0, self.total_amount - (self.paid_amount or 0))
	
	@frappe.whitelist()
	def get_payment_history(self):
		"""Get payment history for this invoice"""
		payments = frappe.get_all(
			"Payment Entry",
			filters={
				"reference_name": self.name,
				"reference_doctype": "Fee Invoice",
				"docstatus": 1
			},
			fields=["name", "posting_date", "paid_amount", "reference_no", "mode_of_payment"],
			order_by="posting_date desc"
		)
		return payments
	
	@frappe.whitelist()
	def send_reminder(self):
		"""Send payment reminder to student"""
		if not self.student:
			frappe.throw("Student not found")
		
		student_email = frappe.get_value("Student", self.student, "email")
		if not student_email:
			frappe.throw("Student email not found")
		
		# Create communication
		communication = frappe.new_doc("Communication")
		communication.communication_type = "Communication"
		communication.communication_medium = "Email"
		communication.subject = f"Payment Reminder - Invoice {self.name}"
		communication.sent_or_received = "Sent"
		communication.sender = frappe.session.user
		communication.recipients = student_email
		communication.content = f"""
		Dear Student,
		
		This is a reminder that payment for invoice {self.name} is due.
		
		Invoice Details:
		- Invoice Number: {self.name}
		- Course: {self.course_name}
		- Amount Due: {self.outstanding_amount}
		- Due Date: {self.due_date}
		
		Please make payment at your earliest convenience.
		
		Thank you.
		"""
		communication.insert()
		communication.send()
		
		frappe.msgprint(f"Payment reminder sent to {student_email}")
	
	@frappe.whitelist()
	def mark_as_paid(self):
		"""Mark invoice as paid manually"""
		if self.payment_status == "Paid":
			frappe.throw("Invoice is already marked as paid")
		
		self.paid_amount = self.total_amount
		self.outstanding_amount = 0
		self.payment_status = "Paid"
		self.status = "Paid"
		self.last_payment_date = datetime.now().date()
		self.save()
		
		frappe.msgprint("Invoice marked as paid")
