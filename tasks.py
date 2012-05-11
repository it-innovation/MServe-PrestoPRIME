########################################################################
#
# University of Southampton IT Innovation Centre, 2011
#
# Copyright in this library belongs to the University of Southampton
# University Road, Highfield, Southampton, UK, SO17 1BJ
#
# This software may not be used, sold, licensed, transferred, copied
# or reproduced in whole or in part in any manner or form or in or
# on any media by any person other than in accordance with the terms
# of the Licence Agreement supplied with the software, or otherwise
# without the prior written consent of the copyright owners.
#
# This software is distributed WITHOUT ANY WARRANTY, without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE, except where stated in the Licence Agreement supplied with
# the software.
#
#	Created By :			Mark McArdle
#	Created Date :			2011-03-25
#	Created for Project :		PrestoPrime
#
########################################################################
import os.path

from celery.task import task
import logging
import subprocess
import tempfile
import json
import hashlib
from subprocess import Popen, PIPE
from celery.task.sets import subtask
from cStringIO import StringIO
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.base import ContentFile
from dataservice.tasks import _get_mfile
from dataservice.tasks import _save_joboutput
from zipfile import ZipFile

@task
def mxftechmdextractor(inputs,outputs,options={},callbacks=[]):
    try:
        mfileid = inputs[0]

        inputfile = _get_mfile(mfileid)

        joboutput = outputs[0]

        logging.info("Processing mxftechmdextractor job on %s" % (inputfile))
        if not os.path.exists(inputfile):
            logging.info("Inputfile  %s does not exist" % (inputfile))
            return False

	tempout=tempfile.NamedTemporaryFile()
	logging.info("temp file: %s" % tempout.name)

        args = ["java -cp /opt/rai/mxftechmdextractor/mxftechmdextractor-last.jar eu.prestoprime.mxftools.test.JustRun",inputfile]
        cmd = " ".join(args)
        #p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, close_fds=True)
        p = Popen(cmd, shell=True, stdout=tempout, stderr=PIPE, close_fds=True)
	p.wait()
	if p.returncode != 0:
		raise Exception("Command %s exited with code %d. Stderr: %s" % (cmd, p.returncode, stderr))
	#(stdout, stderr) = p.communicate()
	#print("stdout"+stdout)
	#print("stderr"+stderr)
	#tempout.close()
	tempout.flush()

	import ConfigParser
	# ensure case is maintained
	config = ConfigParser.RawConfigParser()
	config.optionxform = str
	config.read(tempout.name)
	mxfinfo = dict(config.items("INFO"))
	print(mxfinfo)

        from jobservice.models import JobOutput
        jo = JobOutput.objects.get(id=joboutput)
        #jo.file.save('mxftechmdextractor.txt', ContentFile(p.stdout.read()), save=True)
        jo.file.save('mxftechmdextractor', ContentFile(json.dumps(mxfinfo,indent=4)), save=True)

        for callback in callbacks:
            subtask(callback).delay()

        return {"success":True,"message":"MXFTechMDExtractorPlugin successful"}
    except Exception as e:
        logging.info("Error with mxftechmdextractor. %s" % e)
        raise e
@task
def d10mxfchecksum(inputs,outputs,options={},callbacks=[]):
    try:
        mfileid = inputs[0]
        joboutput = outputs[0]

        inputfile = _get_mfile(mfileid)
        outputfile = tempfile.NamedTemporaryFile()

        logging.info("Processing d10mxfchecksum job on %s" % (inputfile))

        if not os.path.exists(inputfile):
            logging.info("Inputfile  %s does not exist" % (inputfile))
            return False

        args = ["d10sumchecker","-i",inputfile,"-o",outputfile.name]

        ret = subprocess.call(args)

        if ret != 0:
            raise Exception("d10mxfchecksum failed")

        outputfile.seek(0)
        suf = SimpleUploadedFile("mfile",outputfile.read(), content_type='text/plain')

        from jobservice.models import JobOutput
        jo = JobOutput.objects.get(id=joboutput)
        jo.file.save('d10mxfchecksum.txt', suf, save=True)

        for callback in callbacks:
            subtask(callback).delay()

        return {"success":True,"message":"d10mxfchecksum successful"}
    except Exception as e:
        logging.info("Error with d10mxfchecksum %s" % e)
        raise e
    
