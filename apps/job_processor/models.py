from __future__ import absolute_import

import os
import datetime
import uuid
import hashlib
import platform
from multiprocessing import Process

import psutil

from django.db import models, IntegrityError, transaction
from django.db import close_connection
from django.contrib.contenttypes import generic
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.utils.simplejson import loads, dumps

from common.models import Singleton
from clustering.models import Node

from .literals import (JOB_STATE_CHOICES, JOB_STATE_PENDING,
    JOB_STATE_PROCESSING, JOB_STATE_ERROR, WORKER_STATE_CHOICES,
    WORKER_STATE_RUNNING, DEFAULT_JOB_QUEUE_POLL_INTERVAL,
    JOB_QUEUE_STATE_STOPPED, JOB_QUEUE_STATE_STARTED,
    JOB_QUEUE_STATE_CHOICES)
from .exceptions import (JobQueuePushError, JobQueueNoPendingJobs,
    JobQueueAlreadyStarted, JobQueueAlreadyStopped)

job_queue_labels = {}
job_types_registry = {}


class Job(object):
    def __init__(self, function, job_queue_item):
        # Run sync or launch async subprocess
        # OR launch 2 processes: monitor & actual process
        node = Node.objects.myself()
        worker = Worker.objects.create(node=node, pid=os.getpid(), job_queue_item=job_queue_item)
        try:
            transaction.commit_on_success(function)(**loads(job_queue_item.kwargs))
            #function(**loads(job_queue_item.kwargs))
        except Exception, exc:
            transaction.rollback()
            def set_state_error():
                job_queue_item.result = exc
                job_queue_item.state = JOB_STATE_ERROR
                job_queue_item.save()
            transaction.commit_on_success(set_state_error)()                
        else:
            job_queue_item.delete()
        finally:
            worker.delete()
            close_connection()


class JobType(object):
    def __init__(self, name, label, function):
        self.name = name
        self.label = label
        self.function = function
        job_types_registry[self.name] = self
        
    def __unicode__(self):
        return unicode(self.label)
       
    def run(self, job_queue_item, **kwargs):
        job_queue_item.state = JOB_STATE_PROCESSING
        job_queue_item.save()
        p = Process(target=Job, args=(self.function, job_queue_item,))
        p.start()


class JobQueueManager(models.Manager):
    def get_or_create(self, *args, **kwargs):
        job_queue_labels[kwargs.get('name')] = kwargs.get('defaults', {}).get('label')
        return super(JobQueueManager, self).get_or_create(*args, **kwargs)


class JobQueue(models.Model):
    # TODO: support for stopping and starting job queues
    # Internal name
    name = models.CharField(max_length=32, verbose_name=_(u'name'), unique=True)
    unique_jobs = models.BooleanField(verbose_name=_(u'unique jobs'), default=True)
    state = models.CharField(max_length=4,
        choices=JOB_QUEUE_STATE_CHOICES,
        default=JOB_QUEUE_STATE_STARTED,
        verbose_name=_(u'state'))
        
    objects = JobQueueManager()

    def __unicode__(self):
        return unicode(self.label) or self.names
        
    @property
    def label(self):
        return job_queue_labels.get(self.name)

    def push(self, job_type, **kwargs):  # TODO: add replace flag
        job_queue_item = JobQueueItem(job_queue=self, job_type=job_type.name, kwargs=dumps(kwargs))
        job_queue_item.save()
        return job_queue_item
        
    #def pull(self):
    #    queue_item_qs = JobQueueItem.objects.filter(queue=self).order_by('-creation_datetime')
    #    if queue_item_qs:
    #        queue_item = queue_item_qs[0]
    #        queue_item.delete()
    #        return loads(queue_item.data)

    def get_oldest_pending_job(self):
        try:
            return self.pending_jobs.all().order_by('-creation_datetime')[0]
        except IndexError:
            raise JobQueueNoPendingJobs

    @property
    def pending_jobs(self):
        return self.items.filter(state=JOB_STATE_PENDING)
    
    @property
    def error_jobs(self):
        return self.items.filter(state=JOB_STATE_ERROR)

    @property
    def active_jobs(self):
        return self.items.filter(state=JOB_STATE_PROCESSING)
        
    @property
    def items(self):
        return self.jobqueueitem_set
        
    def empty(self):
        self.items.all().delete()
        
    def save(self, *args, **kwargs):
        label = getattr(self, 'label', None)
        if label:
            job_queue_labels[self.name] = label
        return super(JobQueue, self).save(*args, **kwargs)

    def stop(self):
        if self.state == JOB_QUEUE_STATE_STOPPED:
            raise JobQueueAlreadyStopped
        
        self.state = JOB_QUEUE_STATE_STOPPED
        self.save()
    
    def start(self):
        if self.state == JOB_QUEUE_STATE_STARTED:
            raise JobQueueAlreadyStarted
        
        self.state = JOB_QUEUE_STATE_STARTED
        self.save()
        
    def is_running(self):
        return self.state == JOB_QUEUE_STATE_STARTED
        
    # TODO: custom runtime methods
        
    class Meta:
        verbose_name = _(u'job queue')
        verbose_name_plural = _(u'job queues')


