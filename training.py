# Mute tensorflow debugging information console
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from keras.layers import LSTM, GRU, Flatten, Input, concatenate, Embedding, Bidirectional, Dense
from keras.models import Sequential, save_model, Model
from keras.utils import np_utils

import numpy as np

from data import Data


def build_model(x_train, y_train, max_char_token, max_word_token, depth=10):
    # size parameters
    context_len = len(x_train[0][0])
    seq_len = len(x_train[0][1])
    nb_classes = max(y_train) + 1
    # nb_classes = max(y_train)[0]

    context_input = Input(shape=(context_len,), name='context_input')
    context_emb = Embedding(output_dim=512, input_dim=max_word_token, input_length=context_len)(context_input)

    char_seq_input = Input(shape=(seq_len,), name='char_seq_input')
    char_emb = Embedding(output_dim=512, input_dim=max_char_token, input_length=seq_len)(char_seq_input)


    # model.compile(loss='categorical_crossentropy',
    #               optimizer='adadelta',
    #               metrics=['accuracy'])


    merge = concatenate([char_emb, context_emb], axis=1)
    lstm_out = LSTM(2048, activation='tanh', recurrent_dropout=0.2)(merge)
    output = Dense(nb_classes, activation='softmax', name='output')(lstm_out)

    model = Model(inputs=[context_input, char_seq_input], outputs=[output])

    model.compile(loss='categorical_crossentropy',
                  optimizer='adadelta',
                  metrics=['accuracy'])

    # format data for training
    cont_train = np.array([event[0] for event in x_train])
    char_train = np.array([event[1] for event in x_train])
    y_train = np_utils.to_categorical(y_train, nb_classes) # convert classes to binary categorical vectors

    model.fit({'context_input': cont_train, 'char_seq_input': char_train},
              {'output': y_train}, epochs=50, batch_size=32)



if __name__ == '__main__':
    d = Data(r'F:\Datasets\twitter_cikm_2010\training_set_tweets.txt')
    sentances = d.parse(min_sen_len=2, num_max=100)
    td,ew = d.build_training_data(sentances, char_token_len=15)

    model = build_model(td, ew, max_char_token=max(d.char_map.values()), max_word_token=max(d.word_map.values()))
