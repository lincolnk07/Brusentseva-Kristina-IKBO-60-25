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

    if echo "$first_str" | grep -qE '^[[:space:]]*(//|/\*|#)'; then
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

## задание 7
~~~
nano prog7

#!/bin/bash

find "$1" -type f -exec md5sum {} + | sort | awk '
{
    hash = $1
    file = $2

    if (hash == prev_hash) {
        if (printed == 0) {
            print prev_file
            printed = 1
        }
        print file
    } else {
        printed = 0
    }

    prev_hash = hash
    prev_file = file
}
'
chmod +x prog7
mkdir test_dup
echo hello >> test_dup/a.txt
echo hello >> test_dup/b.txt
echo world >> test_dup/c.txt
./prog7 test_dup
~~~
Результат:

<img width="734" height="77" alt="Снимок экрана — 2026-10-01 в 13 47 11" src="https://github.com/user-attachments/assets/16bcd578-84e5-4b8b-9eb2-89be1e9e2b65" />

## задание 8
~~~
nano prog8

#!/bin/bash
tar -cf archive.tar $(find "$1" -type f -name "*.$2")

chmod +x prog8

mkdir test_arch
echo "gfvfvvff" >> test_arch/1.txt
echo "gfvfvvff" >> test_arch/2.txt
echo "gfvfvvff" >> test_arch/3.txt
./prog8 test_arch txt

tar -tf archive.tar

~~~
Результат:

<img width="801" height="128" alt="Снимок экрана — 2026-10-01 в 15 34 58" src="https://github.com/user-attachments/assets/3516ce18-0a1d-4479-806c-01be48909089" />

## задание 9
~~~
nano prog7

#!/bin/bash
sed 's/    /\t/g' "$1" > "$2"


chmod +x prog9
nano input.txt


one    two
hello    world

./prog9 input.txt output.txt
cat -t output.txt
~~~
Результат:

<img width="751" height="84" alt="Снимок экрана — 2026-10-01 в 15 47 44" src="https://github.com/user-attachments/assets/5abce8c7-b0ee-4e00-be5c-c578bf99e7ea" />






