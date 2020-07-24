# docker
install docker desktop
```
docker image ls
docker container ls
docker attach bc763d80c0cb
docker run -it ubuntu:16.04
commit 14531712568a ubuntu:16.04
```
https://www.youtube.com/watch?v=KaSJMDo-aPs&list=PLEsfXFp6DpzTHpw-kUzOd9WWY0zVdzl6q


# To run phpmyadmin
```
service mysql start
service apache2 start
```
execute docker run
```
docker run -p 8000:8000 -it fd6e22eee6a9
```
then, you can externally access phpmyadmin service to access mysql database

# run multiple service
Use multiple ```-p``` options, for example ```:80``` is for myphpadmin service, ```-8000` is for django service
```
docker run -p 8008:80 -p 8000:8000 -it fd6e22eee6a9
```
