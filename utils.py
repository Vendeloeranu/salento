import codecs
import os
import collections
from six.moves import cPickle
import numpy as np

from salento import SalentoJsonParser

class DataLoader():
    def __init__(self, input_file, batch_size, seq_length):
        self.batch_size = batch_size
        self.seq_length = seq_length

        print("reading text file")
        self.preprocess(input_file)
        self.create_batches()
        self.reset_batch_pointer()

    def preprocess(self, input_file):
        with open(input_file, "r") as f:
            data, topics = SalentoJsonParser(f).as_tokens(start_end=True)
        counter = collections.Counter(data)
        count_pairs = sorted(counter.items(), key=lambda x: -x[1])
        self.chars, _ = zip(*count_pairs)
        self.vocab_size = len(self.chars)
        self.vocab = dict(zip(self.chars, range(len(self.chars))))
        self.tensor = np.array(list(map(self.vocab.get, data)))
        self.topics = np.array([np.array(t) for t in topics])
        self.ntopics = len(topics[0])

    def create_batches(self):
        self.num_batches = int(self.tensor.size / (self.batch_size *
                                                   self.seq_length))

        # When the data (tensor) is too small, let's give them a better error message
        if self.num_batches==0:
            assert False, "Not enough data. Make seq_length and batch_size small."

        self.tensor = self.tensor[:self.num_batches * self.batch_size * self.seq_length]
        self.topics = self.topics[:self.num_batches * self.batch_size * self.seq_length]
        xdata = self.tensor
        tdata = self.topics
        ydata = np.copy(self.tensor)
        ydata[:-1] = xdata[1:]
        ydata[-1] = xdata[0]
        self.x_batches = np.split(xdata.reshape(self.batch_size, -1), self.num_batches, 1)
        self.t_batches = np.split(tdata.reshape(self.batch_size, -1, self.ntopics), self.num_batches, 1)
        self.y_batches = np.split(ydata.reshape(self.batch_size, -1), self.num_batches, 1)


    def next_batch(self):
        x, t, y = [], [], self.y_batches[self.pointer]
        for i in range(self.seq_length):
            x.append(np.array([self.x_batches[self.pointer][batch][i] for batch in  
                range(self.batch_size)], dtype=np.int32))
            t.append(np.array([self.t_batches[self.pointer][batch][i] for batch in  
                range(self.batch_size)], dtype=np.float))
        self.pointer += 1
        return x, t, y

    def reset_batch_pointer(self):
        self.pointer = 0
