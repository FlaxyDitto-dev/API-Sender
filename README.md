# API-Sender
This is an API Sender, it can POST payloads to a specific API, like Fluxer, Ollama, Stable-difusion.cpp and more.

By running this Python app, you will be able to open it and post a request by typing it's URL(with the http:// or https://).

This is a web GUI app that runs localy on your machine(no sys req), you can post anything that the payload wants, for example, to generate an image of a golden retriever sitting on a yellow couch(with fluxer):

URL:
http://127.0.0.1:8000/generate

variable1: prompt = (prompt)
(you can add a variable like steps, height, width...)
then you press post request and then it will generate your image from fluxer.

this was just an example for using it for fluxer but it can be used for every place that you can post to and it supports sending a payload
