Flask/Angular Photo Manager
===========================
This is an attempt at (self-hosted) browser based photo manager software.

This is designed by (and for) people with a certain distaste for cloud based photo services and external hard drives, allowing you to store your photo collection on your own server, while using this site to browse, manage, process and publish your photos.

Server-side we use PostgreSQL and Elasticsearch to store data and Python3/Flask for web programming, while the front-end is built on AngularJS and Bootstrap.

What currently works:

* Scan for photos (including raw) and browse file structure/photos. Essentially a remote file manager supporting only photos.
* Identify the same photo, even if stored in multiple places and formats and group as one object (this can be improved considerably).

What should be possible:

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
* ImageMagick
* UFRaw (https://en.wikipedia.org/wiki/UFRaw) for raw photo processing.

Probably you also want something like ``nginx`` running in front of the Python webserver.

Getting up and running
----------------------

After installing the software dependencies listed above:

1. Install Python dependencies::
     
    pip install -r requirements.pip

2. Install js/css dependencies::
    
    cd pm/static; bower install

3. Create ``pm/devconfig.py`` overwriting defaults from ``pm/defaults.py`` as necessary.

4. Install database tables::

    python manage.py resetdb

5. Scan for photos and index (probably some of these will be combined)::

    python manage.py scan # scans for photos
    python manage.py assignphoto # groups image files into photo objects
    python manage.py guessphotoinfo # extracts photo information from files
    python manage.py reindex # index library with elasticsearch

6. Run development server::

    python manage.py run

6. Browse to http://127.0.0.1:8000 

Deploying to server
-------------------
Similar steps to above are required, some notable differences:

* The configuration file can be defined using the environment variable ``PM_CONFIG``.
* nothing else?

In ``sample_config/`` there are some sample configuration files for ``systemd`` and ``nginx``, assuming you run flask through gunicorn. Also there is a rough deployment script in ``deploy.sh``, that should be used as::
 
    ./deploy.sh user@server /srv/DOMAIN

Where ``user@server`` is directly passed to ``ssh`` and can therefore be replaced with an alias from ``~/.ssh/config``.
