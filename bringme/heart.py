import time
#words = input('Please input the words you want to say!:')
words = "Dear jingjing baby, I love U, Forever!"
for item in words.split():
    #item = item+' '
    letterlist = []#letterlistlist_X
    for y in range(12, -12, -1):
        list_X = []#list_X?XStringletters
        letters = ''#letters??list_X
        for x in range(-30, 30):#*,**
            expression = ((x*0.05)**2+(y*0.1)**2-1)**3-(x*0.05)**2*(y*0.1)**3
            if expression <= 0:
                letters += item[(x-y) % len(item)]
            else:
                letters += ' '
        list_X.append(letters)
        letterlist += list_X
    print('\n'.join(letterlist))
    time.sleep(1.5)