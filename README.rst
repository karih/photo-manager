Flask/Angular Photo Manager
===========================
This is an attempt at (self-hosted) browser based photo manager software.

This is built for people with a dislike for cloud based photo services and external hard drives, and allows you to store your photo collection on your own server, while using this site to browse, manage, process and publish your photos.

Server-side we use PostgreSQL to store data and Python(2.7)/Flask for web programming, while the front-end is built on AngularJS and Bootstrap. Probably elasticsearch will be involved at some point for better search and filtering capabilities. Moving to Python 3 should be done soon, assuming all libraries are available.

What currently works:

* Scan for photos (including raw) and browse file structure/photos. Essentially a remote photo file manager.

What should be possible:

* Identify the same photo, even if stored in multiple places and formats and group as one object.
* Allow various tagging and categorizing of these photo objects.
* Basic photo processing, such as resizing, cropping, unsharpening and applying curves.
* Sharing a photo directly online, both temporarily and permanently.
* Publishing photo albums from subset of photos.

and probably a lot more.

Prerequisites
-------------
Besides Python this software requires the following:

* PostgreSQL 
* ElasticSearch 
* ImageMagick
* UFRaw (https://en.wikipedia.org/wiki/UFRaw) for raw photo processing.

Probably you also want something like `nginx` running in front of the Python webserver.

ElasticSearch
~~~~~~~~~~~~~

* Download version of ElasticSearch from https://www.elastic.co/downloads/elasticsearch
* Go to your project folder and::
  
    mkdir -p es ${TMP_DIR}/es/{data,logs}
    tar -zxf ~/Downloads/elasticsearch-2.3.5.tar.gz -C es

* Change the path.data and path.logs to `${TMP_DIR}/es/{data,logs}`.
* Start it with::

    es/elasticsearch-2.3.5/bin/elasticsearch

Getting up and running
----------------------




Start by installing PostgreSQL and creating a database and user.

1. Create `pm/devconfig.py` from `pm/devconfig.py.sample`.
2. Install js/css dependencies::
    
    cd pm/static; bower install

3. Install Python dependencies::
     
    pip install -r requirements.pip

3. Install database tables::

    python manage.py resetdb

4. Scan for photos::

    python manage.py scan

5. Run development server::

    python manage.py run

6. Browse to http://127.0.0.1:8000 

Deploying to server
-------------------
Similar steps to above are required, some notable differences:

* The configuration file can be defined using the environment variable `PM_CONFIG`.
* nothing else?

In `sample_config` there are some sample configuration files for `systemd` and `nginx`, assuming you run flask through gunicorn. Also there is a rough deployment script in `deploy.sh`, that should be used as::
 
    ./deploy.sh user@server /srv/DOMAIN

Where `user@server` is directly passed to `ssh` and can therefore be replaced with an alias from `~/.ssh/config`.


