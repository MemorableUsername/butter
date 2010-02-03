import random
import re
import sys

from hyphenate import hyphenate_word

class word(object):
    def __init__(self, text):
        self.syllables = hyphenate_word(text)

    def __getitem__(self, i):
        return self.syllables[i]

    def __setitem__(self, i, value):
        self.syllables[i] = value

    def __str__(self):
        return "".join(self.syllables)

    def __len__(self):
        return len(self.syllables)

class sentence(object):
    words_ex = re.compile(r'(\W+)')

    def __init__(self, text):
        self.words = sentence.words_ex.split(text)
        for i in range(0, len(self.words), 2):
            self.words[i] = word(self.words[i])

    def __getitem__(self, i):
        return self.words[i*2] # skip spaces

    def __len__(self):
        return (len(self.words)+1)/2

    def __str__(self):
        return "".join([str(i) for i in self.words])


class scorer(object):
    class score(object):
        def __init__(self, total, each):
            self.total = total
            self.each = each

        def __getitem__(self, i):
            return self.each[i]
    
        def __len__(self):
            return len(self.each)

        def __repr__(self):
            return '<%s, %s>' % (self.total, self.each)

    block_words = ['the', 'are', 'was', 'were', 'will', 'would', 'could', 
                   'should', 'can', 'does', 'doesn']
    block_sylls = ['ing']

    def __init__(self, sent):
        self.values = self._score_sentence(sent)

    def _score_sentence(self, sent):
        if len(sent) <= 1:
            return scorer.score(0, [])

        words = [self._score_word(sent, i) for i in range(len(sent))]
        score = reduce(lambda x, y: x+y.total, words, 0)
        return scorer.score(score, words)

    def _score_word(self, sent, i):
        if str(sent[i]) in self.block_words:
            return scorer.score(0, [])

        sylls = [self._score_syllable(sent, i, j) for j in range(len(sent[i]))]
        n = len(sent[i])

        score = sum(sylls) - (n-1)*n/2
        if i>0:
            prev = str(sent[i-1]).lower()
            if prev == 'the' or prev == 'a' or prev == 'an':
                score += 3

        return scorer.score(score, sylls)

    def _score_syllable(self, sent, i, j):
        s = sent[i][j].lower()
        if s in self.block_sylls: return 0
        lengths = [0, 0, 1, 2, 4, 2, 2, 1]
        score = lengths[min(len(s), len(lengths)-1)]

        if re.match(r'^[^aeiou][aeiouy]([^aeiouy])\1$', s):
            score += 8
        elif re.match(r'^[^aeiou][aeiouy][^aeiouy]+$', s):
            score += 2
        elif re.match(r'^[^aeiou][aeiouy][^aeiouy]', s):
            score += 1

        if s[0] == 'b':
            score += 2
        if s[-1] == 't':
            score += 1

        score += len(sent[i])-j-1 # earlier syllables are funnier
        return score

    def sentence(self):
        return self.values.total

    def word(self, i=None):
        if i is None:
            return [w.total for w in self.values]
        else:
            return self.values[i].total

    def syllable(self, i, j=None):
        if j is None:
            return self.values[i].each
        else:
            return self.values[i][j]

# TODO: lazify this
def population(weights):
    p = []
    for i in range(len(weights)):
        p.extend([i]*weights[i])
    return p

def buttify(text, scorer=scorer, rate=50):
    sent = sentence(text)
    score = scorer(sent)

    if score.sentence() == 0:
        raise Exception("unbuttable")

    count = score.sentence()/rate+1
    words = random.sample(population(score.word()), count)

    for i in words:
        buttify_word(sent, i, score.syllable(i))

    return str(sent)

def buttify_word(sent, i, score):
    j = random.choice(population(score))
    if sent[i][j].islower():
        sent[i][j] = 'butt'
    elif sent[i][j][0].isupper() and sent[i][j][1:].islower():
        sent[i][j] = 'Butt'
    else:
        sent[i][j] = 'BUTT'
    if i>0 and str(sent[i-1]).lower() == 'an':
        sent[i-1][0] = sent[i-1][0][0:1]

if __name__ == "__main__":
    import sys
    print buttify(sys.argv[1])
