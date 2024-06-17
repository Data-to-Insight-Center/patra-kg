from transformers import AutoTokenizer, AutoModel
import torch
from rouge import Rouge
from bert_score import score as bertscore
from gensim.models import KeyedVectors
import numpy as np
from sentence_transformers import SentenceTransformer, util
import sacrebleu
import nltk
from nltk.translate.bleu_score import sentence_bleu

# Load the model and tokenizer
model = SentenceTransformer('all-MiniLM-L6-v2')

# model_name = "sentence-transformers/all-MiniLM-L6-v2"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModel.from_pretrained(model_name)


def calculate_bleu(reference_texts, generated_text):
    nltk.download('punkt')

    reference_tokens = [nltk.word_tokenize(ref) for ref in reference_texts]
    # reference_tokens = nltk.word_tokenize(reference)
    generated_tokens = nltk.word_tokenize(generated_text)

    bleu_score = sentence_bleu(reference_tokens, generated_tokens)
    return bleu_score

def compare_similarity(reference, generated_text):
    """
    Compare similarity using the all miniLM v6 and generate a value for similarity.
    :param reference:
    :param generated_text:
    :return:
    """
    embedding1 = model.encode(reference, convert_to_tensor=True)
    embedding2 = model.encode(generated_text, convert_to_tensor=True)

    # Compute similarity (returns a scalar score)
    similarity = util.pytorch_cos_sim(embedding1, embedding2)
    return similarity.item()


def calculate_rogue_scores(reference, generated_text):
    # rouge = Rouge(metrics=["rouge-1", "rouge-2"])
    rouge = Rouge(metrics=["rouge-L"])
    scores = rouge.get_scores(generated_text, reference)
    scores = scores[0]['rouge-l']
    return scores['r'], scores['p'], scores['f']



def calculate_bert_score(reference, generated_text):
    return bertscore(reference, generated_text, lang="en")


def word2vec_cosine_evaluator(reference, generated_text):
    model = KeyedVectors.load('/Users/swithana/git/ai-model-cards/ingester/word2vec-google-news-300.bin')

    reference_vector = get_word2vec_embedding(model, reference)
    gen_vector = get_word2vec_embedding(model, generated_text)
    cosine_similarity = np.dot(reference_vector, gen_vector) / (np.linalg.norm(reference_vector) * np.linalg.norm(gen_vector))
    return cosine_similarity


def get_word2vec_embedding(model, text):
    embedding = []
    text_embeddings = [model[word] for word in text if word in model]
    if text_embeddings:
        embedding.append(np.mean(text_embeddings, axis=0))
    else:
        embedding.append(np.zeros(300))
    embedding = np.mean(embedding, axis=0)
    return embedding



num_questions = 20 - 1
referece_file = "./evaluation/human_reference.txt"
referece_file_2 = "./evaluation/human_reference-2.txt"
gen_file = "./evaluation/codellama13b-low-temp.txt"


def main():
    references = []
    references2 = []
    generated = []
    with open(referece_file, "r") as file:
        i = 0
        for line in file:
            references.append(line)
            i += 1
            if i > num_questions:
                break
    with open(referece_file_2, "r") as file:
        i = 0
        for line in file:
            references2.append(line)
            i += 1
            if i > num_questions:
                break

    with open(gen_file, "r") as file:
        i = 0
        for line in file:
            generated.append(line)
            i += 1
            if i > num_questions:
                break

    # print(calculate_bert_score([references], [generated]))

    f1_values = []
    recall_values = []
    precision_values = []
    bleu_scores = []

    for j in range(num_questions):
        r, p, f = calculate_rogue_scores(references[j], generated[j])
        r2, p2, f2 = calculate_rogue_scores(references2[j], generated[j])
        bleu_score = calculate_bleu([references[j], references2[j]], generated[j])
        f1_values.append((f+f2)/2)
        recall_values.append((r+r2)/2)
        precision_values.append((p+p2)/2)
        bleu_scores.append(bleu_score)



    # for i in range(1):
    #     # precision, recall, f1 = calculate_bert_score(references, generated)
    #     precision, recall, f1 = calculate_bert_score(["Hello World"], ["Who are you"])
    #     f1_values.append(f1.item())
    #     recall_values.append(recall.item())
    #     precision_values.append(precision.item())

    #
    # for i, f1_score in enumerate(f1):
    #     avg_f1 += f1_score
    #
    # for i, r in enumerate(recall):
    #     avg_recall += r
    #
    # for i, p in enumerate(precision):
    #     avg_precision += p

    # print(f1_values)
    print("ROUGE-L F1: {:.3f}\tRecall: {:.3f}\tPrecision: {:.3f}".format(np.average(f1_values), np.average(recall_values), np.average(precision_values)))
    print("AVG Bleu score: {:.3f}".format(np.average(bleu_scores)))
    print(f1_values)
    print(bleu_scores)

if __name__ == "__main__":
    main()