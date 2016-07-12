#!/usr/bin/env python

import sys,math,numpy, scipy, scipy.ndimage, itertools
import threading, Queue, multiprocessing

def mytest(input2=None, **args):
    print "MYTEST:", input2, args

class filter_thread( threading.Thread ):

    def __init__(self, fct, data, output, queue, **kwargs):
        self.kwargs = kwargs
        self.fct = fct
        self.data = data
        self.queue = queue
        self.output = output
        #print type(kwargs)
        #print kwargs
        threading.Thread.__init__(self)

    def run(self):
        while (not self.queue.empty()):
            try:
                block = self.queue.get_nowait()
                #print block

                _out, _in = block
                #print _out, _in
                #print self.args

                _input = self.data[_in[0]:_in[1], _in[2]:_in[3]]

                full_args = self.kwargs.copy()
                full_args['input'] = _input
                #print full_args

                #_output = self.fct(**full_args) #input=_input,
                _output = self.fct(input=_input, **self.kwargs) #input=_input,
                #print _output.shape

                self.output[_out[0]:_out[1], _out[2]:_out[3]] = \
                    _output[(_out[0]-_in[0]):(_out[1]-_out[0]+_out[0]-_in[0]),
                            (_out[2]-_in[2]):(_out[3]-_out[2]+_out[2]-_in[2])]
                    #_output[_in[0]-_out[0]:_in[1]-_out[1], _in[2]-_out[2]:_in[3]-_out[3]]

            except Queue.Empty:
                break

def parallel_filter(fct, data, overlap, nchunks=100, ncpus=0, **kwargs):

    # find the gridding to use
    n_xy = int(math.ceil(math.sqrt(nchunks)))
    #print n_xy

    chunksize = numpy.ceil(numpy.array(data.shape, dtype=numpy.float) / n_xy).astype(numpy.int)
    #print chunksize, data.shape

    work_queue = Queue.Queue()

    for ix,iy in itertools.product(range(n_xy), repeat=2):

        # compute the area for the output - excluding any overlap regions
        data_x1 = ix*chunksize[0]
        data_x2 = data_x1 + chunksize[0]
        if (data_x2 >= data.shape[0]): data_x2 = data.shape[0]

        data_y1 = iy*chunksize[1]
        data_y2 = data_y1+chunksize[1]
        if (data_y2 >= data.shape[1]): data_y2 = data.shape[1]

        # now compute the area including overhead to allow for proper filtering
        in_x1 = numpy.max([(data_x1 - overlap), 0])
        in_x2 = numpy.min([(data_x2 + overlap), data.shape[0]])
        in_y1 = numpy.max([(data_y1 - overlap), 0])
        in_y2 = numpy.min([(data_y2 + overlap), data.shape[1]])

        #print ix,iy,data_x1,data_x2,data_y1,data_y2,"-->", in_x1,in_x2,in_y1,in_y2

        work_queue.put(([data_x1,data_x2,data_y1,data_y2], [in_x1,in_x2,in_y1,in_y2]))

    #
    # Now we have all work put in the work queue, prepare work for execution
    #
    output = numpy.zeros_like(data)

    if (ncpus <= 0):
        ncpus = multiprocessing.cpu_count()

    print("Starting parallel work, %d chunks of %d x %d, using %d threads" % (
        n_xy*n_xy, chunksize[1], chunksize[0], ncpus)
    )

    # start all worker threads
    workers = []
    for cpu in range(ncpus):
        w = filter_thread(fct=fct, data=data, output=output, queue=work_queue, **kwargs)
        w.daemon = True
        workers.append(w)
        w.start()

    # and wait until all work is done
    for i,worker in enumerate(workers):
        worker.join()
        #print "one worker (%d / %d) done" % (i+1, len(workers))

    #print chunksize, data.shape
    return output

if __name__ == "__main__":

    import pyfits

    fn = sys.argv[1]
    hdu = pyfits.open(fn)
    data = hdu[0].data

    output = parallel_filter(
        fct=scipy.ndimage.filters.gaussian_filter,
        #fct=mytest,
        data=data,
        overlap=20,
        nchunks=100,
        ncpus=-1,
        #
        sigma=5,
        truncate=4,
    )

    hdu[0].data = output
    hdu.writeto("xxx.out.fits", clobber=True)
    print "all done!"
    #scipy.ndimage.filters.gaussian_filter(input=data, sigma=5)


