from flask import Flask, jsonify, request, flash,session, json
from connect2db import *
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import datetime
import re
from psycopg2.extras import RealDictCursor
from flask_cors import CORS, cross_origin
from datetime import date
# from urllib3 import request
from datetime import timedelta

date_today = date.today()
date_time = datetime.datetime.now()
d = datetime.datetime.strptime('2011-06-09', '%Y-%m-%d')
my_datetime_utc = date_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')

base = connectDB()
base.autocommit = True
cursor = base.cursor()
cur = base.cursor()
app = Flask(__name__)
key = Fernet.generate_key()
f = Fernet(key)

CORS(app)
app.config['SECRET_KEY'] = 'this is a secret key'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)

@app.route('/change_password', methods=['PUT'])
def change_password():
        old_password = request.json.get('Old_Password')
        new_password = request.json.get('New_Password')
        id = request.json.get('User_Id')
        #print(id)
        cur.execute('SELECT * FROM users where user_id=%s', [id])
        res = cur.fetchall()
        #print(res)
        l = []
        for i in res:
            for j in i:
                l.append(j)
        #print(l[2])
        stored_password = l[2]
        result = check_password_hash(stored_password, old_password)
        if result == True:
            hashed_password = generate_password_hash(new_password)
            cur.execute('update  users SET password =%s where user_id = %s', (hashed_password, id))
            return jsonify({"Status": "200", "Message": "Password updated"})
        else:
            resp = jsonify({"Status": "202", "Message": "Unauthorized Password"})
            resp.status_code = 202
            return resp
@app.route('/ResetPassword', methods=['PUT'])
def  Reset_password():
        User_Id= request.json.get('User_Id')
        Password = request.json.get('Password')
        cur.execute('SELECT * FROM users where user_id=%s', [User_Id])
        res = cur.fetchall()
        if len(res)!=0:
           hashed_password = generate_password_hash(Password)
           cur.execute('update  users SET password =%s where user_id = %s', (hashed_password, User_Id))
           return jsonify({"Message":"Password Reset successfully!","Status Code":"200 OK"})

        else:
           resp = jsonify({"Message":"User doesn't exist ","Status Code":"202 BadRequest"})
           resp.status_code = 202
           return resp

@app.route('/dashboard1', methods=['GET'])
def Server_piechart():
    conn = connectDB()
    cursor = conn.cursor()  # created a cursor
    cursor.execute('select asset_id from asset')
    res = cursor.fetchall()
    count = 0
    for i in res:
        count += 1
    total_servers = count
    cursor.execute('SELECT * FROM asset where reserved=%s and status=%s', [False,False])
    res1 = cursor.fetchall()
    pool = len(res1)
    cursor.execute('SELECT * FROM asset where reserved=%s and status=%s', [True,True])
    res2 = cursor.fetchall()
    servers = len(res2)
    return jsonify({"Message": "Updated Statistics","Status": "200 OK", "reserved": servers,"vacant": pool})

@app.route('/dashboard2', methods=['GET'])
def cluster_piechart():
    cur = connectDB()
    cur = cur.cursor()
    cur.execute(
      " SELECT cluster_id, COUNT(CASE WHEN reserved='t' THEN 1 ELSE NULL END)AS reserved,  COUNT(CASE WHEN reserved='f' or reserved is null THEN 1 ELSE NULL END)AS vacant FROM asset group by cluster_id")
    res = cur.fetchall()
    b = []
    for i in res:
      b.append({"cluster_id": i[0], "Reserved": i[1], "Vacant": i[2]})
    b.append({"Message": "Updated Statistics", "Status": "200 OK"})
    return jsonify({"Dashboard": b})

@app.route('/dashboard3', methods=['GET'])
def location_piechart():
    cur = connectDB()
    cur = cur.cursor()
    cur.execute(" SELECT asset_location, COUNT(CASE WHEN reserved='True' and status='True' THEN 1 ELSE NULL END)AS reserved,  COUNT(CASE WHEN reserved='false' and status='false' or reserved is null THEN 1 ELSE NULL END)AS vacant FROM asset group by asset_location")
    res = cur.fetchall()
    b=[]
    for i in res:
        b.append({"Location":i[0] , "Reserved":i[1] , "Vacant": i[2]})
    b.append({"Message":"Updated Statistics","Status":"200 OK"})
    return jsonify({"Dashboard":b})

@app.route("/dashboard4", methods=['POST'])
def dash_loc():
    """dashboard 4 api: showing statistics of a specific location"""
    try:
        cursorr = base.cursor()
        cursorr.execute("select asset_location from asset")
        resultt = cursorr.fetchall()
        location = request.json.get("Asset_location")
        for i in resultt:
            if location in i:
                cursor = base.cursor()
                cursor1 = base.cursor()
                cursor.execute("select asset_id from asset where reserved=true and status=true and asset_location=%s", [location])
                cursor1.execute("select asset_id from asset where reserved=false and status=false  and asset_location=%s", [location])
                res = cursor.fetchall()
                res1 = cursor1.fetchall()
                return jsonify(
                    {"Location": location, "Reserved": len(res), "Vacant": len(res1), "Message": "Updated Statistics",
                     "Status Code": "200"})
        else:
            resp = jsonify({"Message": "Check location!!", "Status Code": "202 Bad Request"})
            resp.status_code = 202
            return resp
    except Exception as e:
        print(e)
        return jsonify({"Message": "Exception occurred!", "Status Code": "202"})



@app.route('/dashboard5', methods=['GET'])
def server_sorted():
    try:
        conn = connectDB()
        cursor = conn.cursor()
        conn.autocommit = True

        if request.method == 'GET':

            cursor.execute("(SELECT  DISTINCT '6 Months' AS time,(SELECT COUNT(*) FROM asset WHERE reserved='t' AND "
                           "EXTRACT(DAY FROM NOW() - assigned_from)<=182) AS no_of_reserved, (SELECT COUNT(*) FROM asset "
                           "WHERE reserved='f' AND EXTRACT(DAY FROM NOW() - assigned_from)<=182) AS no_of_vacant FROM asset"
                           " WHERE EXTRACT(DAY FROM NOW() - assigned_from)<=182) UNION (SELECT DISTINCT '1 Year' AS time,"
                           "(SELECT COUNT(*) FROM asset WHERE reserved='t' AND (EXTRACT(DAY FROM NOW() - assigned_from)> 182 AND"
                           " EXTRACT(DAY FROM NOW() - assigned_from)<=365)) AS no_of_reserved, (SELECT COUNT(*) FROM asset WHERE"
                           " reserved='f' AND (EXTRACT(DAY FROM NOW() - assigned_from)> 182 AND EXTRACT(DAY FROM NOW() - assigned_from)<=365))"
                           " AS no_of_vacant FROM asset WHERE (EXTRACT(DAY FROM NOW() - assigned_from)> 182 AND"
                           " EXTRACT(DAY FROM NOW() - assigned_from)<=365)) UNION (SELECT DISTINCT '1.5 Year' AS time,(SELECT COUNT(*) FROM "
                           "asset WHERE reserved='t' AND (EXTRACT(DAY FROM NOW() - assigned_from)> 365 AND EXTRACT(DAY FROM NOW() - assigned_from)<=574))"
                           " AS no_of_reserved, (SELECT COUNT(*) FROM asset WHERE reserved='f' AND (EXTRACT(DAY FROM NOW() - assigned_from)> 365 AND"
                           " EXTRACT(DAY FROM NOW() - assigned_from)<=574)) AS no_of_vacant FROM asset WHERE (EXTRACT(DAY FROM NOW() - assigned_from)> 365"
                           " AND EXTRACT(DAY FROM NOW() - assigned_from)<=574)) UNION (SELECT DISTINCT '2 Years' AS time,(SELECT COUNT(*) FROM"
                           " asset WHERE reserved='t' AND (EXTRACT(DAY FROM NOW() - assigned_from)>574)) AS no_of_reserved, (SELECT COUNT(*) FROM asset WHERE "
                           "reserved='f' AND (EXTRACT(DAY FROM NOW() - assigned_from)>574)) AS no_of_vacant FROM asset WHERE "
                           "(EXTRACT(DAY FROM NOW() - assigned_from)>574));")

            c = cursor.fetchall()
            dashboard = []
            print(c, "ccccccccccccccccc")
            for i in c:
                lst = list(i)
                dashboard.append({"Timeline": lst[0], "Reserved": lst[1], "Vacant": lst[2]})
            print(dashboard)
        return jsonify({"Dashboard": dashboard, "Message": "Updated Statistics", "Status": "200 OK"})

    except Exception as e:
        print(e)
    finally:
        cursor.close()
