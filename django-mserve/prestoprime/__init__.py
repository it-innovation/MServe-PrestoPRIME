########################################################################
#
# University of Southampton IT Innovation Centre, 2012
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
#	Created Date :			2012-01-04
#	Created for Project :		PrestoPrime
#
########################################################################

task_descriptions = {}

task_descriptions['prestoprime.tasks.mxftechmdextractor'] = {
        "nbinputs" : 1,
        "nboutputs" : 1,
        "input-0" : { "mimetype" : "application/octet-stream" },
        "output-0" : { "mimetype" : "application/json"},
        "options":[],
        "results" : []
    }
task_descriptions['prestoprime.tasks.d10mxfchecksum'] =    {
        "nbinputs" : 1,
        "nboutputs" : 1,
        "input-0" : { "mimetype" : "application/octet-stream" },
        "output-0" : { "mimetype" : "text/plain"},
        "options":[],
        "results" : []
    }
task_descriptions['prestoprime.tasks.mxfframecount'] = {
        "nbinputs" : 1,
        "nboutputs" : 0,
        "input-0" : { "mimetype" : "application/octet-stream" },
        "options":[],
        "results" : ["lines"]
    }
task_descriptions['prestoprime.tasks.extractd10frame'] = {
        "nbinputs" : 1,
        "nboutputs" : 1,
        "input-0" : { "mimetype" : "application/octet-stream" },
        "output-0" : { "mimetype" : "image/png" },
        "options":['frame'],
        "results" : []
    }
task_descriptions['prestoprime.tasks.ffprobe'] = {
        "nbinputs" : 1,
        "nboutputs" : 1,
        "input-0" : { "mimetype" : "application/octet-stream" },
        "output-0" : { "mimetype" : "application/json" },
        "options":['format'],
        "results" : []
    }
task_descriptions['prestoprime.tasks.extractkeyframes'] = {
        "nbinputs" : 1,
        "nboutputs" : 1,
        "input-0" : { "mimetype" : "application/octet-stream" },
        "output-0" : { "mimetype" : "application/zip" },
        "options":['interval'],
        "results" : []
    }
task_descriptions['prestoprime.tasks.sha1'] = {
        "nbinputs" : 1,
        "nboutputs" : 0,
        "input-0" : { "mimetype" : "application/octet-stream" },
        "options":[],
        "results" : []
    }
task_descriptions['prestoprime.tasks.ffmpeg2theora'] = {
        "nbinputs" : 1,
        "nboutputs" : 1,
        "input-0" : { "mimetype" : "application/octet-stream" },
        "output-0" : { "mimetype" : "application/octet-stream" },
        "options":['args'],
        "results" : []
    }
task_descriptions['prestoprime.tasks.ffmbc'] = {
        "nbinputs" : 1,
        "nboutputs" : 1,
        "input-0" : { "mimetype" : "application/octet-stream" },
        "output-0" : { "mimetype" : "application/octet-stream" },
        "options":['args'],
        "results" : []
    }
task_descriptions['prestoprime.tasks.extractfragment'] = {
        "nbinputs" : 1,
        "nboutputs" : 1,
        "input-0" : { "mimetype" : "application/octet-stream" },
        "output-0" : { "mimetype" : "application/octet-stream" },
        "options":['intime','fragmentlength'],
        "results" : []
    }

import settings
if settings.PRESTOPRIME:
    from jobservice import *
    if 'task_descriptions' in task_descriptions:
        for k in struct.task_descriptions.keys():
            register_task_description(k, task_descriptions[k])
