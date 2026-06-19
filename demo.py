import psycopg2
import pandas as pd
import streamlit as st
from datetime import date


def get_connection():
    return psycopg2.connect(
    host="localhost",
    database="salesmanagament",
    user="postgres",
    password="12345"
)




def validate_login(username, password):
 conn = get_connection()
 cur = conn.cursor()
 cur.execute("""
        SELECT u.user_id,
               u.username,
               u.branch_id,
               b.branch_name,
               u.usr_password,
               u.usr_role
              FROM users u
            LEFT JOIN branches b
            ON u.branch_id = b.branch_id
        WHERE username=%s
        AND usr_password=%s
    """,(username,password))
 user = cur.fetchone()
 cur.close()
 conn.close()

 return user


def insert_sale(branch_id, doj, customer_name, mobile_number, product_name, gross_sales):
    conn = get_connection()
    cur = conn.cursor()

    query = """
    INSERT INTO customer_sales
    (branch_id, doj, cus_name, mobile_number, product_name, gross_sales,sales_status)
    VALUES (%s, %s, %s, %s, %s, %s,'open')
    """

    cur.execute(
        query,
        (branch_id, doj, customer_name, mobile_number, product_name, gross_sales)
    )

    conn.commit()
    cur.close()
    conn.close()


def insert_payment(sale_id,payment_date,payment_method,amount_paid):
    conn = get_connection()
    cur = conn.cursor()
    query = """
    INSERT INTO payment_splits
    (sale_id,payment_date,payment_method,amount_paid)
    VALUES (%s, %s, %s, %s)
    """

    cur.execute(
        query,
        (sale_id,payment_date,payment_method,amount_paid)
    )

    conn.commit()
    cur.close()
    conn.close()