"""ADMIN"""


""" Creating new users """


@cross_origin()
@app.route('/create_user', methods=['POST'])
def create_User():
    try:
        conn = connectDB()
        cursor = conn.cursor()  # created a cursor
        cursor.execute("select User_Id from Users")  # [(1,),(2,)]
        res1 = cursor.fetchall()
        Id_alr = len(res1)
        User_Id = Id_alr + 1

        _json = request.json  # converting to json
        # User_Id = _json['User_Id']
        # print(User_Id, "User_Id")
        Email_Id = _json['Email_Id']
        print(Email_Id, "Email_Id")
        Password = _json['Password']
        print(Password, "PASSSWORD")
        First_Name = _json['First_Name']
        print(First_Name, "First_Name")
        Last_Name = _json['Last_Name']
        print(Last_Name, "Last_Name")
        Created_on = date_today
        print(Created_on, "Created_on")
        Created_by = _json['Created_by']
        print(Created_by, "Created_by")
        # Updated_on = date_today
        # print(Updated_on, "Updated_on")
        # Updated_by = _json['Updated_by']
        # print(Updated_by, "Updated_by")
        Role = _json['Role']
        print(Role, "Role")
        Teams = _json['Teams']
        print(Teams, "Teams")
        # Delete = _json['Delete']
        Delete = "0"
        # delete = dele.encode()
        print(Delete, "deletee", Delete)

        # validate the received values
        if User_Id and Email_Id and Password and First_Name and Last_Name and \
                Created_on and Created_by  and Role and Teams and Delete and request.method == 'POST':  # giving condition whether the method is post
            _hashed_password = generate_password_hash(
                Password)  # using an inbuilt function generate_password_hash the password is hashing
            # save edits



            query1 = ("SELECT User_Id FROM Users ")  # qurey for selecting userid id from the usertable
            print(query1, "q1111")
            cursor.execute(query1)  # executing the qurey
            db224 = cursor.fetchall()  # fetching the qurey
            print(db224, "db224")
            usrid = []  # created an empty list for adding the user ids
            for i in db224:  # iterating the fetched values
                for j in i:  # iterating the tuples
                    print(usrid, "useridd")
                    usrid.append(j)  # appending the values in to the list
                print(usrid, "idddddd")

            if User_Id in usrid:  # checking the user id is present in the list
                resp = jsonify({"Message": "Userid is already exists!",
                                "Status": "202 Bad Request"})  # if the userid is present in the list it will show response as this
                resp.status_code = 202  # status code made as 400
                return resp  # this response will work if this condition works

            query = ("SELECT Email_Id FROM Users ")  # qurey for selecting email id from the usertable
            cursor.execute(query)  # executing the qurey
            db223 = cursor.fetchall()  # fetching the qurey
            emailid = []  # created an empty list for adding the email ids

            for i in db223:  # iterating the fetched values
                for j in i:  # iterating the tuples
                    emailid.append(j)  # appending the values in to the list

            if Email_Id in emailid:  # checking the email id is present in the list
                resp = jsonify({"Message": "Email is already exists!", "Status": "202 Bad Request"})
                # resp = jsonify(
                #     'Email is already exists!')  # if the emailid is present in the list it will show response as this
                resp.status_code = 202  # status code made as 400
                return resp  # this response will work if this condition works

            else:
                sql = "INSERT INTO Users(User_Id, Email_Id, Password,First_Name ,Last_Name , Created_on , created_by ,Role,Teams,delete)" \
                      " VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"  # qurey for inserting values to the sql
                print(sql, "sqlll")
                data = (User_Id, Email_Id, _hashed_password, First_Name, Last_Name, Created_on, Created_by,
                         Role, Teams, Delete)  # passing the variables from frondend to data
                print(data, "dataa")
                # connecting to psql

                cursor.execute(sql, data)  # executed the cursor with the sql qurey and the datas inserting
                conn.commit()  # commited the conn
                resp = jsonify(
                    {"Message": "User added successfully!", "Status": "200 OK"})  # created a response and jsonifed it
                # resp.status_code = 200  # given a status code 200(truse) to the above response
                return resp  # returning the response if the above condition works

        else:
            res = jsonify('User is not added please check the error below!')  # created a response and jsonifed it
            res.status_code = 202  # giving error status
            return res
    except Exception as e:
        print(e)
    finally:
        cursor.close()




@app.route('/view_users', methods=["GET"])
def list_users():
    try:
        conn = connectDB()
        print(conn, "kkkkkk")
        # conn = psycopg2.connect(host='localhost', dbname='server_management1', user='postgres', password='root',
        #                         # connection with database naming conn
        #                         port=5433)
        # conn = dbase.connect()
        cursor = conn.cursor()
        conn.autocommit = True

        if request.method == 'GET':  # GET method is used here
            cursor.execute("select * from Users where delete =B'0'")  # store inserver_table
            data = cursor.fetchall()  # crusor fetchs all the data
            user = []  # serverlist for get method with variable serverl
            for userdata in data:
                jsonData = {"User_Id": userdata[0], "Email_Id": userdata[1], "Password": userdata[2],
                            "First_Name": userdata[3], "Last_Name": userdata[4], "Created_on": userdata[5],
                            "Created_by": userdata[6], "Updated_on": userdata[7], "Updated_by": userdata[8],
                            "Role": userdata[9], "Teams": userdata[10], "Delete": userdata[11],
                            }
                user.append(jsonData)  # it will show all the data stored in the database with key:value
            data_user = []
            for i in user:
                if i["Created_on"]:
                    created_date = i["Created_on"]
                    date_time_obj = created_date.isoformat() + 'Z'
                    i.update({"Created_on": date_time_obj})
                if i["Updated_on"]:
                    Updated_date = i["Updated_on"]
                    date_time_obj1 = Updated_date.isoformat() + 'Z'
                    i.update({"Updated_on": date_time_obj1})
                data_user.append(i)
                print("datauserrr", data_user)
        return jsonify({"Message": "Record found", "Status code": '200 OK', "Listusers": data_user})

    except Exception as e:
        print(e)
    finally:
        cursor.close()