class JobQueueItem(models.Model):
    # TODO: add re-queue
    job_queue = models.ForeignKey(JobQueue, verbose_name=_(u'job queue'))
    creation_datetime = models.DateTimeField(verbose_name=_(u'creation datetime'), editable=False)
    unique_id = models.CharField(blank=True, max_length=64, verbose_name=_(u'id'), unique=True, editable=False)
    job_type = models.CharField(max_length=32, verbose_name=_(u'job type'))
    kwargs = models.TextField(verbose_name=_(u'keyword arguments'))
    state = models.CharField(max_length=4,
        choices=JOB_STATE_CHOICES,
        default=JOB_STATE_PENDING,
        verbose_name=_(u'state'))
    result = models.TextField(blank=True, verbose_name=_(u'result'))
    
    def __unicode__(self):
        return self.unique_id
    
    def save(self, *args, **kwargs):
        self.creation_datetime = datetime.datetime.now()

        if self.job_queue.unique_jobs:
            self.unique_id = hashlib.sha256(u'%s-%s' % (self.job_type, self.kwargs)).hexdigest()
        else:
            self.unique_id = unicode(uuid.uuid4())
        try:
            super(JobQueueItem, self).save(*args, **kwargs)
        except IntegrityError:
            # TODO: Maybe replace instead of rasining exception w/ replace flag
            raise JobQueuePushError
            
    def get_job_type(self):
        return job_types_registry.get(self.job_type)
            
    def run(self):
        job_type_instance = self.get_job_type()
        job_type_instance.run(self)
        
    @property
    def worker(self):
        try:
            return self.worker_set.get()
        except Worker.DoesNotExist:
            return None
    
    class Meta:
        ordering = ('creation_datetime',)
        verbose_name = _(u'job queue item')
        verbose_name_plural = _(u'job queue items')
    

class Worker(models.Model):
    node = models.ForeignKey(Node, verbose_name=_(u'node'))
    pid = models.PositiveIntegerField(max_length=255, verbose_name=_(u'name'))
    creation_datetime = models.DateTimeField(verbose_name=_(u'creation datetime'), default=lambda: datetime.datetime.now(), editable=False)
    heartbeat = models.DateTimeField(blank=True, default=datetime.datetime.now(), verbose_name=_(u'heartbeat check'))
    state = models.CharField(max_length=4,
        choices=WORKER_STATE_CHOICES,
        default=WORKER_STATE_RUNNING,
        verbose_name=_(u'state'))
    job_queue_item = models.ForeignKey(JobQueueItem, verbose_name=_(u'job queue item'))

    def __unicode__(self):
        return u'%s-%s' % (self.node.hostname, self.pid)

    class Meta:
        ordering = ('creation_datetime',)
        verbose_name = _(u'worker')
        verbose_name_plural = _(u'workers')


class JobProcessingConfig(Singleton):
    job_queue_poll_interval = models.PositiveIntegerField(verbose_name=(u'job queue poll interval (in seconds)'), default=DEFAULT_JOB_QUEUE_POLL_INTERVAL)

    def __unicode__(self):
        return ugettext(u'Job queues configuration')

    class Meta:
        verbose_name = verbose_name_plural = _(u'job queues configuration')