import mysql.connector

db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='ROHITH@2006',
    database='event_db'
)
cursor = db.cursor(dictionary=True)

# Show all bookings
cursor.execute('SELECT id, user_email, seats, status FROM bookings')
bookings = cursor.fetchall()
print('ALL BOOKINGS:')
print('=' * 60)
for b in bookings:
    print(f'ID: {b["id"]}, Status: {b["status"]}, Seats: {b["seats"]}')

# Show counts by status
print('\n' + '=' * 60)
print('COUNT BY STATUS:')
cursor.execute('''
    SELECT status, COUNT(*) as count FROM bookings GROUP BY status
''')
for row in cursor.fetchall():
    print(f'{row["status"].upper()}: {row["count"]}')

# Verify the exact query from admin_stats
print('\n' + '=' * 60)
print('ADMIN_STATS QUERY RESULT:')
cursor.execute('''
    SELECT 
        COUNT(*) AS total,
        COALESCE(SUM(status='approved'), 0) AS approved,
        COALESCE(SUM(status='pending'), 0) AS pending,
        COALESCE(SUM(status='rejected'), 0) AS rejected
    FROM bookings
''')
result = cursor.fetchone()
print(f'Total: {result["total"]}')
print(f'Approved: {result["approved"]}')
print(f'Pending: {result["pending"]}')
print(f'Rejected: {result["rejected"]}')

db.close()
