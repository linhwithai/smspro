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
			"fieldname": "total_sessions",
			"label": _("Total Sessions"),
			"fieldtype": "Int",
			"width": 120
		},
		{
			"fieldname": "present_sessions",
			"label": _("Present"),
			"fieldtype": "Int",
			"width": 100
		},
		{
			"fieldname": "absent_sessions",
			"label": _("Absent"),
			"fieldtype": "Int",
			"width": 100
		},
		{
			"fieldname": "late_sessions",
			"label": _("Late"),
			"fieldtype": "Int",
			"width": 100
		},
		{
			"fieldname": "excused_sessions",
			"label": _("Excused"),
			"fieldtype": "Int",
			"width": 100
		},
		{
			"fieldname": "attendance_rate",
			"label": _("Attendance Rate %"),
			"fieldtype": "Percent",
			"width": 130
		}
	]


def get_data(filters):
	conditions = get_conditions(filters)
	
	# Get unique students with their attendance summary
	query = f"""
		SELECT 
			a.student,
			a.student_name,
			a.batch,
			a.batch_name,
			a.course,
			a.course_name,
			COUNT(a.name) as total_sessions,
			SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_sessions,
			SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_sessions,
			SUM(CASE WHEN a.status = 'Late' THEN 1 ELSE 0 END) as late_sessions,
			SUM(CASE WHEN a.status = 'Excused' THEN 1 ELSE 0 END) as excused_sessions,
			ROUND(
				(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / COUNT(a.name)) * 100, 2
			) as attendance_rate
		FROM `tabAttendance` a
		WHERE a.docstatus != 2
		{conditions}
		GROUP BY a.student, a.batch, a.course
		ORDER BY attendance_rate DESC, a.student_name
	"""
	
	return frappe.db.sql(query, as_dict=True)


def get_conditions(filters):
	conditions = ""
	
	if filters.get("student"):
		conditions += f" AND a.student = '{filters['student']}'"
	
	if filters.get("batch"):
		conditions += f" AND a.batch = '{filters['batch']}'"
	
	if filters.get("course"):
		conditions += f" AND a.course = '{filters['course']}'"
	
	if filters.get("from_date"):
		conditions += f" AND a.attendance_date >= '{filters['from_date']}'"
	
	if filters.get("to_date"):
		conditions += f" AND a.attendance_date <= '{filters['to_date']}'"
	
	if filters.get("min_attendance_rate"):
		conditions += f" AND ROUND((SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / COUNT(a.name)) * 100, 2) >= {filters['min_attendance_rate']}"
	
	return conditions


def get_chart_data(data):
	# Attendance Rate Distribution Chart
	attendance_ranges = {
		"90-100%": 0,
		"80-89%": 0,
		"70-79%": 0,
		"60-69%": 0,
		"Below 60%": 0
	}
	
	total_students = len(data)
	present_total = 0
	absent_total = 0
	
	for row in data:
		rate = row.get("attendance_rate", 0)
		
		if rate >= 90:
			attendance_ranges["90-100%"] += 1
		elif rate >= 80:
			attendance_ranges["80-89%"] += 1
		elif rate >= 70:
			attendance_ranges["70-79%"] += 1
		elif rate >= 60:
			attendance_ranges["60-69%"] += 1
		else:
			attendance_ranges["Below 60%"] += 1
		
		present_total += row.get("present_sessions", 0)
		absent_total += row.get("absent_sessions", 0)
	
	chart = {
		"data": {
			"labels": list(attendance_ranges.keys()),
			"datasets": [{
				"name": "Students",
				"values": list(attendance_ranges.values())
			}]
		},
		"type": "bar",
		"colors": ["#28a745", "#20c997", "#ffc107", "#fd7e14", "#dc3545"]
	}
	
	return chart
