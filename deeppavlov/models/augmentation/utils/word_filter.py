from abc import abstractmethod
from typing import List
from numpy.random import sample
from itertools import repeat
from deeppavlov.models.augmentation.utils.inflection import RuInflector
from deeppavlov.models.augmentation.utils.inflection import EnInflector


class WordFilter(object):
    """Class that decides which tokens should not be replaced

    Args:
        replace_freq: [0, 1] propability of token that passed thought other filters to be replaced
        isalpha_only: filter based on string method 'isalpha'
        not_replaced_tokens: List of tokens that shouldn't be replaced

    Attributes:
        replace_freq: [0, 1] propability of token that passed thought other filters to be replaced
        isalpha_only: filter based on string method 'isalpha'
        not_replaced_tokens: List of tokens that shouldn't be replaced
    """

    def __init__(self,
                 replace_freq: float,
                 isalpha_only: bool,
                 not_replaced_tokens: List[str] = []):
        self.replace_freq = replace_freq
        self.isalpha_only = isalpha_only
        self.not_replaced_tokens = not_replaced_tokens

    def filter_isalpha_only(self, tokens):
        if self.isalpha_only:
            return map(lambda x: x.isalpha(), tokens)
        else:
            return repeat(True, len(tokens))

    @abstractmethod
    def filter_not_replaced_token(self, tokens: List[str]):
        """
        It filters tokens based on self.not_replaced_tokens attribute
        Args:
            tokens: tokens that will be filtered
        Returns:
            filter's decides
        """
        raise NotImplementedError("Your wordfilter must implement the abstract method filter_not_replaced_token.")

    @abstractmethod
    def filter_based_on_pos_tag(self, tokens, pos_tags):
        """
        It filters tokens based on self.not_replaced_tokens attribute
        Args:
            tokens: tokens that will be filtered
            pos_tags: pos tags of tokens
        Returns:
            filter's decides
        """
        raise NotImplementedError("Your wordfilter must implement the abstract method filter_based_on_pos_tag.")

    def filter_united(self, tokens, morpho_tags) -> List[bool]:
        return list(map(lambda x, y, z: all([x, y, z]),
                        self.filter_based_on_pos_tag(morpho_tags),
                        self.filter_not_replaced_token(tokens, morpho_tags),
                        self.filter_isalpha_only(tokens)))

    def filter_frequence(self, prev_decision: List[bool]) -> List[bool]:
        return map(lambda x: sample() < self.replace_freq if x else x, prev_decision)

    def filter_words(self, tokens, moprho_tags):
        """It filters tokens bases on replace_freq, isalpha_only, not_replaced_token and pos_tags of tokens
        Args:
            tokens: tokens that will be filtered
        Return:
            List of boolean values,
            'False' for tokens that should not be replaced,
            'True' for tokens that can be replaced
        """
        filtered = self.filter_united(tokens, moprho_tags)
        return list(self.filter_frequence(filtered))


