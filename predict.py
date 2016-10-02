import tensorflow as tf

import argparse
import os
import ast
from six.moves import cPickle

from model import Model
from salento import START

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--save_dir', type=str, default='save',
                       help='model directory to store checkpointed models')
    parser.add_argument('--topk', type=int, default=5,
                       help='print top-k values in distribution')
    parser.add_argument('--topic', type=str, default=None, required=True,
                       help='topic distribution as a Python list')
    parser.add_argument('--prime', default=START,
                       help='prime trace (default is START)')

    args = parser.parse_args()
    predict(args)

def predict(args):
    with open(os.path.join(args.save_dir, 'config.pkl'), 'rb') as f:
        saved_args = cPickle.load(f)
    with open(os.path.join(args.save_dir, 'chars_vocab.pkl'), 'rb') as f:
        chars, vocab = cPickle.load(f)
    model = Model(saved_args, True)
    topic = ast.literal_eval(args.topic)
    with tf.Session() as sess:
        tf.initialize_all_variables().run()
        saver = tf.train.Saver(tf.all_variables())
        ckpt = tf.train.get_checkpoint_state(args.save_dir)
        if ckpt and ckpt.model_checkpoint_path:
            saver.restore(sess, ckpt.model_checkpoint_path)
            dist, prediction = model.predict(sess, args.prime.split(';'), topic, chars, vocab)
            dist = [(chars[i], prob) for i, prob in enumerate(dist)]

            for node, prob in sorted(dist, key=lambda x:x[1], reverse=True)[:args.topk]:
                print('{:.2f} : {}'.format(prob, node))
            print('prediction : {}'.format(prediction))

if __name__ == '__main__':
    main()