@task
def mxfframecount(inputs,outputs,options={},callbacks=[]):

    try:
        mfileid = inputs[0]

        inputfile = _get_mfile(mfileid)
        outputfile = tempfile.NamedTemporaryFile()
        logging.info("Processing mxfframecount job on %s" % (inputfile))

        if not os.path.exists(inputfile):
            logging.info("Inputfile  %s does not exist" % (inputfile))
            return False

        args = ["d10sumchecker","-i",inputfile,"-o",outputfile.name]
        logging.info(args)
        ret = subprocess.call(args)

        if ret != 0:
            raise Exception("mxfframecount failed")

        frames = 0
        for line in open(outputfile.name):
            frames += 1

        # TODO: subtract 1 for additional output
        frames = frames -1

        import dataservice.usage_store as usage_store
        usage_store.record(mfileid,"http://prestoprime/mxf_frames_ingested",frames)

        for callback in callbacks:
            subtask(callback).delay()

        return {"success":True,"message":"mxfframecount successful", "frames": frames }
    except Exception as e:
        logging.info("Error with mxfframecount %s" % e)
        raise e

@task(max_retries=3)
def extractd10frame(inputs,outputs,options={},callbacks=[],**kwargs):
    try:
        mfileid = inputs[0]

        inputfile = _get_mfile(mfileid)
        joboutput = outputs[0]
        frame = str(options['frame'])

        logging.info("Processing extractd10frame job on %s" % (inputfile))
        if not os.path.exists(inputfile):
            logging.info("Inputfile  %s does not exist" % (inputfile))
            return False

        import pyffmpeg

        stream = pyffmpeg.VideoStream()
        stream.open(inputfile)
        image = stream.GetFrameNo(frame)

        # Save the thumbnail
        temp_handle = StringIO()
        image.save(temp_handle, 'png')
        temp_handle.seek(0)

        # Save to the thumbnail field
        suf = SimpleUploadedFile("mfile",temp_handle.read(), content_type='image/png')

        from jobservice.models import JobOutput
        jo = JobOutput.objects.get(id=joboutput.pk)
        jo.file.save('extractd10frame.png', suf , save=False)
        jo.save()

        for callback in callbacks:
                subtask(callback).delay()

        return {"success":True,"message":"extractd10frame successful"}
    except Exception as e:
        logging.info("Error with extractd10frame %s" % e)
        raise e

@task
def ffprobe(inputs,outputs,options={},callbacks=[]):
    try:
        mfileid = inputs[0]

        inputfile = _get_mfile(mfileid)
        joboutput = outputs[0]
        
	logging.info("Processing ffprobe job on %s" % (inputfile))
        if not os.path.exists(inputfile):
            logging.info("Inputfile  %s does not exist" % (inputfile))
            return False

	print_format=options["format"]
	if print_format not in ["default","compact","csv","json","xml"]:
		print_format="json"

	# Requires ffprobe >=0.9
        args = ["ffprobe -v quiet -print_format",print_format,"-show_format -show_streams",inputfile]
        cmd = " ".join(args)
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, close_fds=True)

	# communicate() is preferred to stdout.read()
	(stdout, stderr) = p.communicate()

	if p.returncode != 0:
		raise Exception("Command %s exited with code %d. Stderr: %s" % (cmd, p.returncode, stderr))

        from jobservice.models import JobOutput
        jo = JobOutput.objects.get(id=joboutput)
        jo.file.save('ffprobe.txt', ContentFile(stdout), save=True)
	#(stdout, stderr) = p.communicate()
	#print(stdout)
	#print(stderr)
	#ffprobe_output = json.loads(stdout)	
	#ret = {"success":True}
	#ret["ffprobe"] = ffprobe_output

        for callback in callbacks:
            subtask(callback).delay()

        return {"success":True, "message":"ffprobe successful"}
    except Exception as e:
        logging.info("Error with ffprobe. %s" % e)
        raise e

def zipdir(dir, zipfile):
	files = os.listdir(dir)
        z = ZipFile(zipfile, "w")
        for f in files:
                if os.path.isfile(dir+'/'+f):
                        print('zipping '+dir+'/'+f)
                        z.write(dir+'/'+f, f)
        z.close()
	return z

@task
def extractkeyframes(inputs,outputs,options={},callbacks=[]):
    try:
	mfileid=inputs[0]
	videopath=_get_mfile(mfileid)

	tempdir = tempfile.mkdtemp()
	logging.info("temp dir: %s" % (tempdir))

	interval = options['interval']

	# extract all I frames that are no closer than 'interval'  seconds apart
	ffmpeg_args = "-vf select='eq(pict_type\,I)*(isnan(prev_selected_t)+gte(t-prev_selected_t\,%s))' -vsync 0 -f image2" % (interval)
        args = ["ffmpeg -i",videopath, ffmpeg_args, tempdir+"/%09d.jpg"]
	cmd = " ".join(args)
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, close_fds=True)
	(stdout,stderr) = p.communicate()
	logging.info(stdout)

	if p.returncode != 0:
		raise Exception("Command %s exited with code %d. Stderr: %s" % (cmd, p.returncode, stderr))

	results_file = tempdir+"/results.zip"
	zipdir(tempdir, results_file)			

	results = open(results_file, 'r')
        # make job outputs available
        _save_joboutput(outputs[0], results)
        results.close()

        for callback in callbacks:
            subtask(callback).delay()

        return {"success":True, "message":"keyframe extraction successful"}
    except Exception as e:
        logging.info("Error with keyframe extraction %s" % e)
        raise e


