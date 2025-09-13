# Copyright (c) 2024, Mr Linh Vu and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_dashboard_data():
	"""
	Get dashboard data for SMS Pro
	"""
	try:
		# Get total students
		total_students = frappe.db.count("Student", {"status": "Active"})
		
		# Get total courses
		total_courses = frappe.db.count("Course", {"status": "Active"})
		
		# Get total batches
		total_batches = frappe.db.count("Batch", {"status": "Active"})
		
		# Get total enrollments
		total_enrollments = frappe.db.count("Student Enrollment", {"status": "Active"})
		
		# Get financial data
		financial_data = frappe.db.sql("""
			SELECT 
				SUM(total_fee) as total_revenue,
				SUM(paid_amount) as total_paid,
				SUM(outstanding_amount) as total_outstanding
			FROM `tabStudent Enrollment`
			WHERE docstatus != 2
		""", as_dict=True)[0]
		
		total_revenue = financial_data.total_revenue or 0
		total_paid = financial_data.total_paid or 0
		total_outstanding = financial_data.total_outstanding or 0
		
		# Calculate collection rate
		collection_rate = (total_paid / total_revenue * 100) if total_revenue > 0 else 0
		
		# Get payment status distribution
		payment_status_data = frappe.db.sql("""
			SELECT 
				payment_status,
				COUNT(*) as count
			FROM `tabStudent Enrollment`
			WHERE docstatus != 2
			GROUP BY payment_status
		""", as_dict=True)
		
		payment_status_distribution = {}
		for item in payment_status_data:
			payment_status_distribution[item.payment_status] = item.count
		
		# Get recent enrollments
		recent_enrollments = frappe.get_all(
			"Student Enrollment",
			filters={"docstatus": 1},
			fields=["name", "student", "student_name", "course", "course_name", 
					"batch", "batch_name", "enrollment_date", "payment_status"],
			order_by="enrollment_date DESC",
			limit=5
		)
		
		# Get overdue payments
		overdue_payments = frappe.get_all(
			"Fee Invoice",
			filters={
				"status": "Overdue",
				"outstanding_amount": [">", 0]
			},
			fields=["name", "student", "student_name", "outstanding_amount", "due_date"],
			order_by="due_date ASC",
			limit=5
		)
		
		# Calculate days overdue
		for payment in overdue_payments:
			payment.days_overdue = (frappe.utils.today() - payment.due_date).days
		
		return {
			"status": "success",
			"data": {
				"statistics": {
					"total_students": total_students,
					"total_courses": total_courses,
					"total_batches": total_batches,
					"total_enrollments": total_enrollments
				},
				"financial": {
					"total_revenue": total_revenue,
					"total_paid": total_paid,
					"total_outstanding": total_outstanding,
					"collection_rate": round(collection_rate, 2)
				},
				"payment_status_distribution": payment_status_distribution,
				"recent_enrollments": recent_enrollments,
				"overdue_payments": overdue_payments
			}
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Dashboard Data Error")
		return {
			"status": "error",
			"message": str(e)
		}


@frappe.whitelist()
def get_revenue_chart_data(months=6):
	"""
	Get revenue chart data for the specified number of months
	"""
	try:
		# Get revenue data for the last N months
		revenue_data = frappe.db.sql("""
			SELECT 
				DATE_FORMAT(creation, '%%Y-%%m') as month,
				SUM(total_fee) as revenue
			FROM `tabStudent Enrollment`
			WHERE creation >= DATE_SUB(NOW(), INTERVAL %s MONTH)
			AND docstatus != 2
			GROUP BY DATE_FORMAT(creation, '%%Y-%%m')
			ORDER BY month ASC
		""", (months,), as_dict=True)
		
		# Get payment data
		payment_data = frappe.db.sql("""
			SELECT 
				DATE_FORMAT(creation, '%%Y-%%m') as month,
				SUM(paid_amount) as payments
			FROM `tabStudent Enrollment`
			WHERE creation >= DATE_SUB(NOW(), INTERVAL %s MONTH)
			AND docstatus != 2
			GROUP BY DATE_FORMAT(creation, '%%Y-%%m')
			ORDER BY month ASC
		""", (months,), as_dict=True)
		
		return {
			"status": "success",
			"data": {
				"revenue": revenue_data,
				"payments": payment_data
			}
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Revenue Chart Data Error")
		return {
			"status": "error",
			"message": str(e)
		}


@frappe.whitelist()
def get_course_popularity_data():
	"""
	Get course popularity data for charts
	"""
	try:
		course_data = frappe.db.sql("""
			SELECT 
				c.course_name,
				COUNT(se.name) as enrollment_count
			FROM `tabCourse` c
			LEFT JOIN `tabStudent Enrollment` se ON c.name = se.course
			WHERE se.docstatus != 2 OR se.docstatus IS NULL
			GROUP BY c.name, c.course_name
			ORDER BY enrollment_count DESC
			LIMIT 10
		""", as_dict=True)
		
		return {
			"status": "success",
			"data": course_data
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Course Popularity Data Error")
		return {
			"status": "error",
			"message": str(e)
		}
