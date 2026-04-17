import pyperclip  
def TO_CAMEL_CASE(string:str) -> str:
    split_str = string.split()
    camel_str = [el.capitalize() for el in split_str]
    camel_str = (' '.join(camel_str)).strip()
    print(camel_str)
    return camel_str
    
while 1:
    string = str(input())
    if string == '0':
        break
    pyperclip.copy(TO_CAMEL_CASE(string))
