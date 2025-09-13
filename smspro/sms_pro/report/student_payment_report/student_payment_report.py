# Copyright (c) 2024, Mr Linh Vu and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	
	chart = get_chart_data(data)
	
	return columns, data, None, chart


def get_columns():
	return [
		{
			"fieldname": "student",
			"label": _("Student"),
			"fieldtype": "Link",
			"options": "Student",
			"width": 150
		},
		{
			"fieldname": "student_name",
			"label": _("Student Name"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "course",
			"label": _("Course"),
			"fieldtype": "Link",
			"options": "Course",
			"width": 120
		},
		{
			"fieldname": "course_name",
			"label": _("Course Name"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "batch",
			"label": _("Batch"),
			"fieldtype": "Link",
			"options": "Batch",
			"width": 120
		},
		{
			"fieldname": "batch_name",
			"label": _("Batch Name"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "enrollment_date",
			"label": _("Enrollment Date"),
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "total_fee",
			"label": _("Total Fee"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "paid_amount",
			"label": _("Paid Amount"),
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "outstanding_amount",
			"label": _("Outstanding Amount"),
			"fieldtype": "Currency",
			"width": 130
		},
		{
			"fieldname": "payment_status",
			"label": _("Payment Status"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "last_payment_date",
			"label": _("Last Payment Date"),
			"fieldtype": "Date",
			"width": 130
		}
	]


def get_data(filters):
	conditions = get_conditions(filters)
	
	query = f"""
		SELECT 
			se.student,
			se.student_name,
			se.course,
			se.course_name,
			se.batch,
			se.batch_name,
			se.enrollment_date,
			se.total_fee,
			se.paid_amount,
			se.outstanding_amount,
			se.payment_status,
			se.last_payment_date
		FROM `tabStudent Enrollment` se
		WHERE se.docstatus != 2
		{conditions}
		ORDER BY se.enrollment_date DESC
	"""
	
	return frappe.db.sql(query, as_dict=True)


def get_conditions(filters):
	conditions = ""
	
	if filters.get("student"):
		conditions += f" AND se.student = '{filters['student']}'"
	
	if filters.get("course"):
		conditions += f" AND se.course = '{filters['course']}'"
	
	if filters.get("batch"):
		conditions += f" AND se.batch = '{filters['batch']}'"
	
	if filters.get("payment_status"):
		conditions += f" AND se.payment_status = '{filters['payment_status']}'"
	
	if filters.get("from_date"):
		conditions += f" AND se.enrollment_date >= '{filters['from_date']}'"
	
	if filters.get("to_date"):
		conditions += f" AND se.enrollment_date <= '{filters['to_date']}'"
	
	if filters.get("outstanding_only"):
		conditions += " AND se.outstanding_amount > 0"
	
	return conditions


def get_chart_data(data):
	# Payment Status Chart
	payment_status_count = {}
	total_outstanding = 0
	total_paid = 0
	
	for row in data:
		status = row.get("payment_status", "Unknown")
		payment_status_count[status] = payment_status_count.get(status, 0) + 1
		
		total_outstanding += row.get("outstanding_amount", 0)
		total_paid += row.get("paid_amount", 0)
	
	chart = {
		"data": {
			"labels": list(payment_status_count.keys()),
			"datasets": [{
				"name": "Payment Status",
				"values": list(payment_status_count.values())
			}]
		},
		"type": "pie",
		"colors": ["#28a745", "#ffc107", "#dc3545"]
	}
	
	return chart