"""end"""



@app.route('/update_users', methods=['PUT'])
def update_User():
    try:

        _json = request.json  # converting the request to json
        User_Id = _json['User_Id']
        print(User_Id, "User_Id")
        # Email_Id = _json['Email_Id']
        # print(Email_Id, "Email_Id")
        # Password = _json['Password']
        # print(Password, "PASSSWORD")
        First_Name = _json['First_Name']
        print(First_Name, "First_Name")
        Last_Name = _json['Last_Name']
        print(Last_Name, "Last_Name")
        # Created_on = date_today
        # print(Created_on, "Created_on")
        # Created_by = _json['Created_by']
        # print(Created_by, "Created_by")
        Updated_on = date_today
        print(Updated_on, "Updated_on")
        Updated_by = _json['Updated_by']
        print(Updated_by, "Updated_by")
        Role = _json['Role']
        print(Role, "Role")
        Teams = _json['Teams']
        print(Teams, "Teams")
        # Delete = _json['Delete']
        # delete = dele.encode()
        # print(Delete, "deletee", Delete)

        # validate the received values
        if User_Id and First_Name and Last_Name and \
                Updated_on and Updated_by and Role and Teams and request.method == 'PUT':
            # _hashed_password = generate_password_hash(Password)  # do not save password as a plain text so the
            # generate_password_hash will encrypt the password
            # save edits
            sql = "UPDATE Users SET First_Name = %s," \
                  " Last_Name = %s, Updated_on = %s,Updated_by=%s, Role=%s, Teams=%s WHERE User_Id=%s "  # qurey for updating
            print(sql, "sqlllllll")
            data = (First_Name, Last_Name, Updated_on, Updated_by, Role, Teams,
                    User_Id
                    )  # taking the datas from frondend and passing in to a variable
            print(data, "dataaa")
            conn = connectDB()  # connecting to the database
            cursor = conn.cursor()
            query1 = "SELECT User_Id FROM Users"  # qurey for selecting email id from the usertable
            print(query1, "qq11")
            cursor.execute(query1)  # executing the qurey
            db223 = cursor.fetchall()  # fetching the qurey
            print(db223, "db22")
            userid = []  # created an empty list for adding the email ids

            for i in db223:  # iterating the fetched values
                for j in i:  # iterating the tuples
                    userid.append(j)
            print(userid, "userrr")
            if User_Id in userid:
                cursor.execute(sql, data)  # executing the qurey and the datas from frond end
                conn.commit()
                resp = jsonify({"Message": "User updated successfully!", "Status": "200 OK"})
                # resp = jsonify('User updated successfully!')  # jsonifying the response
                resp.status_code = 200  # making the status as 200 (true)
                conn.close()
                return resp  # if the above condition works then giving the response 200
            else:
                resp = jsonify({"Message": "User doesn't exists!", "Status": "202 Bad Request"})
                # resp = jsonify('no userid!')  # if the userid is present in the list it will show response as this
                resp.status_code = 202  # status code made as 400
                return resp
        else:
            resp = jsonify({"Message": "Please check the error below!", "Status": "202 Bad Request"})
            # res = jsonify('User not found')  # jsonifying the response
            resp.status_code = 202  # giving status code 400 (False)
            return resp  # returning the response

    except Exception as e:
        print(e)
    finally:
        cursor.close()

"""deleting user"""


@app.route('/delete_user', methods=['PUT'])
def delete_user():  # created a function for deleting user with their corresponding
    try:
        # id so thats why the id passing as an argument it will call in the url
        # id = int(id)
        # print(id, "id")
        _json = request.json  # converting the request to json
        User_Id = _json['User_Id']
        print(User_Id, "User_Id")

        conn = connectDB()  # connecting to the database
        cursor = conn.cursor()  # created a cursor function and giving cursor_factory=RealDictCursor

        cursor.execute("SELECT * FROM Users  WHERE User_Id=%s",
                       (User_Id,))  # qurey for selecting the datas with the given id
        # and given to the cursor and it will execute
        db22 = cursor.fetchall()  # fetching all the datas of that corresponding id
        print(db22, "db22")
        """test"""
        query1 = "SELECT User_Id FROM Users WHERE DELETE ='1' ;"
        print(query1, "qqq1111")
        cursor.execute(query1)
        db33 = cursor.fetchall()
        print(db33, "db3333333333")
        dele = []
        for i in db33:
            # print(i,"iii")
            for j in i:
                # print(j,"jjjj")
                dele.append(j)
        print(dele, "dele")
        if User_Id in dele:
            print("its already deleted")
            resp = jsonify({"Message": "This is already deleted!", "Status": "202 Bad Request"})
            # res = jsonify('This is already deleted!')  # jsonifying the response
            resp.status_code = 202  # giving status code 400 (False)
            return resp

        """endtest"""
        if len(db22) != 0:  # checking condition if the user is not null
            cursor.execute("UPDATE  Users SET DELETE ='1'WHERE User_Id =%s", (User_Id,))  # qurey for deleting and it will
            # work only the value is not equal to null
            conn.commit()
            resp = jsonify({"Message": "User deleted successfully!", "Status": "202 OK"})

            # resp = jsonify('User deleted successfully!')  # response is jsonifying
            resp.status_code = 202  # giving status code as 200 (true)
            return resp  # if the above condition works thengive the response as 200
        else:
            resp = jsonify({"Message": "User doesn't exists!", "Status": "202 Bad Request"})
            # res = jsonify("User not available with  id ", User_Id)  # if the user is null then this response works
            resp.status_code = 202  # error response
            return resp

    except Exception as e:
        print(e)
    finally:
        cursor.close()




"""Post of Request"""


