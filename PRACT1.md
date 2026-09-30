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
