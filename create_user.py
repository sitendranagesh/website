from database.auth_operation import create_users_table, add_user

create_users_table()
result = add_user("captain", "sitendra")
print(result)