import json
import os
import re
import datetime
import hashlib

from . import redis, models, logger, app, db, db_engine, exif


tasks = {}

class TaskMeta(type):
    #def __new__(mcls, name, bases, attrs):
    #    print("__new__", mcls, name, bases, attrs)
    #    super(TaskMeta, mcls).__new__(name, bases, attrs)
    def __init__(self, name, bases, attrs):
        #print("__init__", self, name, bases, attrs)
        #super(TaskMeta, self).__init__(name, bases, attrs)
        if name != "Task":
            tasks[name] = self

    waiting_queue    = property(lambda cls: "%s-waiting"    % cls.queue_name)
    processing_queue = property(lambda cls: "%s-processing" % cls.queue_name)

class Task(object, metaclass=TaskMeta):
    priority = 0

    def __init__(self, *task_args):
        self.args = task_args

    @property
    def key(self):
        return json.dumps(self.args)

    def push(self):
        logger.debug("Pushed %s onto %s", self.key, self.__class__.waiting_queue)
        return redis.lpush(self.__class__.waiting_queue, self.key)

    @classmethod
    def pop(cls):
        obj = redis.rpoplpush(cls.waiting_queue, cls.processing_queue)
        if obj is not None:
            return cls(*json.loads(obj))
        
        return None

    @classmethod
    def queue(cls, *args):
        obj = cls(*args)
        obj.push()
        return obj.key
    
    def execute(self):
        #try:
        self.run()
        redis.lrem(self.__class__.processing_queue, -1, self.key)
        #except Exception:
        #    logger.exception("Exception occured in task")
        #    raise


class ThumbnailTask(Task):
    priority = -10
    queue_name = 'thumbnails'

    @property
    def file_id(self):
        return self.args[0]

    @property
    def sizes(self):
        return self.args[1]

    def run(self):
        file = models.File.query.get(self.file_id)
        source_file = file.path

        dest_files = []

        dest_files = [(size, file.get_path(size)) for size in self.sizes]
        dest_files = list(filter(lambda f: not os.path.exists(f[1]), dest_files))

        try:
            for size, file in dest_files:
                logger.info("Resizing size=%s dst=%50s src=%s", size, file, source_file)
            image_processing.create_thumbnails(source_file, 
                [(app.config["SIZES"][size][0:3], dest_file, ) for size, dest_file in dest_files]
            )
        except Exception as e:
            logger.exception("Exception while resizing photo")


class ScanFilesTask(Task):
    priority = 100
    queue_name = 'scanfiles'

    def search_for_images(self, root_path):
        extensions = [extension for x in models.FORMAT_EXTENSIONS for extension in x[1]]
        logger.debug("Looking for extensions: %s", str(extensions))
        for dirname, dirnames, filenames in os.walk(root_path):
            logger.debug("Searching directory %s", dirname)
            for d in dirnames[:]:
                for sd in app.config["SEARCH_EXCLUDE_DIRS"]:
                    if re.fullmatch(sd, os.path.join(dirname, d)) is not None:
                        logger.debug("Skipping directory %s", os.path.join(dirname, d))
                        dirnames.remove(d)
                        break

            for filename in filenames:
                for sf in app.config["SEARCH_EXCLUDE_FILES"]:
                    if re.fullmatch(sf, os.path.join(dirname, filename)) is not None:
                        logger.debug("Skipping file %s", os.path.join(dirname, filename))
                        break
                else:
                    if os.path.splitext(filename)[1].lower()[1:] in extensions:
                        yield os.path.join(dirname, filename)

    def run(self):
        for root in app.config["SEARCH_ROOTS"]:
            for file_path in self.search_for_images(root):
                ScanFileTask.queue(file_path, False)


class ScanFileTask(Task):
    priority = 90
    queue_name = 'scanfile'

    @property
    def file_path(self):
        return self.args[0]

    @property
    def force_hash_check(self):
        return self.args[1]

    def file_hash(self, file_path):
        with open(file_path, 'rb') as f:
            m = hashlib.sha512()
            m.update(f.read())
            return m.hexdigest()

    def run(self):
        logger.debug("Checking %s", self.file_path.encode('utf-8', 'replace').decode('utf-8'))

        stat = os.stat(self.file_path)

        adding_sfile  = False
        updated_props = False
        adding_file   = False

        with db.no_autoflush:
            source_file = models.SourceFile.query.filter(models.SourceFile.path == self.file_path).first()
            if source_file is None:
                source_file = models.SourceFile(path=self.file_path)
                adding_sfile = True

            owner = models.User.query.filter(models.User.system_uid == stat.st_uid).first()
            if owner is None:
                logger.warning("File %s owned by uid %d which is not present in user table", self.file_path, stat.st_uid)
                return

            for prop_name, val in [
                    ("owner",     owner),
                    ("device",    stat.st_dev),
                    ("inode",     stat.st_ino),
                    ("ctime",     datetime.datetime.fromtimestamp(stat.st_ctime)),
                    ("disk_size", stat.st_blocks * 512),
                    ("deleted",   False),
                ]:

                if getattr(source_file, prop_name) != val:
                    if not adding_sfile:
                        updated_props = True
                        logger.warning("File %d:%s property %s changed from %s to %s", 
                            source_file.id, 
                            source_file.path, prop_name, str(getattr(source_file, prop_name)), str(val)
                        )
                    setattr(source_file, prop_name, val)

            source_file.update_last_scan()

            new_hash = None
            if adding_sfile or self.force_hash_check:
                hash = self.file_hash(self.file_path)

                if not adding_sfile and source_file.file.hash != hash:
                    logger.error("File %s (id %d) hash changed from %s to %s", self.file_path, source_file.id, source_file.file.hash, hash)
                    new_hash = hash
                elif adding_sfile:
                    new_hash = hash

            if new_hash:
                file = models.File.query.filter(models.File.hash == new_hash).first()
                if file is None:
                    file = models.File(hash=new_hash, file_size=stat.st_size)
                    adding_file = True
                    db.add(file)
                source_file.file = file

            db.add(source_file)
            db.commit()

            adding_photo = False
            if new_hash or updated_props or adding_file:
                photo = models.Photo.query.filter(models.Photo.files.contains(file) & (models.Photo.owner == owner)).first()
                
                if photo is None:
                    photo = models.Photo(owner=owner, files=[source_file.file, ])
                    adding_photo = True
                    db.add(photo)
                    db.commit()
            else:
                photo = source_file.file.photos.filter(models.Photo.owner == owner).first()

            if adding_file:
                FileReadEXIFTask.queue(file.id)
            if adding_photo and not adding_file:
                PhotoCombineEXIFTask(photo.id)


