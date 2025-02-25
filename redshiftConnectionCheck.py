import psycopg2

# Connection details
REDSHIFT_HOST = "redshift-cluster-1.c356cp9xhdy0.us-east-1.redshift.amazonaws.com"
REDSHIFT_PORT = 5432
REDSHIFT_USER = "awsadmin"
REDSHIFT_PASSWORD = "Admin_123"
REDSHIFT_DB = "dev-1"
# Connect to Redshift
try:
    conn = psycopg2.connect(
        host=REDSHIFT_HOST,
        port=REDSHIFT_PORT,
        dbname=REDSHIFT_DB,
        user=REDSHIFT_USER,
        password=REDSHIFT_PASSWORD
    )
    print("Connected to Redshift successfully!")
    conn.close()
except Exception as e:
    print("Error connecting to Redshift:", e)