@app.route('/create_request', methods=['POST'])
def create_request():
    try:
        conn = connectDB()
        cursor = conn.cursor()  # created a cursor
        print(cursor, "cursoor")

        cursor.execute("select Id from Server_Request")  # [(1,),(2,)]
        res1 = cursor.fetchall()
        Id_alr = len(res1)
        Id = Id_alr + 1

        _json = request.json  # converting to json
        # Id = _json['Id']
        # print(Id, "Id")
        Creator = _json['Creator']
        print(Creator, "Creator")
        Start_Date = _json['Start_Date']
        print(Start_Date, "Start_Date")
        End_Date = _json['End_Date']
        print(End_Date, "End_Date")
        Manufacturer = _json['Manufacturer']
        print(Manufacturer, "Manufacturer")
        # Created_on = date_today
        # print(Created_on, "Created_on")
        Number_Of_Servers = _json['Number_Of_Servers']
        print(Number_Of_Servers, "Number_Of_Servers")
        # Updated_on = date_today
        # print(Updated_on, "Updated_on")
        Cpu_model = _json['Cpu_model']
        print(Cpu_model, "Cpu_model")
        CPU_Sockets = _json['CPU_Sockets']
        print(CPU_Sockets, "CPU_Sockets")
        DIMM_Size = _json['DIMM_Size']
        print(DIMM_Size, "DIMM_Size")
        DIMM_Quantity = _json['DIMM_Quantity']
        # delete = dele.encode()
        print(DIMM_Quantity, "DIMM_Quantity", DIMM_Quantity)
        OS_Vendor = _json['OS_Vendor']
        print(OS_Vendor, "OS_Vendor")
        OS_Controller = _json['OS_Controller']
        print(OS_Controller, "OS_Controller")
        OS_Capacity = _json['OS_Capacity']
        print(OS_Capacity, "OS_Capacity")
        Disk_Vendor = _json['Disk_Vendor']
        print(Disk_Vendor, "Disk_Vendor")
        Disk_Controller = _json['Disk_Controller']
        print(Disk_Controller, "Disk_Controller")
        Disk_Capacity = _json['Disk_Capacity']
        print(Disk_Capacity, "DIMM_Size")
        Network_Type = _json['Network_Type']
        print(Network_Type, "Network_Type")
        Network_speed = _json['Network_speed']
        print(Network_speed, "Network_speed")
        Network_ports = _json['Network_ports']
        print(Network_ports, "Network_ports")
        Special_Switching_Needs = _json['Special_Switching_Needs']
        print(Special_Switching_Needs, "Special_Switching_Needs")
        Infraadmin_Comments = _json['Infraadmin_Comments']
        print(Infraadmin_Comments, "Infraadmin_Comments")
        User_Comments = _json['User_Comments']
        print(User_Comments, "User_Comments")
        Request = _json['Request']
        print(User_Comments, "Request")

        # validate the received values
        if Id and Creator and Start_Date and End_Date and Manufacturer and \
                Number_Of_Servers and Cpu_model and CPU_Sockets and DIMM_Size and \
                DIMM_Quantity and OS_Vendor and OS_Controller and OS_Capacity and \
                Disk_Vendor and Disk_Controller and Disk_Capacity and \
                Network_Type and Network_speed and Network_ports and \
                Special_Switching_Needs and Infraadmin_Comments and \
                User_Comments and Request and request.method == 'POST':  # giving condition whether the method is post



            query1 = ("SELECT Id FROM Server_Request ")  # qurey for selecting userid id from the usertable
            print(query1, "q1111")
            cursor.execute(query1)  # executing the qurey
            db224 = cursor.fetchall()  # fetching the qurey
            print(db224, "db224")
            usrid = []  # created an empty list for adding the user ids
            for i in db224:  # iterating the fetched values
                for j in i:  # iterating the tuples
                    print(usrid, "useridd")
                    usrid.append(j)  # appending the values in to the list
                print(usrid, "idddddd")

            if Id in usrid:  # checking the user id is present in the list
                resp = jsonify({"Message": "This id is already exists!",
                                "Status": "202 Bad Request"})  # if the userid is present in the list it will show response as this
                resp.status_code = 202  # status code made as 400
                return resp  # this response will work if this condition works

            else:

                sql = "INSERT INTO Server_Request(Id, Creator, Start_Date,End_Date ,Manufacturer ," \
                      " Number_Of_Servers , Cpu_model , CPU_Sockets, DIMM_Size," \
                      "DIMM_Quantity,OS_Vendor,OS_Controller,OS_Capacity,Disk_Vendor," \
                      "Disk_Controller,Disk_Capacity,Network_Type,Network_speed," \
                      "Network_ports,Special_Switching_Needs,Infraadmin_Comments,User_Comments,Request)" \
                      " VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s, %s,%s,%s,%s,%s,%s,%s,%s,%s)"  # qurey for inserting values to the sql
                print(sql, "sqlll")
                data = (Id, Creator, Start_Date, End_Date, Manufacturer, Number_Of_Servers, Cpu_model,
                        CPU_Sockets, DIMM_Size, DIMM_Quantity, OS_Vendor, OS_Controller, OS_Capacity,
                        Disk_Vendor, Disk_Controller, Disk_Capacity, Network_Type, Network_speed,
                        Network_ports, Special_Switching_Needs, Infraadmin_Comments, User_Comments,
                        Request)  # passing the variables from frondend to data
                print(data, "dataa")
                # connecting to psql

                cursor.execute(sql, data)  # executed the cursor with the sql qurey and the datas inserting
                conn.commit()  # commited the conn
                resp = jsonify(
                    {"Message": "Request added successfully!", "Status": "200 OK"})  # created a response and jsonifed it
                return resp
            # resp.status_code = 200  # given a status code 200(truse) to the above response
            # return resp  # returning the response if the above condition works

        else:
            res = jsonify(
                {"Message": "Request is not added please check the error below!')  # created a response and jsonifed it"})
            res.status_code = 202  # giving error status
            return res

    except Exception as e:
        print(e)
    finally:
        cursor.close()


"""End post request"""
"""ANJANA"""
# function to convert json format from list of tuples and array.
def convert_json(l_o_t, key):
    b = []
    # iterating  the list of tuples to get individual tuples.
    for item in l_o_t:
        a = {}
        # taking range from 0 to number of items in tuples - 1
        for i in range(len(item)):
            a[key[i]] = item[
                i]  # appending value to dictionary by mapping key from array to value in tuples using indexing.
        b.append(a)  # appending all dictionaries to a list.
    return b


@app.route('/list_asset/Reserved', methods=['GET'])
def list_all_reserved():
    """listing reserved assets"""
    try:
        cursor = base.cursor()
        # To show reserved servers,fetch all the data base from the asset table where reserved=false.
        cursor.execute(
            "select asset_id,asset_name,manufacturer,bmc_ip,bmc_user,asset_location,reserved,assigned_to,assigned_from,assigned_by,created_on,created_by,updated_on,updated_by,os_ip,os_user,purpose,cluster_id,delete,status from asset where reserved=true and status=true")
        res = cursor.fetchall()
        # arr = [desc[0].capitalize() for desc in cursor.description]  # getting column name from database
        arr = ["Asset_Id","Asset_Name", "Manufacturer", "BMC_IP", "BMC_User", "Asset_Location", "Reserved", "Assigned_to",
               "Assigned_from", "Assigned_by", "Created_on", "Created_by", "Updated_on", "Updated_by", "OS_IP",
               "OS_User", "Purpose", "Cluster_Id", "Delete", "Status"]
        json_data = convert_json(res, arr)
        data = []
        for i in json_data:

            cursor.execute("select email_id from users where user_id=%s", [i['Assigned_to']])
            res = cursor.fetchall()
            for j in res:
                i.update({"Assigned_to": j[0].split("@")[0]})
            if i["Assigned_from"]:
                actual_date = i["Assigned_from"]
                date_time_obj = actual_date.isoformat() + 'Z'
                i.update({"Assigned_from": date_time_obj})
            if i["Updated_on"]:
                actual_date = i["Updated_on"]
                date_time_obj1 = actual_date.isoformat() + 'Z'
                i.update({"Updated_on": date_time_obj1})
            if i["Created_on"]:
                actual_date = i["Created_on"]
                date_time_obj2 = actual_date.isoformat() + 'Z'
                i.update({"Created_on": date_time_obj2})
            data.append(i)
        # if json.args()
        return jsonify({"ListAsset": data, "Message": "listing all assets!", "Status code": "200 ok"})
    except Exception as e:
        print(e)
        resp = jsonify({"Message": "exception occurred!", "Status code": "202 bad request"})
        resp.status_code = 202
        return resp


