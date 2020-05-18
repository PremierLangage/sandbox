# Changelog

# 3.0.0

* Changed structure of the json in response to `/specifications/` and `/libraries/` endpoints.
* Added `/usages/` endpoints.
* Now use Python 3.8
* Use a `queue.Queue` instead of a `list` to manage container. `Queue` being implemented in a
thread-safe way.
* Stress tests added
* Tests now done through Github Action.
* Fixed #48
