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

