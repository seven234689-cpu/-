f = open('app.py', 'r', encoding='utf-8')
c = f.read()
f.close()

c = c.replace("'background':'#111'", "'background':'#F5F6FA'")
c = c.replace("'background':'#1C1814'", "'background':'white'")
c = c.replace("background:#070A14", "background:#F5F6FA")
c = c.replace("'background':'#070A14'", "'background':'#F5F6FA'")

open('app.py', 'w', encoding='utf-8').write(c)
print('done')