"""-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""


@app.route('/list_asset/pool', methods=['GET'])
def list_all_pool():
    """listing pooled assets"""
    try:
        cursor = base.cursor()
        # To show reserved servers,fetch all the data base from the asset table where reserved=false.
        cursor.execute(
            "select asset_id,asset_name,manufacturer,bmc_ip,bmc_user,asset_location,reserved,assigned_to,assigned_from,assigned_by,created_on,created_by,updated_on,updated_by,os_ip,os_user,purpose,cluster_id,delete,status from asset where delete=B'0' and reserved=false or reserved IS NULL")

        res = cursor.fetchall()
        # arr = [desc[0] for desc in cursor.description]  # getting column name from database
        arr = ["Asset_Id","Asset_Name", "Manufacturer", "BMC_IP", "BMC_User", "Asset_Location", "Reserved", "Assigned_to",
               "Assigned_from", "Assigned_by", "Created_on", "Created_by", "Updated_on", "Updated_by", "OS_IP",
               "OS_User", "Purpose", "Cluster_Id", "Delete", "Status"]

        json_data = convert_json(res, arr)
        data = []
        for i in json_data:
            if i["Assigned_from"]:
                actual_date = i["Assigned_from"]
                date_time_obj = actual_date.isoformat() + 'Z'
                i.update({"Assigned_from": date_time_obj})
            if i["Updated_on"]:
                actual_date = i["Updated_on"]
                date_time_obj1 = actual_date.isoformat() + 'Z'
                i.update({"Updated_on": date_time_obj1})
            if i["Created_on"]:
                actual_date = i["Created_on"]
                date_time_obj2 = actual_date.isoformat() + 'Z'
                i.update({"Created_on": date_time_obj2})
            data.append(i)

        return jsonify({"ListAsset": data, "Message": "listing all assets!", "Status code": "200 ok"})
    except Exception as e:
        print(e)
        resp =  jsonify({"Message": str(e), "Status code": "202 bad request"})
        resp.status_code = 202
        return resp


"""-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""


@app.route('/my_asset', methods=['POST'])
def my_server():
    """listing specified users reserved assets"""
    try:
        cursor = base.cursor()
        cursor.execute("select user_id from users")
        result = cursor.fetchall()
        list_user_id = []
        for i in result:
            for j in i:
                list_user_id.append(j)
        print(list_user_id)

        user_id = request.json.get('Assigned_to')
        print(user_id)
        print(type(user_id))
        cursor1 = base.cursor()
        if int(user_id) in list_user_id:
            query = "select asset_id,asset_name,manufacturer,bmc_ip,bmc_user,asset_location,reserved,assigned_to,assigned_from,assigned_by,created_on,created_by,updated_on,updated_by,os_ip,os_user,purpose,cluster_id,delete,status  from asset where reserved=%s and assigned_to=%s"
            cursor1.execute(query, [True, user_id])
            res = cursor1.fetchall()
            # arr = [desc[0] for desc in cursor1.description]  # getting column name from database
            arr = ["Asset_Id", "Asset_Name","Manufacturer", "BMC_IP", "BMC_User", "Asset_Location", "Reserved", "Assigned_to",
                   "Assigned_from", "Assigned_by", "Created_on", "Created_by", "Updated_on", "Updated_by", "OS_IP",
                   "OS_User", "Purpose", "Cluster_Id", "Delete", "Status"]
            json_data = convert_json(res, arr)
            data = []
            for i in json_data:
                cursor.execute("select email_id from users where user_id=%s", [i['Assigned_to']])
                res = cursor.fetchall()
                print(res)
                for j in res:
                    i.update({"Assigned_to": j[0].split("@")[0]})
                if i["Assigned_from"]:
                    actual_date = i["Assigned_from"]
                    date_time_obj = actual_date.isoformat() + 'Z'
                    i.update({"Assigned_from": date_time_obj})
                if i["Updated_on"]:
                    actual_date = i["Updated_on"]
                    date_time_obj1 = actual_date.isoformat() + 'Z'
                    i.update({"Updated_on": date_time_obj1})
                if i["Created_on"]:
                    actual_date = i["Created_on"]
                    date_time_obj2 = actual_date.isoformat() + 'Z'
                    i.update({"Created_on": date_time_obj2})
                data.append(i)

            return jsonify({"ListAsset": data, "Message": "Listed specified assets", "Status Code": "200 ok"})
        else:
            resp = jsonify({"Message": "user not found", "Status Code": "202 "})
            resp.status_code = 202
            return resp
    except Exception as e:
        print(e)
        resp = jsonify({"Message": str(e), "Status Code": "202"})
        resp.status_code = 202
        return resp


"""-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""


@app.route('/release_asset', methods=['POST'])
def release():
    """releasing assets of a user"""
    try:
        cursor = base.cursor()
        asset_id = request.json.get('Asset_Id')
        cursor.execute("select reserved from asset where asset_id=%s", [asset_id])
        res = cursor.fetchall()
        for i in res:
            for j in i:
                if j:
                    cursor1 = base.cursor()
                    # cursor1.execute(
                    #     "update asset set assigned_to=NULL,assigned_by=NULL,status = %s,reserved=%s where asset_id=%s",
                    #     [False, False, asset_id])
                    cursor1.execute(
                        "select assigned_to,assigned_from,assigned_by,updated_by from asset where asset_id=%s",
                        [asset_id])
                    details = cursor1.fetchall()
                    for item in details:
                        assigned_to = item[0]
                        assigned_from = item[1]
                        assigned_by = item[2]
                        # updated_by = item[3]
                    cursor1.execute("select id from historic_details")  # [(1,),(2,)]
                    res1 = cursor1.fetchall()
                    ID_alr = len(res1)
                    ID = ID_alr + 1

                    cursor1.execute(
                        "INSERT INTO Historic_details(ID,Asset_ID,Assigned_to,Assigned_from,Updated_on,Updated_by,Remarks) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        [ID, asset_id, assigned_to, assigned_from, date.today(),
                         assigned_by, 'releasing asset'])
                    # cursor1 = base.cursor()
                    cursor1.execute(
                        "update asset set assigned_to=NULL,assigned_by=NULL,status = %s,reserved=%s where asset_id=%s",
                        [False, False, asset_id])
                    return jsonify({"Message": "Server Released", "Status Code": "200 OK"})

                else:
                    resp = jsonify({
                        "Message": "server can't release", "Status Code": "202"})
                    resp.status_code = 202
                    return resp
    except Exception as e:
        print(e)
        resp = jsonify({"StatusInternalServerError": "Invalid character 202"})
        resp.status_code = 202
        return resp


"""-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""


@app.route('/historic_details', methods=['GET'])
def history():
    try:
        cursor = base.cursor()
        cursor.execute("select * from historic_details")
        arr = ["Id", 'Asset_ID', 'Assigned_to', 'Assigned_from', 'Updated_on', 'Updated_by', "Remarks"]
        res = cursor.fetchall()
        # arr= [desc[0] for desc in cursor.description]
        json_data = convert_json(res, arr)
        data = []
        for i in json_data:
            cursor.execute("select email_id from users where user_id=%s", [i['Assigned_to']])
            res = cursor.fetchall()
            print(res)
            for j in res:
                i.update({"Assigned_to": j[0].split("@")[0]})
            if i["Assigned_from"]:
                actual_date = i["Assigned_from"]
                date_time_obj = actual_date.isoformat() + 'Z'
                i.update({"Assigned_from": date_time_obj})
            if i["Updated_on"]:
                actual_date = i["Updated_on"]
                date_time_obj1 = actual_date.isoformat() + 'Z'
                i.update({"Updated_on": date_time_obj1})
            data.append(i)
        return jsonify({"Historic_Details": data, "Message": "Listing Historic details", "Status Code": "200 OK"})
    except Exception as e:
        print(e)
        resp = jsonify({"Message": "Exception occurred!", "Status Code": "202"})
        resp.status_code = 202
        return resp


