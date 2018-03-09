import os
import re
from string import punctuation

class Data():
    '''
        Import and parse data for training word-prediction

        Arguments:
            filepath: path to file

        Raises:
            FileNotFoundError if filepath not found
    '''
    def __init__(self, filepath):
        self.filepath = filepath
        if not os.path.isfile(self.filepath):
            raise FileNotFoundError('Could not find %s' % self.filepath)

        self.f = open(self.filepath, 'r', encoding='latin')

        self.word_map = { '':0 } # 0 is null word
        self.char_map = { '':0 } # 0 is null char
        self.word_map_index = 1
        self.char_map_index = 1

    def parse(self, column=2, min_sen_len=5, num_max=None):
        sentances = []

        for line in self.f.readlines()[:num_max]:
            # convert to array; tab deliminated
            line = line.rstrip().split('\t')

            # get tweet from column
            try:
                text = line[column]
            except IndexError:
                continue
            #remove urls
            text = self.__remove_urls(text)

            # resolve hashtags and mentions
            text = self.__remove_hashtags(text)
            text = self.__remove_mentions(text)

            # split text into sentances (not naive)
            sentances.append(self.__split_into_sentences(text, min_sen_len))
        sentances = [item for sublist in sentances for item in sublist]
        return sentances

    def build_training_data(self, sentances, num_prev_words=2, char_token_len=None):
        '''
            Take in a list of sentances and return the training data required to train model.

            Arguments:
                sentances: list of sentances to train on

            Optional Arguments:
                num_prev_words (default: 2): context lookback distance, uses NULL if no word exists
                char_token_len (defualt: None): manually define the max character token length

        '''

        data = []
        expected_words = []

        if char_token_len == None:
            self.char_token_len = self.__get_max_char_token_len(sentances)
        else:
            self.char_token_len = char_token_len

        for s in sentances:
            split = s.split(' ')
            for i, word in enumerate(split):
                # assign id to word based on encounter
                try:
                    self.word_map[word]
                except:
                    self.word_map.update({ word:self.word_map_index })
                    self.word_map_index+=1

                prev_words = []
                # get indices of previous words and iterate through them to process them.
                for prev_index in [ i - j for j in reversed(range(1, num_prev_words + 1)) ]:
                    if prev_index < 0:
                        prev_words.append(self.word_map[''])
                    else:
                        prev_words.append(self.word_map[split[prev_index]])

                # skip trying to predict words that are too long.
                if len(word) >= self.char_token_len:
                    continue

                seqs = self.transform_event([prev_words, self.sequence(word)]) # generate training data sequences from word sequences.
                data += seqs # add new seqs to data
                expected_words += [self.word_map[word] for _ in range(len(seqs))] # populate enough words to match the number of sequences populated.

                # data.append([prev_words, self.sequence(word), self.word_map[word]])

        assert(len(self.word_map) == self.word_map_index) # make sure nothing went wrong with indexing words
        assert(len(data) == len(expected_words))

        # implicit data ordering
        return (data, expected_words)

    def transform_event(self, event):
        '''
            Intermediary function used to transform a word event into many training samples.

            Arguments:
                event: list of [prev_words, self.sequence(word)]

            Returns:
                List of structure: [[prev_words, seq1], [prev_words, seq2], ...]
        '''
        data = []
        for seq in event[1]:
            data.append([event[0], seq])
        return data

    def sequence(self, word, tokenize=True):
        ''' Return a list of all sequences of a word.

            > Data().sequence('hello', tokenize=False)
            ['', 'h', 'he', 'hel', 'hell', 'hello']

            > Data().sequence('hello', tokenize=True)
            [[0, 0, 0, ...], [5, 0, 0, 0], 'he', 'hel', 'hell', 'hello']
        '''

        if tokenize:
            a = [0 for _ in range(self.char_token_len)]
            l = [a.copy()]
            for i, c in enumerate(word):
                # assign id to character encounter
                try:
                    self.char_map[c]
                except:
                    self.char_map.update({ c:self.char_map_index })
                    self.char_map_index+=1
                try:
                    a[i] = self.char_map[c]
                except IndexError: # out of range (likely user defined max char len)
                    break
                l.append(a.copy())
        else:
            s = ''
            l = ['']
            for c in word:
                s += c
                l.append(s)

        return l

    def __get_max_char_token_len(self, sentances):
        m = 0
        mword = ''
        msen = ''
        for sentance in sentances:
            for word in sentance.split(' '):
                if len(word) > m:
                    msen = sentance
                    m = len(word)
                    mword = word

        return m

    def __remove_hashtags(self, text):
        return ' '.join(filter(lambda x:x[0]!='@', text.split()))

    def __remove_mentions(self, text):
        return ' '.join(filter(lambda x:x[0]!='#', text.split()))

    def __split_into_sentences(self, text, min_sen_len):
        # using this spliting algorithm becuase of the sheer amount of edge cases
        # credit: https://stackoverflow.com/a/31505798
        caps = "([A-Z])"
        prefixes = "(Mr|St|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|Mt)[.]"
        suffixes = "(Inc|Ltd|Jr|Sr|Co)"
        starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
        acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
        websites = "[.](com|net|org|io|gov|me|edu)"
        text = " " + text + "  "
        text = text.replace("\n"," ")
        text = re.sub(prefixes,"\\1<prd>",text)
        text = re.sub(websites,"<prd>\\1",text)
        if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
        text = re.sub("\s" + caps + "[.] "," \\1<prd> ",text)
        text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
        text = re.sub(caps + "[.]" + caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
        text = re.sub(caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>",text)
        text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
        text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
        text = re.sub(" " + caps + "[.]"," \\1<prd>",text)
        if "”" in text: text = text.replace(".”","”.")
        if "\"" in text: text = text.replace(".\"","\".")
        if "!" in text: text = text.replace("!\"","\"!")
        if "?" in text: text = text.replace("?\"","\"?")
        text = text.replace(".",".<stop>")
        text = text.replace("?","?<stop>")
        text = text.replace("!","!<stop>")
        text = text.replace("<prd>",".")
        sentences = text.split("<stop>")
        sentences = sentences[:-1]
        sentences = [re.sub(r'-|/|\\', ' ', s.strip(r'.|!|?').strip().replace(',','')) for s in sentences if len(s.split()) >= min_sen_len]
        return sentences

    def __remove_urls(self, text):
        # source: https://stackoverflow.com/a/11332543
        return re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', text)

if __name__ == '__main__':
    d = Data(r'F:\Datasets\twitter_cikm_2010\training_set_tweets.txt')
    sentances = d.parse(min_sen_len=2, num_max=10000)
    td = d.build_training_data(sentances, char_token_len=15)

    for i in range(len(td[0])):
        print(td[0][i], td[1][i])