#            # Let's try to attach file to an existing photo object or create a new one
#            try: 
#                photo = models.File.query.filter(models.File.hash == file.hash).filter(models.File.photo_id != None)[0].photo
#                file.photo = photo
#            except IndexError:
#                metadata = exif.PhotoExif(file.path)
#                try:
#                    photo = [f for f in models.File.query.filter(models.File.photo_id != None).filter(models.File.path.contains(drop_dir_ext(file.path))) if drop_dir_ext(f.path) == drop_dir_ext(file.path) and f.photo.date == metadata.date][0].photo
#                    file.photo = photo
#                except IndexError:
#                    photo = models.Photo(**metadata.get_dict())
#                    file.photo = photo
#                    db.add(photo)
#                except OSError:
#                    logger.exception("Skipping entry due to exception")
#        except KeyError as e:
#            logger.info("Refusing to scan file %s owned by user %d which is not present in users table", file_path, stat.st_uid)
#        except PermissionError as e:
#            logger.info("Refusing to scan file %s - permission error")


class FileReadEXIFTask(Task):
    priority = 50
    queue_name = 'filereadexif'

    @property
    def file_id(self):
        return self.args[0]

    def run(self):
        logger.info("Reading EXIF of file %d", self.file_id)
        file =  models.File.query.get(self.file_id)
        for source_file in file.source_files:
            metadata = exif.PhotoExif(source_file.path)
            break
        else:
            logger.error("Could not read any of File %d source files", file.id) 
            return

        for key, val in metadata.__dict__().items():
            setattr(file, key, val)
            
        db.add(file)
        db.commit()

        for photo in file.photos:
            PhotoCombineEXIFTask.queue(photo.id)


class PhotoCombineEXIFTask(Task):
    priority = 60
    queue_name = 'photocombineexif'

    @staticmethod
    def sort_key(x):
        try:
            return len(x)
        except TypeError:
            return x

    @property
    def photo_id(self):
        return self.args[0]

    def run(self):
        photo = models.Photo.query.get(self.photo_id)
        files = list(photo.files)

        for key in models.metadata.keys():
            if getattr(photo, "%s_changed" % key) is not None:
                # metadata property was manually updated so we won't overwrite it
                continue

            vals = sorted(set([v for v in [getattr(f, key) for f in files] if v is not None]), key=PhotoCombineEXIFTask.sort_key)
            # vals are sorted by length
            
            if len(vals) > 0: # 
                setattr(photo, key, vals[0])
            else:
                setattr(photo, key, None)

        db.add(photo)
        db.commit()


class PhotoAutoMergeTask(Task):
    priority = 200
    queue_name = 'photomerge'

    @property
    def photo_id(self):
        return self.args[0]

    def run(self):
        result = db_engine.execute("""
            SELECT photos.owner_id, photos.date, array_agg(photos.id), COUNT(*) as cnt 
            FROM photos 
            WHERE photos.date IS NOT NULL 
            GROUP BY photos.owner_id, photos.date 
            HAVING COUNT(*) > 1
        """)
        for candidates in result:
            photos = sorted([models.Photo.query.get(pid) for pid in candidates[2]], key=lambda x: 0 if x.changed is None else -1)

            print("Owner %3d Date %s" % (candidates[0], candidates[1]))
            for i, photo in enumerate(photos):
                print("  %1d: %10s %s " % (i, photo.files[0].hash[:10], ", ".join(photo.basenames)))

            for i in range(len(photos)):
                for j in range(i+1, len(photos)):
                    if photos[j].changed is not None:
                        continue

                    x = set(".".join(bn.split(".")[:-1]) for bn in photos[i].basenames) & set(".".join(bn.split(".")[:-1]) for bn in photos[j].basenames)
                    if len(x) > 0:
                        # same date and (base)-filename
                        assert photos[i].owner == photos[j].owner
                        assert photos[i].date  == photos[j].date
                        if photos[i].group is not None and photos[j].group is not None:
                            assert photos[i].group == photos[j].group
                        print("Combining %d and %d" % (i, j))
                        photos[i].merge(photos[j])
                        db.delete(photos[j])
                        db.commit()


            #pg = db.query(models.Photo, sa.fun
            #pg = models.Photo.query\
            #    .filter((models.Photo.deleted == False) & (models.Photo.date is not None))\
            #    .group_by(models.Photo.owner, models.Photo.date)


class GenerateArchiveTask(Task):
    priority = 20
    queue_name = 'genarchive'


