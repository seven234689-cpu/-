import db
opts = [{'label': r['student_code'], 'value': r['student_code']} 
        for _, r in db.df_student.iterrows()]
print("Options count:", len(opts))
print("First option:", opts[0])
print("Last option:", opts[-1])