def get_branches():
    conn = get_connection()
    query = """
        SELECT branch_id, branch_name
        FROM branches
        ORDER BY branch_name
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def get_sales_data(role, branch_id=None):

    conn = get_connection()
        

    

    if role == "Super Admin":

        query = """
        SELECT
    cs.sale_id,
    b.branch_name,
    cs.doj,
    cs.cus_name,
    cs.product_name,
    cs.gross_sales,
    cs.received_amount,
    cs.pending_amount,
    cs.sales_status
    FROM customer_sales cs
    JOIN branches b
    ON cs.branch_id = b.branch_id
        ORDER BY cs.doj DESC
        """

        df = pd.read_sql(query, conn)

        
    else:

        query = """
        
    SELECT
    cs.sale_id,
    b.branch_name,
    cs.doj,
    cs.cus_name,
    cs.product_name,
    cs.gross_sales,
    cs.received_amount,
    cs.pending_amount,
    cs.sales_status
    FROM customer_sales cs
    JOIN branches b
    ON cs.branch_id = b.branch_id
       
      WHERE cs.branch_id=%s
        ORDER BY cs.doj DESC
        """

        df = pd.read_sql(
            query,
            conn,
            params=(branch_id,)
        )
    conn.commit()
    conn.close()
    return df 
   
if "logged_in" not in st.session_state:
     st.session_state.logged_in = False




if not st.session_state.logged_in:
 st.set_page_config(layout="centered")
 st.title(" Sales Dashboard login Page")
 username = st.text_input("Username")
 password = st.text_input("Password", type="password")
 login = st.button("Login",type="primary")

 if login:
        user = validate_login(username,password)

        if user:

            st.session_state.logged_in = True
            st.session_state.user_id = user[0]
            st.session_state.username = user[1]
            st.session_state.branch_id = user[2]
            st.session_state.branch_name=user[3]
            st.session_state.usr_role = user[5]

            st.success("Login Successful")
            st.balloons()
                      

        else:
            st.error("Invalid Username or Password")


else:
   
    
    st.sidebar.title("**Navigation**")
    st.sidebar.subheader("GO TO")
    

    page = st.sidebar.radio(
        "",
        [
            "📊 Dashboard & Reports",
            "➕ Data Entry Workspace",
            "📝 Advanced SQL Engine"
        ]
         )
    
    st.sidebar.markdown("---")

    st.sidebar.write(f"👤 User: **{st.session_state.username}**")
    st.sidebar.write(f"🔑 Role: **{st.session_state.usr_role}**")
    if st.session_state.usr_role=="Admin":
       st.info(
        f"Assigned Branch : {st.session_state.branch_name}"
    )
    

    if st.sidebar.button("Logout"):
     st.session_state.clear()
     st.rerun()

    st.markdown("""
    <style>
    .stApp {
    background: linear-gradient(
    135deg,
    #f5f7fa 0%,
    #c3cfe2 100%
    );
    }
    </style>
    """, unsafe_allow_html=True) 
    
    if page=="📊 Dashboard & Reports":

        role = st.session_state.usr_role
        branch_id = st.session_state.branch_id
       




        
        sales_df = get_sales_data(
        role,
        branch_id
        )
                
        st.title("🏢Sales Intelligence Hub",text_alignment="center")
        

        st.subheader("🔍 Filters")

        col1, col2, col3, col4 = st.columns(4)

        if role == "Super Admin":

         branch_options = ["All"] + sorted(
         sales_df["branch_name"].dropna().unique()
         )

         selected_branch = col1.selectbox(
        "Branch",
         branch_options
         )

        
         product_options = ["All"] + sorted(
          sales_df["product_name"].dropna().unique()
          )
        

         selected_product = col2.selectbox(
        "Product",
         product_options
         )

         start_date = col3.date_input(
         "Start Date",
        sales_df["doj"].min()
        )

         end_date = col4.date_input(
        "End Date",
        date.today()
        )
        else:
            col1, col2, col3 = st.columns(3)

           #  Product Filter


            product_options = ["All"] + sorted(
            sales_df["product_name"].dropna().unique()
            )

            selected_product = col1.selectbox(
            "Product Name",
            product_options
            )

            start_date = col2.date_input(
            "Start Date",
            sales_df["doj"].min()
            )

            end_date = col3.date_input(
            "End Date",
            date.today()
            )
            
            selected_branch = st.session_state.branch_name


    #Filters:
        filtered_df = sales_df.copy()

        if role == "Super Admin":

         if selected_branch != "All":
          filtered_df = filtered_df[
          filtered_df["branch_name"] == selected_branch
          ]

        if selected_product != "All":
          filtered_df = filtered_df[
          filtered_df["product_name"] == selected_product
         ]
          

        filtered_df = filtered_df[
         (pd.to_datetime(filtered_df["doj"]).dt.date >= start_date)
    &
         (pd.to_datetime(filtered_df["doj"]).dt.date <= end_date)
         ]

        overall_revenue = filtered_df["gross_sales"].sum()

        received_amount = filtered_df[
         "received_amount"
         ].sum()

        pending_amount = filtered_df[
         "pending_amount"
         ].sum()

        pending_percent = (
         (pending_amount / overall_revenue) * 100
         if overall_revenue > 0 else 0
         )
        
        #KPI Metrics:

        st.subheader("📈 Key Metrics")

        st.markdown("""
        <style>
        [data-testid="stMetricValue"] {
        font-size: 18px !important;
        }
        </style>
         """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
         label="Overall Revenue",
         value=f"₹ {overall_revenue:,.2f}",
         border=True
         
         )

        c2.metric(
        "Received Amount",
        f"₹ {received_amount:,.2f}",
         border=True
         )

        c3.metric(
        "Pending Amount",
        f"₹ {pending_amount:,.2f}",
        border=True
         )

        c4.metric(
        "Pending Collection %",
        f"{pending_percent:.2f}%",
        border=True
         )        


        st.subheader("Sales Report")

        st.dataframe(
        filtered_df,
        use_container_width=True
         )
        
        
        st.metric(
            "Total Records",
            len(filtered_df)
        )






    if page=="➕ Data Entry Workspace":
      role = st.session_state.usr_role
      branch_id = st.session_state.branch_id
      branch_name=st.session_state.branch_name
        
      
       
      st.title("📑 Operations Record Creator",text_alignment="center")
    #   st.switch_page("pages/new_sale.py")
      tab1, tab2 = st.tabs(
      [
        "Add New Sales Entry",
        "Log Payment Split Details"
      ]
      )

      with tab1:

    #    
       st.title("Customer Sales Entry")

    #    branch_id = st.number_input("Branch ID", min_value=1)

       branches_df = get_branches()

       if role=="Super Admin":
        selected_branch = st.selectbox(
       "Branch Name",
        branches_df["branch_name"]
       )

        branch_id = branches_df.loc[
        branches_df["branch_name"] == selected_branch,
       "branch_id"
       ] .iloc[0]
       
       if role=="Admin":

        st.text_input(
        "Branch Name",
        value=st.session_state.branch_name,
        disabled=True
       )

        branch_id = st.session_state.branch_id
          
       

       doj = st.date_input(
      "Sale Date",
       value=date.today()
    )

       customer_name = st.text_input("Customer Name")

       mobile_number = st.text_input("Mobile Number")

       product_name = st.text_input("Product Name")

       gross_sales = st.number_input(
      "Gross Sales",
       min_value=0.0,
       step=100.0
    )

       if st.button("Save Sale",type="primary"):

         if customer_name and mobile_number and product_name:

          insert_sale(
            branch_id,
            doj,
            customer_name,
            mobile_number,
            product_name,
            gross_sales
        )

         st.success("Sale Added Successfully!")
      

     
       else:
        st.error("Please fill all fields.")


      with tab2:
          st.title("💳 Payment Split")
          sale_df = pd.read_sql(
          """
          SELECT sale_id
          FROM customer_sales
          ORDER BY sale_id DESC
          """,
          get_connection()
          )

          sale_id = st.selectbox(
          "Select Sale",
           sale_df["sale_id"]
           )



          payment_date = st.date_input(
          "Payment Date",
          value=date.today()
)

          payment_method = st.selectbox(
          "Payment Method",
          ["Cash","UPI","Card"]
          )


          amount_paid = st.number_input(
          "Amount Paid",
           min_value=0.0
          )

          if st.button("Add Payment",type="primary"):
           if amount_paid>0:
       

            insert_payment(
           sale_id,
           payment_date,
           payment_method,
           amount_paid

        )
            st.success("Payment Successfull")

          

           else:
            st.error("Please Fill All The Fields.")
    



    if page=="📝 Advanced SQL Engine":
        st.title("📊 Live SQL Business Analytics Engine",text_alignment="center")

        st.caption(
        "Select and execute one of the mandatory verification queries "
        "to audit records from your tables."
    )

        st.markdown("### Choose Targeted Predefined Operational Query")

        role = st.session_state.usr_role         
        branch_id = st.session_state.branch_id  

        if st.session_state.usr_role == "Super Admin":

         query_options = {

        "1. Retrieve all records from customer_sales table":
        """
        SELECT *
        FROM customer_sales
        ORDER BY sale_id DESC
        """,

        "2. Retrieve all records from branches table":
        """
        SELECT *
        FROM branches
        ORDER BY branch_id
        """,

        "3. Retrieve all records from payment_splits table":
        """
        SELECT *
        FROM payment_splits
        ORDER BY payment_id DESC
        """,

        "4. Retrieve all sales belonging to Chennai branch":
        """
        SELECT cs.*
        FROM customer_sales cs
        JOIN branches b
        ON cs.branch_id = b.branch_id
        WHERE b.branch_name = 'Chennai'
        """,

        "5. Calculate the total gross sales across all branches":
        """
        SELECT
        COALESCE(SUM(gross_sales), 0) AS total_gross_sales
        FROM customer_sales
        """,

        "6. Calculate the total received amount across all sales":
        """
        SELECT
        COALESCE(SUM(received_amount), 0) AS total_received_amount
        FROM customer_sales
        """,
 
       "7. Count the Total Number of Sales Per Branch":
        """
        SELECT
        b.branch_name,
        COUNT(cs.sale_id) AS total_sales
        FROM branches b
        LEFT JOIN customer_sales cs
        ON b.branch_id = cs.branch_id
        GROUP BY b.branch_name
        ORDER BY total_sales DESC
        """,


        "8. Find the Average Gross Sales Amount":
        """
        SELECT
        ROUND(AVG(gross_sales),2) AS average_gross_sales
        FROM customer_sales
        """,


       "9. Retrieve Sales Details Along With the Branch Name":
        """
        SELECT
        cs.sale_id,
        cs.doj ,
        cs.cus_name,
        cs.product_name,
        cs.gross_sales,
        cs.received_amount,
        cs.pending_amount,
        b.branch_name
        FROM customer_sales cs
        INNER JOIN branches b
        ON cs.branch_id = b.branch_id
        ORDER BY cs.sale_id DESC
        """,

        "10. Retrieve Sales Details Along With Total Payment Received Using payment_splits.":
        """
        SELECT
        cs.sale_id,
        cs.cus_name,
        cs.product_name,
        cs.gross_sales,
        COALESCE(SUM(ps.amount_paid),0) AS total_payment_received
        FROM customer_sales cs
        LEFT JOIN payment_splits ps
        ON cs.sale_id = ps.sale_id
        GROUP BY
        cs.sale_id,
        cs.cus_name,
        cs.product_name,
        cs.gross_sales
        ORDER BY cs.sale_id DESC
        """,


        "11. Show Branch-wise Total Gross Sales Using JOIN + GROUP BY":
        """
        SELECT
        b.branch_name,
        COUNT(cs.sale_id) AS total_sales,
        SUM(cs.gross_sales) AS total_gross_sales
        FROM branches b
        LEFT JOIN customer_sales cs
        ON b.branch_id = cs.branch_id
        GROUP BY
        b.branch_name
        ORDER BY total_gross_sales DESC
        """,


        "12. Retrieve Sales Along With Branch Admin Name":
        """
        SELECT
        cs.sale_id,
        cs.cus_name,
        cs.product_name,
        cs.gross_sales,
        b.branch_name,
        u.username AS admin_name
        FROM customer_sales cs
        INNER JOIN branches b
        ON cs.branch_id = b.branch_id
        INNER JOIN users u
        ON b.branch_id = u.branch_id
        WHERE u.usr_role = 'Admin'
        ORDER BY cs.sale_id DESC
        """,

        "13. Find Sales Where the Pending Amount is Greater Than 5000":
        """
        SELECT
        sale_id,
        doj,
        cus_name,
        product_name,
        gross_sales,
        received_amount,
        pending_amount
        FROM customer_sales
        WHERE pending_amount > 5000
        ORDER BY pending_amount DESC
        """,

        "14. Retrieve Top 3 Highest Gross Sales":
        """
        SELECT
        sale_id,
        cus_name,
        product_name,
        gross_sales,
        doj
        FROM customer_sales
        ORDER BY gross_sales DESC
        LIMIT 3
        """,

        "15. Calculate Payment Method-wise Total Collection (Cash / UPI / Card)":
        """
        SELECT
        payment_method,
        SUM(amount_paid) AS total_collection
        FROM payment_splits
        GROUP BY payment_method
        ORDER BY total_collection DESC
        """


    }
    

        if st.session_state.usr_role == "Admin":
        
        
         query_options = {

        "1. View My Branch Sales":
        f"""
        SELECT *
        FROM customer_sales
        WHERE branch_id = {branch_id}
        ORDER BY sale_id DESC
        """,

        "2. View My Branch Details":
        f"""
        SELECT *
        FROM branches
        WHERE branch_id = {branch_id}
        """,

        "3. View My Branch Payment Splits":
        f"""
        SELECT ps.*
        FROM payment_splits ps
        JOIN customer_sales cs
        ON ps.sale_id = cs.sale_id
        WHERE cs.branch_id = {branch_id}
        ORDER BY ps.payment_id DESC
        """,

        "4. View Pending Payments":
        f"""
        SELECT *
        FROM customer_sales
        WHERE branch_id = {branch_id}
        AND pending_amount > 0
        ORDER BY pending_amount DESC
        """,

        "5. Calculate the Total Gross Sales Across All Branches":
        f"""
        SELECT
        COALESCE(SUM(gross_sales), 0) AS total_gross_sales
        FROM customer_sales
        WHERE branch_id = {branch_id}
        """,


        "6. Calculate the Total Received Amount Across All Sales":
        f"""
        SELECT
        COALESCE(SUM(received_amount), 0) AS total_received_amount
        FROM customer_sales
        WHERE branch_id = {branch_id}
        """,


        "7.Count the Total Number of Sales Per Branch":
        f"""
        SELECT
        COUNT(*) AS total_sales
        FROM customer_sales
        WHERE branch_id = {branch_id}
        """,


        "8.Find the Average Gross Sales Amount":
        f"""
        SELECT
        ROUND(AVG(gross_sales),2) AS average_gross_sales
        FROM customer_sales
        WHERE branch_id = {branch_id}
        """,

        "9.Retrieve Sales Details Along With the Branch Name":
        f"""
        SELECT
        cs.sale_id,
        cs.doj,
        cs.cus_name,
        cs.product_name,
        cs.gross_sales,
        cs.received_amount,
        cs.pending_amount,
        b.branch_name
        FROM customer_sales cs
        INNER JOIN branches b
        ON cs.branch_id = b.branch_id
        WHERE cs.branch_id = {branch_id}
        ORDER BY cs.sale_id DESC
        """,

        "10. Retrieve Sales Details Along With Total Payment Received Using payment_splits":
        f"""
        SELECT
        cs.sale_id,
        cs.cus_name,
        cs.product_name,
        cs.gross_sales,
        COALESCE(SUM(ps.amount_paid),0) AS total_payment_received
        FROM customer_sales cs
        LEFT JOIN payment_splits ps
        ON cs.sale_id = ps.sale_id
        WHERE cs.branch_id = {branch_id}
        GROUP BY
        cs.sale_id,
        cs.cus_name,
        cs.product_name,
        cs.gross_sales
        ORDER BY cs.sale_id DESC
        """,

        "11. Show Branch-wise Total Gross Sales":
        f"""
        SELECT
        b.branch_name,
        COUNT(cs.sale_id) AS total_sales,
        SUM(cs.gross_sales) AS total_gross_sales
        FROM branches b
        INNER JOIN customer_sales cs
        ON b.branch_id = cs.branch_id
        WHERE b.branch_id = {branch_id}
        GROUP BY
        b.branch_name
        """,

        "12. Retrieve Sales Along With Branch Admin Name":
        f"""
        SELECT
        cs.sale_id,
        cs.cus_name,
        cs.product_name,
        cs.gross_sales,
        b.branch_name,
        u.username AS admin_name
        FROM customer_sales cs
        INNER JOIN branches b
        ON cs.branch_id = b.branch_id
        INNER JOIN users u
        ON b.branch_id = u.branch_id
        WHERE u.usr_role = 'Admin'
        AND cs.branch_id = {branch_id}
        ORDER BY cs.sale_id DESC
        """,

        "13. Find Sales Where the Pending Amount is Greater Than 5000":
        f"""
        SELECT
        sale_id,
        doj,
        cus_name,
        product_name,
        gross_sales,
        received_amount,
        pending_amount
        FROM customer_sales
        WHERE branch_id = {branch_id}
        AND pending_amount > 5000
        ORDER BY pending_amount DESC
        """,

        "14. Retrieve Top 3 Highest Gross Sales":
        f"""
        SELECT
        sale_id,
        cus_name,
        product_name,
        gross_sales,
        doj
        FROM customer_sales
        WHERE branch_id = {branch_id}
        ORDER BY gross_sales DESC
        LIMIT 3
        """,

        "15. Calculate Payment Method-wise Total Collection (Cash / UPI / Card)":
        f"""
        SELECT
        ps.payment_method,
        SUM(ps.amount_paid) AS total_collection
        FROM payment_splits ps
        INNER JOIN customer_sales cs
        ON ps.sale_id = cs.sale_id
        WHERE cs.branch_id = {branch_id}
        GROUP BY ps.payment_method
        ORDER BY total_collection DESC
        """


    }
    
        selected_query = st.selectbox(
        "**Choose query**",
        list(query_options.keys())
     )

        sql_query = query_options[selected_query]

        st.code(sql_query, language="sql")

        if st.button("Execute Live Database Transaction",type="primary"):

         conn = get_connection()

         df = pd.read_sql(sql_query, conn)

         conn.close()

         st.success("Query Executed Successfully")

         st.dataframe(
            df,
            use_container_width=True
        )

         st.metric(
            "Total Records",
            len(df)
        )

 



    
  


  

    


   
