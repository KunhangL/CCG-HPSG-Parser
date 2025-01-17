import sys
import re
import torch
from typing import List, Dict

sys.path.append('..')
from data_loader import DataItem


DATA_MASK_PADDING = 0
TARGET_PADDING = -100


def pre_tokenize_sent(sent: str) -> List[str]:
    # This function is not very complete yet!!!
    splited = sent.split(' ')
    returned = list()
    for token in splited:
        if re.match('[a-zA-Z]', token[-1]):
            returned.append(token)
        elif token == 'Mr.' or token == 'Ms.':
            returned.append(token)
        else:
            returned.extend([token[0: -1], token[-1]])
    return returned


def get_cat_ids(
    categories: List[str],
    category2idx: Dict[str, int]
) -> List[int]:
    return [
        category2idx[category] if category in category2idx else TARGET_PADDING
        for category in categories
    ]


def prepare_data(
    data_items: List[DataItem],
    tokenizer,
    category2idx: Dict[str, int]
):
    """
    Output: wrapped data needed to input into the model
    """
    data = list()  # a list containing a list of input_ids for each sentence
    mask = list()  # a list containing the attention mask list for each sentence
    word_piece_tracked = list()  # a list containing the list of word_piece_tracked for each sentence
    target = list()  # a list containing the list of one-hot vectors for each sentence

    for data_item in data_items:
        pretokenized_sent = [token.contents for token in data_item.tokens]
        categories = [str(token.tag) for token in data_item.tokens]

        word_piece_tracked.append(
            [
                len(item)
                for item in tokenizer(pretokenized_sent, add_special_tokens=False).input_ids
            ]
        )

        inputs = tokenizer(
            pretokenized_sent,
            add_special_tokens=False,
            is_split_into_words=True
        )
        data.append(inputs.input_ids)
        mask.append(inputs.attention_mask)
        target.append(get_cat_ids(categories, category2idx))

    max_length = max(
        max([len(input_ids) for input_ids in data]),
        max([len(tgt) for tgt in target])
    )
    for i in range(len(data)):
        assert len(data[i]) == len(mask[i])
        data[i] = data[i] + [DATA_MASK_PADDING] * (max_length - len(data[i]))  # padding
        mask[i] = mask[i] + [DATA_MASK_PADDING] * (max_length - len(mask[i]))  # padding
    for i in range(len(target)):
        target[i] = target[i] + [TARGET_PADDING] * (max_length - len(target[i]))  # padding

    return {
        'input_ids': torch.LongTensor(data),
        'mask': torch.FloatTensor(mask),
        'word_piece_tracked': word_piece_tracked,
        'target': torch.LongTensor(target)
    }
