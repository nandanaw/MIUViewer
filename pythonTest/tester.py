import re
input_string = input("Input String: ")
m = re.split('[^A-Za-z]', input_string)

ret_dict = {}

while '' in m:
    m.remove('')

for x in m:
    if x in ret_dict:
        ret_dict[x] += 1
    else:
        ret_dict[x] = 1

for item in ret_dict.items():
    print(str(item[1]) + " " + str(item[0]))