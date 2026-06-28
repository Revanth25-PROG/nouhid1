from flask import Flask, render_template, request, redirect, url_for, session, flash
from supabase import create_client, Client
from datetime import date

app = Flask(__name__)
app.secret_key = 'super_secret_key'

import os
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://dwunumnikuafvlgcgrnw.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Initialize Supabase client
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Error initializing Supabase client: {e}")
    supabase = None

@app.route('/')
def index():
    return render_template('admin.html')

@app.route('/adminlogin', methods=['POST'])
def adminlogin():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if supabase:
        try:
            response = supabase.table('admins').select("*").eq('username', username).eq('password', password).execute()
            admin = response.data
            
            if admin:
                session['admin_logged_in'] = True
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid username or password.")
        except Exception as e:
            flash(f"Supabase query error: {e}")
    else:
        flash("Supabase client is not configured. Please enter your URL and KEY in app.py.")
    
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('index'))
        
    present_count = 0
    absent_count = 0
    total_count = 0
    
    if supabase:
        try:
            today_str = date.today().isoformat()
            
            res_present = supabase.table('attendance').select('*', count='exact').eq('status', 'Present').eq('date', today_str).execute()
            present_count = res_present.count if res_present.count is not None else len(res_present.data)
            
            res_absent = supabase.table('attendance').select('*', count='exact').eq('status', 'Absent').eq('date', today_str).execute()
            absent_count = res_absent.count if res_absent.count is not None else len(res_absent.data)
            
            res_total = supabase.table('students').select('*', count='exact').execute()
            total_count = 72
        except Exception as e:
            print(f"Error fetching counts: {e}")
            
    return render_template('dashboard.html', present=present_count, absent=abs(present_count-total_count-absent_count), total=total_count)

@app.route('/attendance')
def attendance():
    if not session.get('admin_logged_in'):
        return redirect(url_for('index'))
        
    present_count = 0
    absent_count = 0
    total_count = 0
    
    if supabase:
        try:
            today_str = date.today().isoformat()
            
            res_present = supabase.table('attendance').select('*', count='exact').eq('status', 'Present').eq('date', today_str).execute()
            present_count = res_present.count if res_present.count is not None else len(res_present.data)
            
            res_absent = supabase.table('attendance').select('*', count='exact').eq('status', 'Absent').eq('date', today_str).execute()
            absent_count = res_absent.count if res_absent.count is not None else len(res_absent.data)
            
            res_total = supabase.table('students').select('*', count='exact').execute()
            total_count = res_total.count if res_total.count is not None else len(res_total.data)
        except Exception as e:
            print(f"Error fetching counts: {e}")
            
    return render_template('atten.html', present=present_count, absent=absent_count, total=total_count)

@app.route('/present')
def present_students():
    if not session.get('admin_logged_in'):
        return redirect(url_for('index'))
        
    prestu = []
    
    if supabase:
        try:
            today_str = date.today().isoformat()
            # Fetch attendance and join with students using Supabase foreign key relationship
            res = supabase.table('attendance').select('status, date, students(id, name, roll_no)').eq('status', 'Present').eq('date', today_str).execute()
            
            # Extract student data from the nested relationship
            for item in res.data:
                if item.get('students'):
                    prestu.append(item['students'])
        except Exception as e:
            print(f"Error fetching present students: {e}")
            
    return render_template('present.html', prestu=prestu)

@app.route('/absent')
def absent_students():
    if not session.get('admin_logged_in'):
        return redirect(url_for('index'))
        
    students = []
    
    if supabase:
        try:
            today_str = date.today().isoformat()
            # Fetch attendance and join with students using Supabase foreign key relationship
            res = supabase.table('attendance').select('status, date, students(id, name, roll_no)').eq('status', 'Absent').eq('date', today_str).execute()
            
            # Extract student data from the nested relationship
            for item in res.data:
                if item.get('students'):
                    students.append(item['students'])
        except Exception as e:
            print(f"Error fetching absent students: {e}")
            
    return render_template('absent.html', student=students)

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
