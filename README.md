# OneClick Demo

A repository for demo purposes of the [OneClick](https://github.com/janlauber/one-click) project.


```bash
docker run --name mysql-fitness-tracker -e MYSQL_ROOT_PASSWORD=my-secret-pw -e MYSQL_DATABASE=fitness_tracker -e MYSQL_USER=user -e MYSQL_PASSWORD=password -p 3306:3306 -d mysql:latest
```