"""-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""


@app.route("/dashboard4", methods=['POST'])
def dash_locc():
    """dashboard 4 api: showing statistics of a specific location"""
    try:
        cursorr = base.cursor()
        cursorr.execute("select asset_location from asset")
        resultt = cursorr.fetchall()
        location = request.json.get("Asset_location")
        for i in resultt:
            if location in i:
                cursor = base.cursor()
                cursor1 = base.cursor()
                cursor.execute("select asset_id from asset where reserved=true and asset_location=%s", [location])
                cursor1.execute("select asset_id from asset where reserved=false and asset_location=%s", [location])
                res = cursor.fetchall()
                res1 = cursor1.fetchall()
                return jsonify(
                    {"Location": location, "Reserved": len(res), "Vacant": len(res1), "Message": "Updated Statistics",
                     "Status Code": "200"})
        else:
            resp = jsonify({"Message": "Check location!!", "Status Code": "202 Bad Request"})
            resp.status_code = 202
            return resp
    except Exception as e:
        print(e)
        resp = jsonify({"Message": "Exception occurred!", "Status Code": "202"})
        resp.status_code = 202
        return resp


"""-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""


@app.route('/assign_asset', methods=['POST'])
def assign():
    """assigning asset to a user"""
    try:
        asset_id = request.json.get('Asset_Id')
        user_id = request.json.get('Assigned_to')
        assigned_by = request.json.get('Assigned_by')
        Updated_by = request.json.get('Updated_by')

        cursor = base.cursor()
        cursor.execute("select reserved,delete from asset where asset_id=%s", [asset_id])
        res = cursor.fetchall()
        if res == [(False, '0')]:
            cursor1 = base.cursor()
            cursor1.execute("select id from historic_details")
            res1 = cursor1.fetchall()
            id = len(res1) + 1
            cursor1.execute(
                "INSERT INTO Historic_details(ID,Asset_ID,Assigned_to,Assigned_from,Updated_on,Updated_by,Remarks) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                [id, asset_id, user_id, date.today(),
                 date.today(), Updated_by, 'assigning server'])
            cursor1.execute(
                "update asset set assigned_to=%s,assigned_from=%s, assigned_by=%s,status=true,reserved=%s where asset_id=%s",
                [user_id, date.today(), assigned_by, True, asset_id])
            return jsonify({"Message": "Server Assigned!", "Status Code": "200 OK"})
        else:
            resp = jsonify({"Message": "Server Cannot Be Assigned!", "Status Code": "202 Bad Request"})
            resp.status_code = 202
            return resp
    except Exception as e:
        print(e)
        resp = jsonify({"Message": "Exception occurred!", "Status Code": "202"})
        resp.status_code = 202
        return resp


"""------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"""


@app.route('/list_request', methods=['GET'])
def user_request_list():
    """listing requests from users"""
    try:
        cursor = base.cursor()
        cursor.execute("select * from server_request")
        request_list = cursor.fetchall()
        arr = ["Id", "Creator", "Start_Date", "End_Date", "Manufacturer", "Number_Of_Servers", "Cpu_model",
               "CPU_Sockets", "DIMM_Size", "DIMM_Quantity", "OS_Vendor", "OS_Controller", "OS_Capacity", "Disk_Vendor",
               "Disk_Controller", "Disk_Capacity", "Network_Type", "Network_speed", "Network_ports",
               "Special_Switching_Needs", "Infraadmin_Comments", "User_Comments", "Request"]
        json_data = convert_json(request_list, arr)
        data = []
        for i in json_data:
            if i["Start_Date"]:
                actual_date = i["Start_Date"]
                date_time_obj = actual_date.isoformat() + 'Z'
                i.update({"Start_Date": date_time_obj})
            if i["End_Date"]:
                actual_date = i["End_Date"]
                date_time_obj1 = actual_date.isoformat() + 'Z'
                i.update({"End_Date": date_time_obj1})
            data.append(i)
        return jsonify({"Data": "List of requests", "Listusers": data, "Status": "200 OK"})
    except Exception as e:
        print(e)
        resp =  jsonify({"Message": "Exception occurred!", "Status Code": "202"})
        resp.status_code = 202
        return resp



"""suchitra"""
conn = connectDB()

conn.autocommit = True  # if you commit a database, it saves all the changes till that particular point


@cross_origin()
                       #1 # adding_asset  #
@app.route('/add_asset', methods=['POST'])

def add_asset():

    try:

        if request.method == 'POST':  # using POST method to request the data
            cursor = conn.cursor()
            cursor.execute("select Asset_Id from Asset")  # [(1,),(2,)]
            res1 = cursor.fetchall()            #  fetching the data from database
            Id_alr = len(res1)                 # variable id_alr used for the length of the fetched data
            Asset_Id = Id_alr + 1           # here it is incred with +1
            cursor.execute                # it is executed
            _json = request.json            # json format
            print("_json")


            Asset_Name=_json["Asset_Name"]
            Manufacturer = _json["Manufacturer"]
            BMC_IP = _json["BMC_IP"]
            BMC_User= _json["BMC_User"]
            BMC_Password = _json["BMC_Password"]
            Asset_Location = _json["Asset_Location"]
            # Reserved = _json["Reserved"]
            # # assigned_on = _json["assigned_on"]
            # Assigned_to = _json["Assigned_to"]
            # Assigned_from=_json["Assigned_from"]
            # Assigned_by = _json["Assigned_by"]
            Created_on=date_today
            Created_by = _json["Created_by"]
            OS_IP=_json["OS_IP"]
            OS_User=_json["OS_User"]
            OS_Password=_json["OS_Password"]
            # Updated_on=_json["Updated_on"]
            # Updated_by= _json["Updated_by"]
            Purpose = _json["Purpose"]
            Cluster_Id = _json["Cluster_Id"]
            # team_id = _json["team_id"]
            Delete = "0"
            # Status = _json["Status"]
            print("server_id")
            # cursor = conn.cursor()  # created a cursor
            print("zdfrhv")
            query1 ="SELECT Asset_Id FROM Asset"
            print(query1,"q1111")
            cursor.execute(query1)
            fetch = cursor.fetchall()
            print(fetch,"fe1111")
            lst = []
            for i in fetch:
                for j in i:
                    lst.append(j)
                print(lst,"lsttt")
            if Asset_Id not in  lst:

                    # values to assign in the columns
                VALUES = (Asset_Id,Asset_Name,Manufacturer,BMC_IP,BMC_User,BMC_Password,
                          Asset_Location,#Reserved,Assigned_to,Assigned_from,Assigned_by,
                          Created_on,Created_by,OS_IP,OS_User,OS_Password,#Updated_on,Updated_by,
                          Purpose,Cluster_Id,Delete) #Delete,Status)
                print("iohvd")
                cursor.execute(
                    'INSERT INTO Asset(Asset_Id,Asset_Name,Manufacturer,BMC_ip,BMC_User,'
                    'BMC_Password,Asset_Location,Created_on,Created_by,OS_IP,OS_User,OS_Password,Purpose,Cluster_Id,delete) '
                    'values (%s,%s, %s ,%s ,%s ,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',VALUES)
                    # execute the values using cursor in the server_table to store all the new data
                print("awxfyn")
                conn.commit()
                # conn.commit()  # commit
                print("oook")
                cursor.execute('select * from asset') # to show the data in the asset_table
                print("fjrdgchk")
                data = cursor.fetchall()              #it will fetch all the data with variable data

                print("_id")



                    # serverList.append(data)
                # return jsonify(serverList)            #it will show list of server with this newly added
                resp = jsonify({'Message':'recorded successfully' ,'Status code':'200 ok'})  # created a response and jsonifed it
                resp.status_code = 200  # given a status code 200(truse) to the above response
                return resp  # returning the response if the above condition works
    except Exception as exp:
            resp = jsonify({'Message':'AlreadyExist' ,'Status code':'202'})  # created a response and jsonifed it
            resp.status_code = 202
            return resp               #return the response
    finally:
        cursor.close()

                   # 2   #list_asset#

