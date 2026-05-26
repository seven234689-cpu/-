import db

code = '205N0001.19'

print("=== df_gpa ===")
stu = db.df_gpa[db.df_gpa['student_code'] == code]
print("Found in df_gpa:", len(stu))
print(stu)

print("\n=== df (scores) ===")
sc = db.df[db.df['student_code'] == code]
print("Found in df:", len(sc))
print(sc.head(3))