class EnWordFilter(WordFilter):
    """Class that decides which tokens should not be replaced, for english language

    Args:
        replace_freq: [0, 1] propability of token that have been passed thought other filters to be replaced
        isalpha_only: filter based on string method 'isalpha'
        not_replaced_tokens: List of tokens that shouldn't be replaced
        replaced_pos_tags: List of pos_tags that can be replaced,
                           e.g. 'NOUN' for Noun, 'VERB' for Verb, 'ADJ' for Adjective, 'ADV' for Adverb

    Attributes:
        replace_freq: [0, 1] propability of token that have been passed thought other filters to be replaced
        isalpha_only: filter based on string method 'isalpha'
        not_replaced_tokens: List of tokens that shouldn't be replaced
        replaced_pos_tags: List of pos_tags that can be replaced,
                           e.g. 'NOUN' for Noun, 'VERB' for Verb, 'ADJ' for Adjective, 'ADV' for Adverb
    """

    def __init__(self,
                 replace_freq: float,
                 isalpha_only: bool,
                 not_replaced_tokens: List[str] = [],
                 replaced_pos_tags: List[str] = ['ADJ', 'ADV', 'NOUN', 'VERB']):
        super(EnWordFilter, self).__init__(replace_freq, isalpha_only, not_replaced_tokens)
        self.replaced_pos_tags = replaced_pos_tags
        self.inflector = EnInflector()

    def filter_not_replaced_token(self, tokens, morpho_tags):
        return map(lambda token, morpho_tag:
                   self.inflector.lemmatize(token, morpho_tag) not in self.not_replaced_tokens,
                   tokens,
                   morpho_tags)

    def filter_based_on_pos_tag(self, morpho_tags):
        """Function that filters tokens with pos_tags and rules
        Args:
            morpho_tags: morpho tags in UD2.0 format of filtered tokens
                         e.g. {'source_token': 'luck', 'pos_tag': 'NOUN', 'features' {'Number': 'Sing'}}
        Return:
            List of boolean values,
            'False' for tokens that should not be replaced,
            'True' for tokens that can be replaced
        """
        prev_morpho_tag = None
        result = []
        for morpho_tag in morpho_tags:
            if prev_morpho_tag and\
                    prev_morpho_tag['pos_tag'] == 'PRON' and\
                    prev_morpho_tag['source_token'].lower() == 'there' and\
                    self.inflector.lemmatize(morpho_tag['source_token'], morpho_tag) == 'be':
                result.append(False)
                prev_morpho_tag = morpho_tag
            else:
                result.append(morpho_tag['pos_tag'] in self.replaced_pos_tags)
                prev_morpho_tag = morpho_tag
        return result


class RuWordFilter(WordFilter):
    """Class that decides which tokens should not be replaced, for russian language

    Args:
        replace_freq: [0, 1] propability of token that have been passed thought other filters to be replaced
        isalpha_only: filter based on string method 'isalpha'
        not_replaced_tokens: List of tokens that shouldn't be replaced
        replaced_pos_tags: List of pos_tags that can be replaced,
                           e.g. 'NOUN' for Noun, 'VERB' for Verb,
                           'ADJ' for Adjective, 'ADV' for Adverb, 'NUM' for Numerical

    Attributes:
        replace_freq: [0, 1] propability of token that have been passed thought other filters to be replaced
        isalpha_only: filter based on string method 'isalpha'
        not_replaced_tokens: List of tokens that shouldn't be replaced
        replaced_pos_tags: List of pos_tags that can be replaced,
                           e.g. 'NOUN' for Noun, 'VERB' for Verb,
                           'ADJ' for Adjective, 'ADV' for Adverb, 'NUM' for Numerical
        is_replace_numeral_adjective: to replace numeral adjective or not, based on pos_tag
    """

    def __init__(self,
                 replace_freq: float,
                 isalpha_only: bool,
                 not_replaced_tokens: List[str] = ['иметь', 'обладать', 'любить', 'нравиться'],
                 replaced_pos_tags: List[str] = ['ADJ', 'ADV', 'NOUN', 'VERB', 'NUM']):
        super(RuWordFilter, self).__init__(replace_freq, isalpha_only, not_replaced_tokens)
        self.replaced_pos_tags = replaced_pos_tags
        self.inflector = RuInflector()

    def filter_not_replaced_token(self, tokens, morpho_tags):
        return map(lambda x, y:
                   self.inflector.lemmatize(x, y) not in self.not_replaced_tokens,
                   tokens,
                   morpho_tags)

    def filter_based_on_pos_tag(self, morpho_tags):
        """Function that filters tokens with pos_tags and rules
        Args:
            morpho_tags: morpho tags in UD2.0 format of filtered tokens
                         e.g. {'source_token': 'удачи',
                               'pos_tag': 'NOUN'
                               'features': {'Animacy':'Inan', 'Case':'Acc', 'Gender':'Fem', 'Number': 'Plur'}}
        Return:
            List of boolean values,
            'False' for tokens that should not be replaced,
            'True' for tokens that can be replaced
        """
        return list(map(lambda x: x['pos_tag'] in self.replaced_pos_tags, morpho_tags))