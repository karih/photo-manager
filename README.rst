Flask/React Photo Library/Publishing Manager
============================================
This is an attempt at (self-hosted) browser based photo management software.

This is designed by (and for) people with a certain distaste for cloud based photo services and external hard drives, allowing you to store your photo collection on your own server, while using this site to browse, manage, process and publish your photos.

Server-side we use PostgreSQL, Elasticsearch and Redis to store data and Python3/Flask for web programming, while the front-end is built on React and Bootstrap.

What should eventually be possible:

* Allow various tagging and categorizing of these photo objects.
* Basic photo processing, such as resizing, cropping, unsharpening and applying curves.
* Sharing a photo directly online, both temporarily and permanently.
* Publishing photo albums from subset of photos.

and probably a lot more.

Prerequisites
-------------
Besides Python3 and the libraries specified in ``requirements.pip`` this software requires the following:

* PostgreSQL
* Elasticsearch
* Redis
* ImageMagick
* UFRaw (https://en.wikipedia.org/wiki/UFRaw) for raw photo processing.

Probably you also want something like ``nginx`` running in front of the Python webserver.

Getting up and running
----------------------

Refer to ``deploy.sh`` for somewhat up to date installation instructions.

Deploying to server
-------------------
* The configuration file can be defined using the environment variable ``PM_CONFIG``.
* nothing else?

In ``sample_config/`` there are some sample configuration files for ``systemd`` and ``nginx``, assuming you run flask through gunicorn. Also there is a rough deployment script in ``deploy.sh``, that should be used as::
 
    ./deploy.sh user@server /srv/DOMAIN

Where ``user@server`` is directly passed to ``ssh`` and can therefore be replaced with an alias from ``~/.ssh/config``.
