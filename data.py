import os
import re
from string import punctuation

class Data():
    '''
        Import and parse data for training word-prediction

        Arguments:
            filepath: path to file

        Raises:
            FileNotFound
    '''
    def __init__(self, filepath):
        self.filepath = filepath
        if not os.path.isfile(self.filepath):
            raise FileNotFoundError('Could not find %s' % self.filepath)

        self.f = open(self.filepath, 'r', encoding='latin')

    def parse(self, column=2, min_sen_len=5, num_max=None):
        for line in self.f.readlines()[:num_max]:
            # convert to array; tab deliminated
            line = line.rstrip().split('\t')

            # get tweet from column
            text = line[column]

            #remove urls
            text = self.__remove_urls(text)

            # resolve hashtags and mentions's
            text = self.__remove_hashtags(text)
            text = self.__remove_mentions(text)

            # split text into sentances (not naive)
            sentences = self.__split_into_sentences(text, min_sen_len)

            # print(text)
            print(sentences)
            # print(repr(line))

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
        sentences = [s.strip(r'.|!|?').strip().replace(',','') for s in sentences if len(s.split()) >= min_sen_len]
        return sentences

    def __remove_urls(self, text):
        # source: https://stackoverflow.com/a/11332543
        return re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', text)

if __name__ == '__main__':
    data = Data(r'F:\Datasets\twitter_cikm_2010\training_set_tweets.txt').parse(min_sen_len=2, num_max=10)