@app.route('/list_asset', methods=["GET"])
def view_server():
    # conn = connectDB()
    try:
        print(conn,"kkkkkk")

        cursor = conn.cursor()
        # conn.autocommit = True

        if request.method == 'GET':  # GET method is used here
            cursor.execute("select * from asset WHERE delete =B'0'")  # store inserver_table

            data = cursor.fetchall()  # crusor fetchs all the data
            serverl = []  # serverlist for get method with variable serverl
            for serverData in data:


                jsonData =  {"Asset_ID": serverData[0],"Asset_Name":serverData[1],"Manufacturer": serverData[2],"BMC_IP": serverData[3], "BMC_User": serverData[4],
                        # "BMC_password": serverData[4],
                        "Asset_Location": serverData[6],"Reserved": serverData[7],"OS_IP":serverData[15],"Assigned_to": serverData[8],"Assigned_from":serverData[9],"Assigned_by": serverData[10],
            "OS_User":serverData[16],
                        "Created_on":serverData[11],"Created_by":serverData[12],"Updated_on":serverData[13],"Updated_by":serverData[14],
                             "Purpose":serverData[18],"Cluster_Id":serverData[19] ,
                         "Delete":serverData[20],
                    "Status":serverData[21]}
                serverl.append(jsonData)  # it will show all the data stored in the database with key:value
        a = []
        for i in serverl:

            cursor.execute("select email_id from users where user_id=%s", [i['Assigned_to']])              # select the email id from user table a it is sameas assigned to
            res = cursor.fetchall()                                # it will fetch all the data
            print(res)
            for j in res:
                i.update({"Assigned_to": j[0].split("@")[0]})              #it will split the email id and print the first name only
            a.append(i)
        datavar = []
        for i in serverl:
            if i["Created_on"]:
                created_date = i["Created_on"]                         #here changing the format to "2022-10-03T00:00:00Z"
                date_time_obj = created_date.isoformat() + 'Z'
                i.update({"Created_on": date_time_obj})
            if i["Updated_on"]:
                Updated_date = i["Updated_on"]
                date_time_obj1 = Updated_date.isoformat() + 'Z'
                i.update({"Updated_on": date_time_obj1})
            if i["Assigned_from"]:
                Updated_date = i["Assigned_from"]
                date_time_obj1 = Updated_date.isoformat() + 'Z'
                i.update({"Assigned_from": date_time_obj1})
            datavar.append(i)
            # print("datauserrr", datavar)
        return jsonify({"Message":"listing all assets","Status code": '200 OK',"ListAsset":datavar})           # response message
    except Exception as e:
        print(e)
    finally:
        cursor.close()

# 3 # delete_asset#

@app.route('/delete_asset', methods=['PUT'])
def delete_ser():  # created a function for deleting user with their corresponding
    try:

        _json = request.json  # converting the request to json
        Asset_Id = _json['Asset_Id']
        print(Asset_Id, "Asset_Id")

        conn = connectDB()  # connecting to the database
        cursor = conn.cursor()  # created a cursor function and giving cursor_factory=RealDictCursor
        curs = conn.cursor()
        cursor.execute("SELECT * FROM asset  WHERE Asset_Id=%s",
                       (Asset_Id,))  # qurey for selecting the datas with the given id
        # and given to the cursor and it will execute
        db22 = cursor.fetchall()  # fetching all the datas of that corresponding id
        print(db22, "db22")

        if len(db22) != 0:  # checking condition if the user is not null
            cursor.execute("UPDATE  asset SET DELETE ='1',Reserved= False,Updated_on=%s WHERE Asset_Id =%s", [date.today() ,(Asset_Id,)])  # qurey for deleting and it will
            # work only the value is not equal to null
            curs.execute(
                "SELECT Asset_Id,Assigned_to,Assigned_from,Updated_on,Updated_by FROM ASSET WHERE Asset_Id =%s",
            (Asset_Id,))
            print("axydt cgbi; kn/on'i")
            data = curs.fetchall()  # fetching all the datas of that corresponding id
            print(data, "dattttaa")
            remarks = "remark"

            lst = []
            for i in data:
                for j in i:
                    lst.append(j)
                    # lst.append()
            print(lst, "lsssttttt")  # it will print the list lst
            print(lst[0], "ppppp")
            # print(lst[1],"qqqq")
            # print(lst[2],"ooo")
            # print(lst[3],"333")
            # print(lst[4],"44")
            lst2 = lst + [remarks]  # creating another list to add the string format REMARK with that list lst
            print(lst2, "l222")

            query = (lst2[0], lst2[1], lst2[2], lst2[3], lst2[4],
                     lst2[5])  # query to get all the fields starting from index 0 to 5
            # print(query,"qqq")
            # print(lst[0],"1lst")
            # print(lst[0],"9999")
            curs.execute(
                'INSERT INTO  historic_details(Asset_Id,Assigned_to,Assigned_from,Updated_on,Updated_by,remarks)values (%s, %s ,%s ,%s ,%s,%s)',
                query)  # insert query

            print(query, "queryyyyyyyyy")  # it will print the query



            conn.commit()
            resp = jsonify({"Message": "asset deleted successfully!", "Status": "200 OK"})

            # resp = jsonify('User deleted successfully!')  # response is jsonifying
            resp.status_code = 200  # giving status code as 200 (true)
            return resp  # if the above condition works thengive the response as 200



        else:
            resp = jsonify({"Message": "ASSET_ID IS NOT THERE!", "Status": "202 Bad Request"})
            # res = jsonify("User not available with  id ", User_Id)  # if the user is null then this response works
            resp.status_code = 202  # error response
            return resp

    except Exception as e:
        print(e)
    finally:
        cursor.close()

  #if assigned from is null ,then it will show error like violates not null constraint
  #in postman it is showing like this -
#   The view function for 'delete_ser' did not return a valid response. The function either returned None or ended without a return statement


      #4 #platform_profile#

@app.route('/platformProfile', methods=['GET'])
def getfile():
        print("vgsduofwedj")


        with open("platformprofile.json", "r+") as f:
            data = f.read()
        return data

   #5 #update the request_form#