@task(name="prestoprime.tasks.sha1",default_retry_delay=15,max_retries=3)
def sha1file(inputs,outputs,options={},callbacks=[]):

    """Return hex sha1 digest for a Django FieldFile"""
    try:
        mfileid = inputs[0]
        path = _get_mfile(mfileid)
        file = open(path,'r')
        sha1 = hashlib.sha1()
        while True:
            data = file.read(8192)  # multiple of 128 bytes is best
            if not data:
                break
            sha1.update(data)
        file.close()
        sha1string = sha1.hexdigest()
        logging.info("SHA1 calculated %s" % (sha1string))

	# TODO: move to dataservice and store checksum in file?
        #from dataservice.models import MFile
        #_mf = MFile.objects.get(id=mfileid)
        #_mf.checksum = md5string
        #_mf.save()

        for callback in callbacks:
            logging.info("Running Callback %s" % callback)
            subtask(callback).delay()

        return {"success":True,"message":"SHA1 successful", "sha1" : sha1string}
    except Exception, e:
        logging.info("Error with sha1 %s" % e)
        raise e

@task(name="prestoprime.tasks.ffmpeg2theora")
def ffmpeg2theora(inputs,outputs,options={},callbacks=[]):
    try:
	mfileid=inputs[0]
	videopath=_get_mfile(mfileid)

	tempout=tempfile.NamedTemporaryFile()
	logging.info("temp file: %s" % tempout.name)

	ffmpeg_args=options["args"]

	# extract all I frames that are no closer than 5 seconds apart
	args = ["ffmpeg2theora -i",videopath,ffmpeg_args,"-o", tempout.name]
	cmd = " ".join(args)
	logging.info(cmd)
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, close_fds=True)
	(stdout,stderr) = p.communicate()
	logging.info(stdout)

	if p.returncode != 0:
		raise Exception("Command %s exited with code %d. Stderr: %s" % (cmd, p.returncode, stderr))

        # make job outputs available
        _save_joboutput(outputs[0], tempout)

        for callback in callbacks:
            subtask(callback).delay()

        return {"success":True, "message":"ffmpeg2theora successful"}
    except Exception as e:
        logging.info("Error with ffmpeg2theora. %s" % e)
        raise e

@task(name="prestoprime.tasks.ffmbc")
def ffmbc(inputs,outputs,options={},callbacks=[]):
    try:
	mfileid=inputs[0]
	videopath=_get_mfile(mfileid)

	tempout=tempfile.NamedTemporaryFile()
	logging.info("temp file: %s" % tempout.name)

	ffmpeg_args=options["args"]

	# extract all I frames that are no closer than 5 seconds apart
	args = ["ffmbc -y -i",videopath,ffmpeg_args,tempout.name]
	cmd = " ".join(args)
	logging.info(cmd)
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, close_fds=True)
	(stdout,stderr) = p.communicate()
	logging.info(stdout)

	if p.returncode != 0:
		raise Exception("Command %s exited with code %d. Stderr: %s" % (cmd, p.returncode, stderr))

        # make job outputs available
        _save_joboutput(outputs[0], tempout)

        for callback in callbacks:
            subtask(callback).delay()

        return {"success":True, "message":"ffmbc successful"}
    except Exception as e:
        logging.info("Error with ffmbc %s." % e)
        raise e

@task
def extractfragment(inputs,outputs,options={},callbacks=[]):
    try:
	mfileid=inputs[0]
	videopath=_get_mfile(mfileid)

	tempout=tempfile.NamedTemporaryFile(suffix=".mp4")
	logging.info("temp file: %s" % tempout.name)

	intime=options["intime"]
	fragmentlength=options["fragmentlength"]

	# extract 'fragmentlength' video fragment starting at 'intime' (seconds)
	# ffmpeg -ss 00:00:30.0 -t 00:00:10.0 -i input.wmv -acodec copy -vcodec copy -async 1 output.wmv
	args = ["ffmpeg -y -ss",intime,"-t",fragmentlength,"-i",videopath,"-acodec copy -vcodec copy -async 1",tempout.name]
	cmd = " ".join(args)
	logging.info(cmd)
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE, close_fds=True)
	(stdout,stderr) = p.communicate()
	logging.info(stdout)

	if p.returncode != 0:
		raise Exception("Command %s exited with code %d. Stderr: %s" % (cmd, p.returncode, stderr))

        # make job outputs available
        _save_joboutput(outputs[0], tempout)

        for callback in callbacks:
            subtask(callback).delay()

        return {"success":True, "message":"extractfragment successful"}
    except Exception as e:
        logging.info("Error with extractfragment %s." % e)
        raise e

