# Copyright (c) 2024, Mr Linh Vu and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


@frappe.whitelist()
def create_payment_entry_for_invoice(invoice_name, paid_amount, payment_date=None, mode_of_payment=None, reference_no=None):
	"""
	Create a Payment Entry for a Fee Invoice
	
	Args:
		invoice_name: Name of the Fee Invoice
		paid_amount: Amount to be paid
		payment_date: Date of payment (defaults to today)
		mode_of_payment: Payment method
		reference_no: Reference number for the payment
	"""
	try:
		# Get the invoice
		invoice = frappe.get_doc("Fee Invoice", invoice_name)
		
		if not invoice:
			frappe.throw(_("Invoice not found"))
		
		if not payment_date:
			payment_date = frappe.utils.today()
		
		# Create Payment Entry
		payment_entry = frappe.new_doc("Payment Entry")
		payment_entry.payment_type = "Receive"
		payment_entry.posting_date = payment_date
		payment_entry.party_type = "Customer"
		payment_entry.party = invoice.student  # Assuming student is linked to customer
		payment_entry.paid_amount = paid_amount
		payment_entry.received_amount = paid_amount
		
		# Set mode of payment
		if mode_of_payment:
			payment_entry.mode_of_payment = mode_of_payment
		else:
			# Get default mode of payment
			default_mode = frappe.get_value("Mode of Payment", {"enabled": 1}, "name")
			if default_mode:
				payment_entry.mode_of_payment = default_mode
		
		# Add reference to invoice
		payment_entry.append("references", {
			"reference_doctype": "Fee Invoice",
			"reference_name": invoice_name,
			"allocated_amount": paid_amount
		})
		
		# Set reference number if provided
		if reference_no:
			payment_entry.reference_no = reference_no
		
		payment_entry.insert()
		payment_entry.submit()
		
		# Update invoice payment status
		update_invoice_payment_status(invoice_name)
		
		return {
			"status": "success",
			"payment_entry": payment_entry.name,
			"message": _("Payment Entry {0} created successfully").format(payment_entry.name)
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Payment Entry Creation Error")
		return {
			"status": "error",
			"message": str(e)
		}


@frappe.whitelist()
def update_invoice_payment_status(invoice_name):
	"""
	Update payment status of a Fee Invoice based on Payment Entries
	"""
	try:
		invoice = frappe.get_doc("Fee Invoice", invoice_name)
		
		# Get total paid amount from Payment Entries
		total_paid = frappe.db.sql("""
			SELECT SUM(pe.paid_amount)
			FROM `tabPayment Entry` pe
			JOIN `tabPayment Entry Reference` per ON pe.name = per.parent
			WHERE per.reference_doctype = 'Fee Invoice'
			AND per.reference_name = %s
			AND pe.docstatus = 1
		""", (invoice_name,), as_list=True)[0][0] or 0
		
		# Update invoice
		invoice.paid_amount = total_paid
		invoice.outstanding_amount = max(0, invoice.total_amount - total_paid)
		
		# Update payment status
		if total_paid == 0:
			invoice.payment_status = "Unpaid"
		elif total_paid >= invoice.total_amount:
			invoice.payment_status = "Paid"
			invoice.status = "Paid"
		else:
			invoice.payment_status = "Partially Paid"
		
		# Update last payment date
		last_payment = frappe.db.sql("""
			SELECT pe.posting_date
			FROM `tabPayment Entry` pe
			JOIN `tabPayment Entry Reference` per ON pe.name = per.parent
			WHERE per.reference_doctype = 'Fee Invoice'
			AND per.reference_name = %s
			AND pe.docstatus = 1
			ORDER BY pe.posting_date DESC
			LIMIT 1
		""", (invoice_name,), as_list=True)
		
		if last_payment:
			invoice.last_payment_date = last_payment[0][0]
		
		invoice.save()
		
		# Update enrollment payment status
		update_enrollment_payment_status(invoice.student_enrollment)
		
		return {
			"status": "success",
			"paid_amount": total_paid,
			"outstanding_amount": invoice.outstanding_amount,
			"payment_status": invoice.payment_status
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Payment Status Update Error")
		return {
			"status": "error",
			"message": str(e)
		}


@frappe.whitelist()
def update_enrollment_payment_status(enrollment_name):
	"""
	Update payment status of a Student Enrollment based on related invoices
	"""
	try:
		enrollment = frappe.get_doc("Student Enrollment", enrollment_name)
		
		# Get all invoices for this enrollment
		invoices = frappe.get_all(
			"Fee Invoice",
			filters={"student_enrollment": enrollment_name},
			fields=["name", "total_amount", "paid_amount", "payment_status"]
		)
		
		total_invoice_amount = sum(inv.total_amount for inv in invoices)
		total_paid_amount = sum(inv.paid_amount for inv in invoices)
		
		# Update enrollment
		enrollment.paid_amount = total_paid_amount
		enrollment.outstanding_amount = max(0, enrollment.total_fee - total_paid_amount)
		
		# Update payment status
		if total_paid_amount == 0:
			enrollment.payment_status = "Unpaid"
		elif total_paid_amount >= enrollment.total_fee:
			enrollment.payment_status = "Paid"
		else:
			enrollment.payment_status = "Partially Paid"
		
		enrollment.save()
		
		return {
			"status": "success",
			"total_fee": enrollment.total_fee,
			"paid_amount": total_paid_amount,
			"outstanding_amount": enrollment.outstanding_amount,
			"payment_status": enrollment.payment_status
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Enrollment Payment Status Update Error")
		return {
			"status": "error",
			"message": str(e)
		}


@frappe.whitelist()
def get_payment_summary(student=None, batch=None, course=None):
	"""
	Get payment summary for students, batches, or courses
	"""
	try:
		filters = {}
		
		if student:
			filters["student"] = student
		if batch:
			filters["batch"] = batch
		if course:
			filters["course"] = course
		
		# Get enrollments
		enrollments = frappe.get_all(
			"Student Enrollment",
			filters=filters,
			fields=["name", "student", "student_name", "course", "course_name", 
					"batch", "batch_name", "total_fee", "paid_amount", 
					"outstanding_amount", "payment_status"]
		)
		
		# Calculate totals
		total_fees = sum(e.total_fee for e in enrollments)
		total_paid = sum(e.paid_amount for e in enrollments)
		total_outstanding = sum(e.outstanding_amount for e in enrollments)
		
		# Count by payment status
		status_count = {
			"Paid": len([e for e in enrollments if e.payment_status == "Paid"]),
			"Partially Paid": len([e for e in enrollments if e.payment_status == "Partially Paid"]),
			"Unpaid": len([e for e in enrollments if e.payment_status == "Unpaid"])
		}
		
		return {
			"status": "success",
			"enrollments": enrollments,
			"summary": {
				"total_enrollments": len(enrollments),
				"total_fees": total_fees,
				"total_paid": total_paid,
				"total_outstanding": total_outstanding,
				"payment_completion_rate": (total_paid / total_fees * 100) if total_fees > 0 else 0,
				"status_count": status_count
			}
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Payment Summary Error")
		return {
			"status": "error",
			"message": str(e)
		}


@frappe.whitelist()
def send_payment_reminders():
	"""
	Send payment reminders for overdue invoices
	This function is called daily via scheduler
	"""
	try:
		# Get overdue invoices
		overdue_invoices = frappe.get_all(
			"Fee Invoice",
			filters={
				"status": "Overdue",
				"outstanding_amount": [">", 0]
			},
			fields=["name", "student", "student_name", "outstanding_amount", "due_date"]
		)
		
		sent_count = 0
		
		for invoice in overdue_invoices:
			# Get student email
			student_email = frappe.get_value("Student", invoice.student, "email")
			
			if not student_email:
				continue
			
			# Check if reminder was sent today
			today = frappe.utils.today()
			existing_reminder = frappe.db.exists(
				"Communication",
				{
					"reference_doctype": "Fee Invoice",
					"reference_name": invoice.name,
					"subject": ["like", "%Payment Reminder%"],
					"creation": ["like", f"{today}%"]
				}
			)
			
			if existing_reminder:
				continue
			
			# Send reminder
			communication = frappe.new_doc("Communication")
			communication.communication_type = "Communication"
			communication.communication_medium = "Email"
			communication.subject = f"Payment Reminder - Invoice {invoice.name}"
			communication.sent_or_received = "Sent"
			communication.sender = "Administrator"
			communication.recipients = student_email
			communication.content = f"""
			Dear {invoice.student_name},
			
			This is a friendly reminder that payment for invoice {invoice.name} is overdue.
			
			Invoice Details:
			- Invoice Number: {invoice.name}
			- Outstanding Amount: ₫{invoice.outstanding_amount:,.0f}
			- Due Date: {invoice.due_date}
			- Days Overdue: {(frappe.utils.today() - invoice.due_date).days} days
			
			Please make payment at your earliest convenience to avoid any late fees.
			
			Thank you for your attention to this matter.
			
			Best regards,
			SMS Pro Team
			"""
			communication.insert()
			communication.send()
			
			sent_count += 1
		
		frappe.logger().info(f"Sent {sent_count} payment reminders")
		
		return {
			"status": "success",
			"reminders_sent": sent_count,
			"message": f"Sent {sent_count} payment reminders"
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Payment Reminder Error")
		return {
			"status": "error",
			"message": str(e)
		}