@app.route('/request_update', methods=['PUT'])
def UpdateRequest():  # created a function for deleting user with their corresponding

    conn = connectDB()
    if request.method == 'PUT':
        _json = request.json                #the put method withjson format
        ID = _json["ID"]

        # Infraadmin_Comments   =  _json["Infraadmin_Comments"]
        Infraadmin_Comments = _json["Infraadmin_Comments"]
        Request= _json["Request"]

        cursor = conn.cursor()            # cursor used

        data = ( ID, Infraadmin_Comments,Request)      #value
        cursor.execute("SELECT * FROM server_request  WHERE ID=%s", (ID,))       # execute query with id
        print(data)

        cursor.execute("UPDATE  server_request SET Request= %s WHERE ID =%s",
                       (Request, ID))  # qurey for updating the request column using id
        print("kkkkkkk")

        cursor.execute(
            "UPDATE server_request SET Infraadmin_Comments = array_prepend( %s, Infraadmin_Comments) WHERE ID=%s",
            [str(Infraadmin_Comments) + str(my_datetime_utc), ID])                # updating thecomment section with today date and time
        conn.commit()           #commit
        cursor.execute('select * from server_request where ID = %s', (ID,))
        data = cursor.fetchall()         # it fetches all the data
        print("data")


        resp = jsonify({"Message": "updated successfully!", "Status": "200 OK"})      # final message it will print

        # resp = jsonify('User deleted successfully!')  # response is jsonifying
        resp.status_code = 200  # giving status code as 200 (true)
        return resp

"""vibha"""


@app.route('/update_asset_details', methods=['POST'])
def update_asset():
    conn = connectDB()
    if request.method == 'POST':
        _json = request.json
        Asset_Id = str(_json["Asset_Id"])
        Asset_Location = _json["Asset_Location"]
        Purpose = _json["Purpose"]
        Updated_by = _json["Updated_by"]
        cursor = conn.cursor()
        data = (Updated_by, Asset_Location, Purpose)
        cursor.execute('select * from asset where asset_id=%s', Asset_Id)
        sql_update_query = """UPDATE asset set Updated_by = %s , asset_location = %s , purpose = %s  where asset_id = %s"""
        cursor.execute(sql_update_query, (Updated_by, Asset_Location, Purpose, Asset_Id))
        conn.commit()
        cursor.execute('select * from asset where asset_id = %s', Asset_Id)
        data = cursor.fetchall()
        resp = jsonify({'Message': 'Asset updated successfully !!', 'status': '200 OK'})
        #print(resp)
        resp.status_code = 200
        v = resp.status_code
        #print(v)
        assert v == 200, "code does'not match"
        return resp



@app.route('/server_request', methods=['PUT'])
def server_request():
    conn = connectDB()
    if request.method == 'PUT':
        _json = request.json
        ID = _json["ID"]
        Creator = _json["Creator"]
        Start_Date = _json["Start_Date"]
        End_Date = _json["End_Date"]
        Manufacturer = _json["Manufacturer"]
        Number_Of_Servers = _json["Number_Of_Servers"]
        Cpu_model = _json["Cpu_model"]
        CPU_Sockets = _json["CPU_Sockets"]
        DIMM_Size = _json["DIMM_Size"]
        DIMM_Quantity = _json["DIMM_Quantity"]
        OS_Vendor = _json["OS_Vendor"]
        OS_Controller = _json["OS_Controller"]
        OS_Capacity = _json["OS_Capacity"]
        Disk_Vendor = _json["Disk_Vendor"]
        Disk_Controller = _json["Disk_Controller"]
        Disk_Capacity = _json["Disk_Capacity"]
        Network_Type = _json["Network_Type"]
        Network_speed = _json["Network_speed"]
        Network_ports = _json["Network_ports"]
        Special_Switching_Needs = _json["Special_Switching_Needs"]
        User_Comments = _json["User_Comments"]

        cursor = conn.cursor()

        data = (ID, Creator, Start_Date, End_Date, Manufacturer, Number_Of_Servers, Cpu_model, CPU_Sockets, DIMM_Size,
                DIMM_Quantity, OS_Vendor,
                OS_Controller, OS_Capacity, Disk_Vendor, Disk_Controller, Disk_Capacity, Network_Type, Network_speed,
                Network_ports, Special_Switching_Needs, User_Comments)
        cursor.execute("SELECT * FROM server_request  WHERE ID=%s", (ID,))
        #print(data)

        cursor.execute(
            "UPDATE  server_request SET Creator= %s, Start_Date= (%s), End_Date= (%s), Manufacturer= %s, Number_Of_Servers = %s , Cpu_model = %s, CPU_Sockets = %s, DIMM_Size = %s, DIMM_Quantity = %s, OS_Vendor = %s, OS_Controller = %s, OS_Capacity = %s , Disk_Vendor = %s, Disk_Controller = %s, Disk_Capacity = %s, Network_Type = %s, Network_speed = %s, Network_ports = %s, Special_Switching_Needs = %s WHERE ID =%s",
            (Creator, Start_Date, End_Date, Manufacturer, Number_Of_Servers, Cpu_model, CPU_Sockets, DIMM_Size,
             DIMM_Quantity, OS_Vendor,
             OS_Controller, OS_Capacity, Disk_Vendor, Disk_Controller, Disk_Capacity, Network_Type, Network_speed,
             Network_ports, Special_Switching_Needs, ID))

        cursor.execute("UPDATE server_request SET User_Comments = array_prepend( %s, User_Comments) WHERE ID=%s",
                       (User_Comments, ID))

        conn.commit()
        cursor.execute('select * from server_request where ID = %s', (ID,))
        data = cursor.fetchall()
        resp = jsonify({'Message': 'Server Request updated successfully !!', 'Status': '200 OK'})
        #print(resp)
        resp.status_code = 200
        v = resp.status_code
        #print(v)
        assert v == 200, "code does'not match"
        return resp


import base64
from itsdangerous import base64_decode
app.config['SECRET_KEY'] = 'this is a secret key'

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
CORS(app)

@app.route('/login', methods=['POST'])
def login():
        Email_Id = request.json.get('Email_Id')
        Password = request.json.get('Password')
        # id = request.json.get('User_Id')
        #print(id)
        newtoken = Password
        token = newtoken.encode('ascii')
        base64_bytes = base64.b64encode(token)
        base64_message = base64_bytes.decode('ascii')
        value = base64_decode(base64_message)
        UserPass = value.decode('ascii')

        if len(Email_Id)==0 or len(Password)==0:

            resp = jsonify({'Message': "Email/Password can't be empty",'Status':"202"})
            resp.status_code = 202
            return resp
        if len(Password)!=0 and len(Email_Id)!=0:
           cur.execute('SELECT * FROM users where email_id=%s', [Email_Id])
           res = cur.fetchall()
           if len(res)!=0:
               l = []
               for i in res:
                   for j in i:
                       l.append(j)
               # print(l[2])
               stored_password = l[2]
               result = check_password_hash(stored_password, Password)
               if result == True:
                     return jsonify({'Message': 'Succesfully Logged In', 'Role': l[9], 'Username': l[3], 'User_Id': l[0],
                               'Status': "200 OK", 'Token': base64_message})
               else:
                     resp = jsonify({'Message': 'Bad Request - invalid email id or password', 'Status': '202'})
                     resp.status_code = 202
                     return resp
           else:
               resp = jsonify({'Message': "Bad Request - invalid email id or password", 'Status': "202"})
               resp.status_code = 202
               return resp

        else:
            resp = jsonify({'Message': 'Password must be not null'})
            resp.status_code = 202
            return resp

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

