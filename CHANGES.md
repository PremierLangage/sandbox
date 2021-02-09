# Changelog


## 3.0.3

* Expire date is now timezone-aware


## 3.0.2

* User in container is now 'student' instead of 'root'


## 3.0.1

* Use pycodestyle instead of pytest pep8 extension


## 3.0.0

* Changed structure of the json in response to `/specifications/` and `/libraries/` endpoints.
* Added `/usages/` endpoints.
* Now use Python 3.8
* Use a `queue.Queue` instead of a `list` to manage container. `Queue` being implemented in a
thread-safe way.
* Stress tests added
* Tests now done through Github Action.
* Fixed #48
