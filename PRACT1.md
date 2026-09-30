# практическая 1


## задание 1
~~~
grep -o '^[^:]*' /etc/passwd | sort
~~~
Результат: 

<img width="1354" height="937" alt="Снимок экрана — 2026-09-30 в 17 43 33" src="https://github.com/user-attachments/assets/9d7cc5a5-0019-47a9-84c0-0a3f42c38724" />

## задание 2
~~~
cat /etc/protocols | sort -k2 -nr | head -5 | awk '{print $2, $1}'
~~~
Результат: 
<img width="1326" height="155" alt="Снимок экрана — 2026-09-30 в 17 56 11" src="https://github.com/user-attachments/assets/9821241b-7501-461f-a35c-d9e23dfe4918" />

## задание 3
~~~
nano banner

#!/bin/bash

text="$1"
len=${#text}
line=$(printf '%*s' "$((len + 2))" '' | tr ' ' '-')

echo "+$line+"
echo "| $text |"
echo "+$line+"
~~~
Результат: 
<img width="956" height="93" alt="Снимок экрана — 2026-09-30 в 20 11 20" src="https://github.com/user-attachments/assets/db8f294f-b210-4279-adc4-6a2fb91baf89" />

## задание 4
~~~
nano identifiers

#!/bin/bash
grep -o '[A-Za-z_][A-Za-z0-9_]*' "$1" | sort -u | tr '\n' ' '

#include <stdio.h>

int main() {
    printf("hello world\n");
    return 0;
}int main() {
    int number = 5;
    printf("hello");
}

./identifiers main.c
~~~
Результат: 

<img width="812" height="54" alt="Снимок экрана — 2026-09-30 в 20 39 05" src="https://github.com/user-attachments/assets/2f60a47c-772c-434e-a7ff-dba64f512d1f" />

## задание 5
~~~
nano reg

chmod +x "$1"
sudo cp "$1" /usr/local/bin

chmod +x reg

./reg banner

~~~


## задание 6
~~~
nano prog6

#!/bin/bash

for file in *.c *.js *.py

do
    first_str=$(head -n 1 "$file")
    if echo "$first_str" | grep -q '^//\|^/\*\|^#'; then
        echo "$file: comments"
    else
        echo "$file: no comments"
    fi
done


chmod +x prog6

nano test.c

// comment
int main() {
    return 0;
}

nano test.py
# comment
print("hello")

nano test.js
// comment
console.log("hello");

./prog6
~~~

Результат: 

<img width="644" height="100" alt="Снимок экрана — 2026-09-30 в 21 43 16" src="https://github.com/user-attachments/assets/96f24607-7e94-46d4-bdcd-0d2f532581ec" />




